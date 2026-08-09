#!/usr/bin/env python3
"""Cluster-Bootstrap fuer die ns(df=4)-Basis (M_c, Cluster = Matchup).

Identisch zu `_cluster_bootstrap.py`, nur mit natural cubic spline
(lineare Randbedingungen) statt der cr-Basis. Noetig, weil die
gespeicherten Replikate auf k = 6 / cr fixiert sind und eine
Basisaenderung sie entwertet.

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
import time

import numpy as np
import pandas as pd
import rpy2.robjects as ro
from rpy2.rinterface_lib.embedded import RRuntimeError
from rpy2.robjects import numpy2ri, pandas2ri
from rpy2.robjects.conversion import localconverter

OUT = "revision/snapshots/continuous_unbiasedness/main_spec"
# NICHT nach /tmp: WSL leert das bei jedem VM-Neustart, und der Lauf hat dann
# sein ganzes Zeitfenster mit dem Neubau des Frames verbracht statt mit
# Replikaten. `data/interim/` liegt auf dem Windows-Dateisystem, ueberlebt den
# Neustart und ist gitignoriert.
FRAME = "data/interim/pfd_mainspec_frame2.parquet"
COVS = ["TsDur", "Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
        "Compet_WTA"]
DF = 4
NGRID = 100

PART = int(sys.argv[1])
NREP = int(sys.argv[2])

ro.r("library(mgcv); library(lme4); library(splines)")

def build():
    """Frame neu bauen, wenn der /tmp-Cache fehlt.

    WSL leert /tmp beim Neustart der VM; ein Lauf, der sich nur auf den
    Cache verlaesst, stirbt dann beim Start. Identisch zu
    `_cluster_inference.py:build()`.
    """
    import sys

    from omegaconf import OmegaConf

    sys.path.insert(0, "src")
    from pfd.models.filter_and_shape import filter_and_shape_data

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
    print("Frame-Cache fehlt, wird neu gebaut ...", flush=True)
    df = build()
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
ro.globalenv["kk"] = DF
with localconverter(ro.default_converter + numpy2ri.converter):
    ro.globalenv["hrs"] = HRS
ro.r("""
sm <- ns(d0$X, df = kk)
B  <- predict(sm, d0$X); nb <- ncol(B)
Bg <- predict(sm, log(hrs))
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

NPY = f"{OUT}/ns4_bootstrap_beta1_part{PART}.npy"

# Zwischenspeichern nach JEDEM Replikat, und beim Start fortsetzen statt neu
# beginnen. Ein erster Lauf wurde nach ~50 min abgebrochen und hatte nichts
# geschrieben, weil np.save erst hinter der Schleife stand.
rows, singular, failed = [], 0, 0
try:
    rows = [r for r in np.load(NPY)]
    print(f"  fortgesetzt: {len(rows)} Replikate bereits vorhanden",
          flush=True)
except FileNotFoundError:
    pass

t_start = time.time()
for r in range(len(rows), NREP):
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
    np.save(NPY, np.array(rows))
    el = time.time() - t_start
    print(f"  r{r:03d} {time.time() - t0:5.1f} s   beta1(24h) "
          f"{(C @ fx)[np.argmin(np.abs(HRS - 24))]:.4f}   "
          f"gesamt {el / 60:.1f} min   ETA "
          f"{el / (r + 1) * (NREP - r - 1) / 60:.0f} min", flush=True)

boot = np.array(rows)
np.save(NPY, boot)
pd.DataFrame({"hours": HRS, "boot_sd": boot.std(axis=0, ddof=1),
              "boot_mean": boot.mean(axis=0)}).to_csv(
    f"{OUT}/ns4_bootstrap_part{PART}.csv", index=False)
print(f"\npart {PART} fertig: {len(rows)} Replikate, {singular} singulär, "
      f"{failed} Fehler, {(time.time() - t_start) / 60:.1f} min")
print(f"geschrieben: {OUT}/ns4_bootstrap_beta1_part{PART}.npy")
