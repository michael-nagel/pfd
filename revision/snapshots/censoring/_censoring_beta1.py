#!/usr/bin/env python3
"""Robustheit gegen den `NumOddsMvt < 20`-Filter (R1-v, Teil 3).

Referee 1 (Kommentar 5) verlangt zu zeigen, dass die Schlussfolgerungen nicht
an dieser Selektion haengen. Dazu wird die Hauptspezifikation der
kontinuierlichen Unbiasedness-Regression (M_c aus
`continuous_unbiasedness/main_spec/_ladder.py`) zweimal geschaetzt:

  produktion   NumOddsMvt < 20, wie im Paper
  vollstaendig alle Serien, auch die mit zensierter Pfadmitte

Alles andere ist identisch: Endog = Match - p_ref, Exog = p(t) - p_ref,
p_ref = erster echt beobachteter Preis der eigenen Serie, X = log(Stunden bis
Anpfiff), Kovariaten TsDur + Competition, k = 6, bs = "cr", fREML.

Rein diagnostisch, kein Eingriff in die Produktions-Pipeline.
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
K = 6

pd.set_option("display.width", 220)
ro.r("library(mgcv)")


def build(cap):
    """Frame der Hauptspezifikation; `cap=True` setzt den <20-Filter."""
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
    if cap:
        d = d[d["NumOddsMvt"] < 20]

    d = d.sort_values(["GroupId", "Update"])
    d["PRef"] = d.groupby("GroupId", sort=False)["OddsMvt"].transform("first")
    d["Endog"] = d["Match"] - d["PRef"]
    d["Exog"] = d["OddsMvt"] - d["PRef"]
    d["ObsIdx"] = d.groupby("GroupId").cumcount()
    d = d[d["ObsIdx"] > 0]
    d["X"] = np.log(d["HoursToKick"])
    keep = (["GroupId", "Matchup", "Bookies", "X", "Endog", "Exog"] + COVS)
    return d[keep].reset_index(drop=True)


FML = ("Endog ~ s(X, k = kk, bs = 'cr') + s(X, by = Exog, k = kk, bs = 'cr')"
       " + " + " + ".join(COVS)
       + " + s(Bookies, bs = 're') + s(Exog, Bookies, bs = 're')")


def fit(d, label):
    """M_c schaetzen und beta_1 an den festen Stundenmarken auslesen."""
    d = d.copy()
    d["Bookies"] = d["Bookies"].astype(str)
    num = ["Endog", "Exog", "X"] + COVS
    d = d[np.isfinite(d[num]).all(axis=1)]
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
    o.insert(0, "sample", label)
    o["n_obs"] = len(d)
    o["n_series"] = d["GroupId"].nunique() if "GroupId" in d else np.nan
    print(f"  {label:<14s} {secs:5.1f} s   {len(d):>9,d} Zeilen", flush=True)
    return o


print("Frames bauen ...", flush=True)
d_cap = build(cap=True)
d_all = build(cap=False)
print(f"  produktion   {len(d_cap):>9,d} Zeilen, "
      f"{d_cap['GroupId'].nunique():>7,d} Serien")
print(f"  vollstaendig {len(d_all):>9,d} Zeilen, "
      f"{d_all['GroupId'].nunique():>7,d} Serien   "
      f"(+{d_all['GroupId'].nunique() - d_cap['GroupId'].nunique():,d} Serien, "
      f"+{len(d_all) - len(d_cap):,d} Zeilen)")

print("\nSchaetzen ...", flush=True)
res = pd.concat([fit(d_cap, "produktion"), fit(d_all, "vollstaendig")],
                ignore_index=True)

piv = res.pivot(index="hours", columns="sample",
                values=["beta_1", "se"]).sort_index(ascending=False)
piv.columns = [f"{a}_{b}" for a, b in piv.columns]
piv["diff"] = piv["beta_1_vollstaendig"] - piv["beta_1_produktion"]
# Differenz gemessen in Standardfehlern der Produktionsfassung
piv["diff_in_se"] = piv["diff"] / piv["se_produktion"]

print("\n" + "=" * 78)
print("BETA_1 MIT UND OHNE DEN <20-FILTER")
print("=" * 78)
print(piv.round(4).to_string())
res.to_csv(f"{OUT}/beta1_filter_marks_long.csv", index=False)
piv.reset_index().to_csv(f"{OUT}/beta1_filter_marks.csv", index=False)

print(f"\n  groesste Abweichung {piv['diff'].abs().max():.4f} "
      f"({piv['diff_in_se'].abs().max():.2f} Standardfehler)")
print(f"\ngeschrieben: {OUT}/beta1_filter_marks.csv, "
      f"beta1_filter_marks_long.csv")
