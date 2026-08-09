#!/usr/bin/env python3
"""Randartefakt und Basiswahl: drei Optionen nebeneinander (R1-vii).

Der Knick am linken Rand der Hauptabbildung ist ein Artefakt der
UNPENALISIERTEN festen Basis, die die lme4-/Sandwich-/Bootstrap-Route
braucht (README Abschnitt 7). Zur Entscheidung stehen drei Wege:

  (a) engerer Trim, 36 h statt 48 h, Basis unveraendert (k = 6, cr)
  (b) sparsamere Basis, k = 4 statt 6, Trim unveraendert
  (c) natural cubic spline (splines::ns) mit linearen Randbedingungen
      statt der cr-Basis

Verglichen werden PUNKTSCHAETZER ueber OLS auf derselben festen Basis-
konstruktion wie in `_cluster_inference.py`; laut dortigem Gate liegt der
Unterschied zu den lme4-Punktschaetzern bei max 0,006, fuer einen
Kurvenvergleich also unerheblich. Baender werden hier NICHT gerechnet -- sie
haengen an den Bootstrap-Replikaten, siehe Hinweis am Ende.

Rein diagnostisch, nichts an der Produktions-Pipeline.
"""

import sys
import tempfile

import numpy as np
import pandas as pd
import rpy2.robjects as ro
from omegaconf import OmegaConf
from rpy2.robjects import numpy2ri, pandas2ri
from rpy2.robjects.conversion import localconverter

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

OUT = "revision/snapshots/continuous_unbiasedness/main_spec"
FRAME = f"{tempfile.gettempdir()}/pfd_mainspec_frame2.parquet"
COVS = ["TsDur", "Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
        "Compet_WTA"]
MARKS = [24.0, 6.0, 1.0]
NGRID = 100

pd.set_option("display.width", 240)
ro.r("library(mgcv); library(splines)")


def build():
    """Wie `_cluster_inference.py:build()`."""
    cfg = OmegaConf.create({"estimation": {
        "spec": "BmHome", "normalize": True, "compets": None,
        "bm_quantile": 0.25, "ts_dur": [12, 72], "period": None,
        "resample_freq": "1min", "pctl": 2}})
    raw = pd.read_hdf("data/processed/shaped_data.h5", "df")
    for c in ("Date", "Update"):
        raw[c] = pd.to_datetime(raw[c])
    kick = raw.groupby("Matchup")["Date"].first()
    d, *_ = filter_and_shape_data(raw.copy(), cfg)
    d["Kick"] = d["Matchup"].map(kick)
    d["HoursToKick"] = (d["Kick"] - d["Update"]).dt.total_seconds() / 3600.0
    d = d[d["HoursToKick"] > 0]
    d = d[d.groupby("GroupId")["OddsMvt"].transform("std") > 0]
    d = d[d["NumOddsMvt"] < 20]
    d = d.sort_values(["GroupId", "Update"])
    d["PRef"] = d.groupby("GroupId", sort=False)["OddsMvt"].transform("first")
    d["Endog"] = d["Match"] - d["PRef"]
    d["Exog"] = d["OddsMvt"] - d["PRef"]
    d["ObsIdx"] = d.groupby("GroupId").cumcount()
    d = d[d["ObsIdx"] > 0]
    d["X"] = np.log(d["HoursToKick"])
    keep = ["GroupId", "Matchup", "Bookies", "X", "HoursToKick", "Endog",
            "Exog", "PRef", "Match", "NumOddsMvt"] + COVS
    d = d[keep].reset_index(drop=True)
    d.to_parquet(FRAME)
    return d


try:
    df = pd.read_parquet(FRAME)
except (FileNotFoundError, OSError):
    df = build()
print(f"{len(df):,d} Zeilen, {df['GroupId'].nunique():,d} Serien")

h_lo, h_hi = df["HoursToKick"].quantile([0.01, 0.99])
HRS = np.exp(np.linspace(np.log(h_hi), np.log(h_lo), NGRID))
print(f"Gitter {HRS.max():.1f} bis {HRS.min():.3f} h\n")

with localconverter(ro.default_converter + pandas2ri.converter):
    ro.globalenv["d0"] = df[["Endog", "Exog", "X"] + COVS]
with localconverter(ro.default_converter + numpy2ri.converter):
    ro.globalenv["hrs"] = HRS


