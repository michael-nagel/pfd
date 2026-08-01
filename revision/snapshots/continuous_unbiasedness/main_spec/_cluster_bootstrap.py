#!/usr/bin/env python3
"""Cluster-Bootstrap zur Validierung des CR1-Sandwich (M_c, Cluster = Matchup).

Der CR1-Sandwich korrigiert nur mit einem Skalar G/(G-1) * (N-1)/(N-K) und
"sieht" die starke Unbalanciertheit der Cluster nicht (1 bis 24 Bookmaker je
Matchup, Median 7). Der Bootstrap resampled MATCHUPS mit Zurücklegen und
refittet M_c je Replikat -- eine vom Sandwich unabhängige Bestätigung.

Aufruf:  _cluster_bootstrap.py <part> <n_rep>
`part` (0 oder 1) setzt den Seed-Versatz und den Dateinamen, damit zwei
Prozesse parallel laufen können, ohne multiprocessing/fork mit eingebettetem
R zu mischen (R ist nach der Initialisierung nicht fork-sicher).

Rein diagnostisch.
"""

import sys
import tempfile
import time

import numpy as np
import pandas as pd
import rpy2.robjects as ro
from rpy2.rinterface_lib.embedded import RRuntimeError
from rpy2.robjects import numpy2ri, pandas2ri
from rpy2.robjects.conversion import localconverter

OUT = "revision/snapshots/continuous_unbiasedness/main_spec"
FRAME = f"{tempfile.gettempdir()}/pfd_mainspec_frame2.parquet"
COVS = ["TsDur", "Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
        "Compet_WTA"]
K = 6
NGRID = 100

PART = int(sys.argv[1])
NREP = int(sys.argv[2])

ro.r("library(mgcv); library(lme4)")

df = pd.read_parquet(FRAME)
df["Bookies"] = df["Bookies"].astype(str)
h_lo, h_hi = df["HoursToKick"].quantile([0.01, 0.99])
HRS = np.exp(np.linspace(np.log(h_hi), np.log(h_lo), NGRID))
print(f"part {PART}: {len(df):,d} Zeilen, {df['Matchup'].nunique():,d} "
      f"Matchups, {NREP} Replikate", flush=True)

# Zeilenindizes je Matchup einmal vorberechnen (1-basiert für R)
order = np.argsort(df["Matchup"].to_numpy(), kind="stable")
mu_sorted = df["Matchup"].to_numpy()[order]
bounds = np.flatnonzero(np.r_[True, mu_sorted[1:] != mu_sorted[:-1]])
groups = np.split(order, bounds[1:])
G = len(groups)

# Volle Daten einmal nach R; je Replikat wandert nur der Indexvektor hinüber
with localconverter(ro.default_converter + pandas2ri.converter):
    ro.globalenv["d0"] = df[["Endog", "Exog", "X", "Bookies"] + COVS]
ro.globalenv["kk"] = K
with localconverter(ro.default_converter + numpy2ri.converter):
    ro.globalenv["hrs"] = HRS
ro.r("""
sm <- smoothCon(s(X, k = kk, bs = "cr"), data = d0, absorb.cons = TRUE)[[1]]
B  <- PredictMat(sm, d0); nb <- ncol(B)
Bg <- PredictMat(sm, data.frame(X = log(hrs)))
d  <- d0
for (j in seq_len(nb)) {
    d[[paste0("b", j)]]  <- B[, j]
    d[[paste0("eb", j)]] <- B[, j] * d0$Exog
}
d$Bookies <- factor(d$Bookies)
""")
nb = int(ro.globalenv["nb"][0])

fe = (" + ".join(f"b{j}" for j in range(1, nb + 1)) + " + Exog + "
      + " + ".join(f"eb{j}" for j in range(1, nb + 1)) + " + "
      + " + ".join(COVS))
ro.globalenv["fml"] = f"Endog ~ {fe} + (1 + Exog | Bookies)"
print(f"  {ro.globalenv['fml'][0]}", flush=True)

rows, singular, failed = [], 0, 0
t_start = time.time()
for r in range(NREP):
    rng = np.random.default_rng(42 + PART * 1000 + r)
    draw = rng.integers(0, G, size=G)
    idx = np.concatenate([groups[i] for i in draw]) + 1     # R ist 1-basiert
    with localconverter(ro.default_converter + numpy2ri.converter):
        ro.globalenv["idx"] = idx.astype(np.int32)
    t0 = time.time()
    try:
        ro.r("""
        dr <- d[idx, ]
        mb <- lmer(as.formula(fml), data = dr, REML = FALSE)
        sg <- isSingular(mb)
        fxb <- fixef(mb)
        """)
    except RRuntimeError as e:
        failed += 1
        print(f"  r{r:03d} FEHLER {str(e).strip().splitlines()[-1]}",
              flush=True)
        continue
    with localconverter(ro.default_converter + numpy2ri.converter):
        fx = np.asarray(ro.globalenv["fxb"], float)
        Bg = np.asarray(ro.globalenv["Bg"], float)
    nm = list(ro.r("names(fxb)"))
    C = np.zeros((len(HRS), len(fx)))
    C[:, nm.index("Exog")] = 1.0
    for j in range(nb):
        C[:, nm.index(f"eb{j + 1}")] = Bg[:, j]
    singular += int(bool(ro.globalenv["sg"][0]))
    rows.append(C @ fx)
    el = time.time() - t_start
    print(f"  r{r:03d} {time.time() - t0:5.1f} s   beta1(24h) "
          f"{(C @ fx)[np.argmin(np.abs(HRS - 24))]:.4f}   "
          f"gesamt {el / 60:.1f} min   ETA "
          f"{el / (r + 1) * (NREP - r - 1) / 60:.0f} min", flush=True)

boot = np.array(rows)
np.save(f"{OUT}/bootstrap_beta1_part{PART}.npy", boot)
pd.DataFrame({"hours": HRS, "boot_sd": boot.std(axis=0, ddof=1),
              "boot_mean": boot.mean(axis=0)}).to_csv(
    f"{OUT}/bootstrap_part{PART}.csv", index=False)
print(f"\npart {PART} fertig: {len(rows)} Replikate, {singular} singulär, "
      f"{failed} Fehler, {(time.time() - t_start) / 60:.1f} min")
print(f"geschrieben: {OUT}/bootstrap_beta1_part{PART}.npy")
