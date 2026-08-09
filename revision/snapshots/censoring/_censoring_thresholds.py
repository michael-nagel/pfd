#!/usr/bin/env python3
"""Haelt beta_1 bei ALTERNATIVEN Filterschwellen? (R1-v, Teil 3b)

`_censoring_beta1.py` vergleicht nur zwei Faelle: Produktionsfilter
(NumOddsMvt < 20) gegen alle Serien. Der Referee fragt allgemeiner, ob die
Schlussfolgerungen an der Selektion haengen. Hier wird dieselbe
Spezifikation (M_c) ueber eine Reihe von Schwellen geschaetzt.

Der Frame wird EINMAL ohne Filter gebaut und danach nur noch geteilt, damit
die Schwellen sich ausschliesslich in der Zeilenmenge unterscheiden.

Rein diagnostisch, nichts an der Produktions-Pipeline.
"""

import sys
import time

import numpy as np
import pandas as pd
import rpy2.robjects as ro
from omegaconf import OmegaConf
from rpy2.robjects import numpy2ri, pandas2ri
from rpy2.robjects.conversion import localconverter

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

OUT = "revision/snapshots/censoring"
COVS = ["TsDur", "Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
        "Compet_WTA"]
MARKS = [24.0, 12.0, 6.0, 3.0, 1.0, 0.25]
THRESHOLDS = [10, 15, 18, 20, 21]      # 20 = Produktion, 21 = alle Serien
K = 6

pd.set_option("display.width", 220)
ro.r("library(mgcv)")

FML = ("Endog ~ s(X, k = kk, bs = 'cr') + s(X, by = Exog, k = kk, bs = 'cr')"
       " + " + " + ".join(COVS)
       + " + s(Bookies, bs = 're') + s(Exog, Bookies, bs = 're')")


def build():
    """Frame OHNE Schwellenfilter; NumOddsMvt bleibt zum Teilen erhalten."""
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

    d = d.sort_values(["GroupId", "Update"])
    d["PRef"] = d.groupby("GroupId", sort=False)["OddsMvt"].transform("first")
    d["Endog"] = d["Match"] - d["PRef"]
    d["Exog"] = d["OddsMvt"] - d["PRef"]
    d["ObsIdx"] = d.groupby("GroupId").cumcount()
    d = d[d["ObsIdx"] > 0]
    d["X"] = np.log(d["HoursToKick"])
    keep = ["GroupId", "Matchup", "Bookies", "X", "Endog", "Exog",
            "NumOddsMvt"] + COVS
    return d[keep].reset_index(drop=True)


def fit(d, label):
    """M_c schaetzen und beta_1 an den Stundenmarken auslesen."""
    d = d.copy()
    d["Bookies"] = d["Bookies"].astype(str)
    num = ["Endog", "Exog", "X"] + COVS
    d = d[np.isfinite(d[num]).all(axis=1)]
    n_ser = d["GroupId"].nunique()
    with localconverter(ro.default_converter + pandas2ri.converter):
        ro.globalenv["d"] = d[["Endog", "Exog", "X", "Bookies"] + COVS]
    with localconverter(ro.default_converter + numpy2ri.converter):
        ro.globalenv["marks"] = np.log(np.array(MARKS, float))
    ro.globalenv["kk"] = K
    ro.globalenv["fml"] = FML
    t0 = time.time()
    ro.r("""
    d$Bookies <- factor(d$Bookies)
    m <- bam(as.formula(fml), data = d, method = "fREML", discrete = TRUE)
    nd <- data.frame(X = marks, TsDur = 0, Compet_Challenger_Men = 0,
                     Compet_ITF_Men = 0, Compet_Misc = 0, Compet_WTA = 0,
                     Bookies = factor(levels(d$Bookies)[1],
                                      levels = levels(d$Bookies)))
    Xp <- predict(m, transform(nd, Exog = 1), type = "lpmatrix") -
          predict(m, transform(nd, Exog = 0), type = "lpmatrix")
    out <- data.frame(beta_1 = as.vector(Xp %*% coef(m)),
                      se = sqrt(pmax(0, rowSums((Xp %*% vcov(m)) * Xp))))
    """)
    secs = time.time() - t0
    with localconverter(ro.default_converter + pandas2ri.converter):
        o = ro.conversion.get_conversion().rpy2py(ro.globalenv["out"])
    o.insert(0, "hours", MARKS)
    o.insert(0, "threshold", label)
    o["n_obs"] = len(d)
    o["n_series"] = n_ser
    print(f"  Schwelle {label:<12s} {secs:5.1f} s   {len(d):>9,d} Zeilen, "
          f"{n_ser:>7,d} Serien", flush=True)
    return o


print("Frame bauen ...", flush=True)
full = build()
print(f"  {len(full):,d} Zeilen, {full['GroupId'].nunique():,d} Serien\n")

print("Schaetzen ...", flush=True)
res = pd.concat(
    [fit(full[full["NumOddsMvt"] < t], f"< {t}") for t in THRESHOLDS],
    ignore_index=True)
res.to_csv(f"{OUT}/beta1_thresholds_long.csv", index=False)

piv = res.pivot(index="hours", columns="threshold",
                values="beta_1").sort_index(ascending=False)
piv = piv[[f"< {t}" for t in THRESHOLDS]]
piv.to_csv(f"{OUT}/beta1_thresholds.csv")

print("\nbeta_1 je Schwelle:")
print(piv.to_string(float_format=lambda v: f"{v:.4f}"))

prod = piv["< 20"]
print("\nAbweichung von der Produktionsschwelle (< 20):")
dev = piv.sub(prod, axis=0).drop(columns="< 20")
print(dev.to_string(float_format=lambda v: f"{v:+.4f}"))
print(f"\ngroesste absolute Abweichung: {dev.abs().to_numpy().max():.4f}")

n = res.groupby("threshold")["n_series"].first().reindex(
    [f"< {t}" for t in THRESHOLDS])
print("\nSerien je Schwelle:")
print(n.to_string())
print(f"\nDateien: {OUT}/beta1_thresholds.csv, "
      f"{OUT}/beta1_thresholds_long.csv")