def curve(kind, k):
    """Basis bauen, OLS fitten, beta_1 auf dem Gitter auslesen.

    `kind` ist "cr" (mgcv-Regressionsspline, Constraint absorbiert) oder
    "ns" (natural cubic spline mit linearen Randbedingungen).
    """
    ro.globalenv["kind"] = kind
    ro.globalenv["kk"] = k
    ro.r("""
    if (kind == "cr") {
        sm <- smoothCon(s(X, k = kk, bs = "cr"), data = d0,
                        absorb.cons = TRUE)[[1]]
        B  <- PredictMat(sm, d0)
        Bg <- PredictMat(sm, data.frame(X = log(hrs)))
    } else {
        sm <- ns(d0$X, df = kk)
        B  <- predict(sm, d0$X)
        Bg <- predict(sm, log(hrs))
    }
    nb <- ncol(B)
    d <- d0
    for (j in seq_len(nb)) {
        d[[paste0("b", j)]]  <- B[, j]
        d[[paste0("eb", j)]] <- B[, j] * d0$Exog
    }
    fe <- paste(c(paste0("b", seq_len(nb)), "Exog",
                  paste0("eb", seq_len(nb)), COVS_R), collapse = " + ")
    m <- lm(as.formula(paste("Endog ~", fe)), data = d)
    cf <- coef(m)
    b1 <- as.vector(cf[["Exog"]] + Bg %*% cf[paste0("eb", seq_len(nb))])
    """)
    with localconverter(ro.default_converter + numpy2ri.converter):
        return np.asarray(ro.globalenv["b1"]).ravel(), int(ro.globalenv["nb"][0])


ro.globalenv["COVS_R"] = ro.StrVector(COVS)

OPTIONS = {
    "aktuell: cr k=6": ("cr", 6),
    "(b) cr k=4": ("cr", 4),
    "(c) ns df=4": ("ns", 4),
    "(c) ns df=3": ("ns", 3),
}

curves, nbs = {}, {}
for lab, (kind, k) in OPTIONS.items():
    curves[lab], nbs[lab] = curve(kind, k)
    print(f"  {lab:<18s} Basisspalten {nbs[lab]}")

out = pd.DataFrame(curves, index=HRS).rename_axis("hours").reset_index()
out.to_csv(f"{OUT}/basis_options_curves.csv", index=False)


def at(c, h):
    return float(c[int(np.abs(HRS - h).argmin())])


print("\n" + "=" * 78)
print("KERNWERTE UND RANDVERHALTEN")
print("=" * 78)
rows = []
for lab, c in curves.items():
    left = c[HRS > 36]                       # Zone des Artefakts
    inner = c[(HRS <= 36) & (HRS >= 24)]
    rows.append({
        "Option": lab, "Spalten": nbs[lab],
        "24h": at(c, 24), "6h": at(c, 6), "1h": at(c, 1),
        "min 36-48h": left.min(), "beta1 45.5h": at(c, 45.5),
        "monoton 48->24h": bool(np.all(np.diff(c[HRS >= 24][::-1]) >= -1e-9)),
        "Knick (Delta zu 34h)": at(c, 34) - left.min(),
    })
t = pd.DataFrame(rows)
print(t.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
t.to_csv(f"{OUT}/basis_options_summary.csv", index=False)

base = curves["aktuell: cr k=6"]
print("\nAbweichung von der aktuellen Fassung an den Kernpunkten:")
for lab, c in curves.items():
    if lab == "aktuell: cr k=6":
        continue
    print(f"  {lab:<18s} 24h {at(c, 24) - at(base, 24):+.4f}   "
          f"6h {at(c, 6) - at(base, 6):+.4f}   "
          f"1h {at(c, 1) - at(base, 1):+.4f}")

print("\n" + "=" * 78)
print("(a) TRIM: WAS EIN ENGERES FENSTER KOSTET")
print("=" * 78)
for hmax in (48, 36, 24):
    share = (df["HoursToKick"] <= hmax).mean()
    print(f"  Trim {hmax:>2d} h: {share * 100:5.2f} % der Beobachtungen, "
          f"beta_1(aktuell) am linken Rand = {at(base, hmax):.4f}")

print("\nHINWEIS ZUR BAND-BERECHNUNG")
print("Die 100 gespeicherten Bootstrap-Replikate sind auf k = 6 / cr fixiert")
print("(`_cluster_bootstrap.py:32,61`). Option (a) laesst sie gueltig, weil")
print("nur das Berichtsfenster enger wird. Optionen (b) und (c) aendern die")
print("Basis und verlangen einen neuen Bootstrap-Lauf (2 x 50 Replikate,")
print("zuletzt 145 und 152 min).")
print(f"\nDateien: {OUT}/basis_options_curves.csv, "
      f"{OUT}/basis_options_summary.csv")
