#!/usr/bin/env python3
"""Randdiagnostik der x-Achse: Datendichte und Stabilität des linken Rands.

Das Auswertungsgitter der Hauptspezifikation ist auf das 1.–99. Perzentil von
`HoursToKick` beschnitten (`_ladder.py:114`, `_cluster_inference.py:165`,
`_lme4_main.py:138`), also 59,90 h bis 0,067 h; beobachtet sind 0,017 h bis
181,2 h. Das Modell selbst ist auf ALLEN Beobachtungen geschätzt -- der Trim
betrifft nur Auswertung und Darstellung.

  1) Beobachtungen und Serien je Stunden-Bin, kumuliert von links
  2) beta_1 über den VOLLEN beobachteten Bereich für k = 6, 10, 20 (M_c),
     um zu zeigen, ob der Knick am linken Rand basisgetrieben ist
  3) CSV + Abbildung mit vollem Bereich und markierter Trim-Grenze

Rein diagnostisch.
"""

import sys
import tempfile

import numpy as np
import pandas as pd
import rpy2.robjects as ro
from rpy2.robjects import numpy2ri, pandas2ri
from rpy2.robjects.conversion import localconverter

sys.path.insert(0, "src")

OUT = "revision/snapshots/continuous_unbiasedness/main_spec"
FRAME = f"{tempfile.gettempdir()}/pfd_mainspec_frame2.parquet"
COVS = ["TsDur", "Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
        "Compet_WTA"]
EDGES = [np.inf, 72, 48, 24, 12, 6, 3, 1, 0]
NGRID = 200

pd.set_option("display.width", 220)
ro.r("library(mgcv)")

df = pd.read_parquet(FRAME)
df["Bookies"] = df["Bookies"].astype(str)
h = df["HoursToKick"]
print(f"Frame: {len(df):,d} Zeilen, {df['GroupId'].nunique():,d} Serien")
print(f"HoursToKick: min {h.min():.4f}  1. Pctl {h.quantile(.01):.4f}  "
      f"Median {h.median():.2f}  99. Pctl {h.quantile(.99):.2f}  "
      f"max {h.max():.1f}\n")

# ---------------------------------------------------- 1) Verteilung je Bin
rows = []
for hi, lo in zip(EDGES[:-1], EDGES[1:], strict=True):
    m = (h > lo) & (h <= hi)
    lab = (f"> {lo:g} h" if np.isinf(hi) else
           (f"< {hi:g} h" if lo == 0 else f"{lo:g}-{hi:g} h"))
    rows.append({"Bin": lab, "n_obs": int(m.sum()),
                 "n_Serien": df.loc[m, "GroupId"].nunique(),
                 "Anteil_obs": m.mean()})
bins = pd.DataFrame(rows)
bins["kum_von_links"] = bins["Anteil_obs"].cumsum()
print("1) VERTEILUNG ÜBER DIE STUNDEN-ACHSE (links = fern vom Anpfiff)")
print(bins.to_string(index=False, float_format=lambda v: f"{v:,.5f}"))
bins.to_csv(f"{OUT}/edge_distribution.csv", index=False)

for t in (59.90, 48, 40, 30, 24):
    m = h > t
    print(f"  > {t:>6.2f} h: {int(m.sum()):>8,d} Beob. "
          f"({m.mean() * 100:5.2f} %), "
          f"{df.loc[m, 'GroupId'].nunique():>6,d} Serien")

# ------------------------------- 2) beta_1 über den vollen Bereich, k-Serie
print("\n2) beta_1 ÜBER DEN VOLLEN BEOBACHTETEN BEREICH (M_c, mgcv)")
HRS = np.exp(np.linspace(np.log(h.max()), np.log(h.min()), NGRID))
FML = ("Endog ~ s(X, k = kk, bs = 'cr') + s(X, by = Exog, k = kk, bs = 'cr')"
       " + " + " + ".join(COVS)
       + " + s(Bookies, bs = 're') + s(Exog, Bookies, bs = 're')")

cols = ["Endog", "Exog", "X", "Bookies"] + COVS
with localconverter(ro.default_converter + pandas2ri.converter):
    ro.globalenv["d"] = df[cols]
with localconverter(ro.default_converter + numpy2ri.converter):
    ro.globalenv["hrs"] = HRS
ro.globalenv["fml"] = FML
ro.r('d$Bookies <- factor(d$Bookies)')

curves = []
for k in (6, 10, 20):
    ro.globalenv["kk"] = k
    ro.r("""
    m <- bam(as.formula(fml), data = d, method = "fREML", discrete = TRUE,
             nthreads = 4)
    g <- data.frame(X = log(hrs), Bookies = levels(d$Bookies)[1])
    for (cv in c("TsDur", "Compet_Challenger_Men", "Compet_ITF_Men",
                 "Compet_Misc", "Compet_WTA")) g[[cv]] <- 0
    Xp <- predict(m, transform(g, Exog = 1), type = "lpmatrix") -
          predict(m, transform(g, Exog = 0), type = "lpmatrix")
    rec <- unlist(lapply(m$smooth, function(s)
        if (inherits(s, "random.effect")) s$first.para:s$last.para else NULL))
    if (!is.null(rec)) Xp[, rec] <- 0
    out <- data.frame(hours = hrs, beta_1 = as.vector(Xp %*% coef(m)),
                      se = sqrt(pmax(0, rowSums((Xp %*% vcov(m)) * Xp))))
    """)
    with localconverter(ro.default_converter + pandas2ri.converter):
        o = ro.conversion.get_conversion().rpy2py(ro.globalenv["out"])
    curves.append(o.assign(k=k))
    print(f"  k={k:<3d} fertig", flush=True)

cur = pd.concat(curves, ignore_index=True)
cur.to_csv(f"{OUT}/edge_beta1_fullrange.csv", index=False)

print("\n  beta_1 an ausgewählten Stunden, je k:")
piv = []
for t in (181, 120, 90, 72, 60, 48, 36, 24, 12, 6, 1, 0.1, 0.02):
    r = {"Stunden": t}
    for k in (6, 10, 20):
        c = cur[cur["k"] == k]
        i = int(np.argmin(np.abs(c["hours"].to_numpy() - t)))
        r[f"k={k}"] = c["beta_1"].iloc[i]
        if k == 6:
            r["SE(k=6)"] = c["se"].iloc[i]
    r["n_obs_>=Stunde"] = int((h >= t).sum())
    piv.append(r)
pv = pd.DataFrame(piv)
print(pv.to_string(index=False, float_format=lambda v: f"{v:,.3f}"))
pv.to_csv(f"{OUT}/edge_beta1_by_k.csv", index=False)

# Spannweite über k als Stabilitätsmaß, getrennt innerhalb/außerhalb Trim
w = cur.pivot_table(index="hours", columns="k", values="beta_1")
w["spread"] = w.max(axis=1) - w.min(axis=1)
lo99, hi99 = h.quantile(.01), h.quantile(.99)
inside = w[(w.index >= lo99) & (w.index <= hi99)]
outside = w[w.index > hi99]
print("\n  Spannweite beta_1 über k = 6/10/20:")
print(f"    innerhalb des Trims (0,067-59,9 h): Median "
      f"{inside['spread'].median():.3f}, max {inside['spread'].max():.3f}")
print(f"    links ausserhalb (> 59,9 h):        Median "
      f"{outside['spread'].median():.3f}, max {outside['spread'].max():.3f}")

print(f"\ngeschrieben: {OUT}/edge_distribution.csv, "
      f"edge_beta1_fullrange.csv, edge_beta1_by_k.csv")
