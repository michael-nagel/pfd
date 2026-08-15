#!/usr/bin/env python3
"""Kalibrierungssteigung ueber die Zeit bis Anpfiff (R1-viii, Teil 2).

`_flb_calibration.py` vergleicht nur Opening und Closing. Der Referee fragt,
ob der Bias ueber das Fenster schrumpft -- das ist eine Kurve, keine zwei
Punkte. Hier laeuft dieselbe Kalibrierungsregression auf der kontinuierlichen
Achse, analog zur beta_1-Kurve aus Comment 7:

    Match_it = a(X_it) + lambda(X_it) * p_it + Kovariaten + u_it,
    X = log(Stunden bis Anpfiff)

Basis ist `splines::ns(df = 4)`, dieselbe wie in der Antwort zu Comment 7,
und die Inferenz ist CR1 auf Matchup -- also ohne Random Effects, konsistent
zur Umstellung aus R1-ii. lambda und sein Standardfehler an den Stundenmarken
kommen ueber die Delta-Methode.

Rein diagnostisch.
"""

import sys

import numpy as np
import pandas as pd
import rpy2.robjects as ro
from omegaconf import OmegaConf
from rpy2.robjects import numpy2ri, pandas2ri
from rpy2.robjects.conversion import localconverter
from scipy import stats

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

OUT = "revision/snapshots/flb_calibration"
FRAME = "data/interim/pfd_flb_continuous.parquet"
COVS = ["TsDur", "Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
        "Compet_WTA"]
MARKS = [24.0, 12.0, 6.0, 3.0, 1.0, 0.25]

pd.set_option("display.width", 220)
ro.r("library(splines)")


def build():
    """Wie `_censoring_thresholds.py:build`, aber Preis und Ausgang roh."""
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
    d["X"] = np.log(d["HoursToKick"])
    keep = ["GroupId", "Matchup", "Bookies", "X", "Match", "OddsMvt",
            "IsFav"] + COVS
    d = d[keep].reset_index(drop=True)
    d.to_parquet(FRAME)
    return d


try:
    d = pd.read_parquet(FRAME)
    print(f"Frame aus Cache: {len(d):,d} Zeilen", flush=True)
except (FileNotFoundError, OSError):
    d = build()
    print(f"Frame neu gebaut: {len(d):,d} Zeilen", flush=True)
print(f"  {d['GroupId'].nunique():,d} Serien, "
      f"{d['Matchup'].nunique():,d} Matchups")
print(f"  X von {d['X'].min():.2f} bis {d['X'].max():.2f} "
      f"({np.exp(d['X'].min()):.3f} bis {np.exp(d['X'].max()):.1f} h)")

with localconverter(ro.default_converter + pandas2ri.converter):
    ro.globalenv["d"] = d[["Match", "OddsMvt", "X", "Matchup"] + COVS]
with localconverter(ro.default_converter + numpy2ri.converter):
    ro.globalenv["marks"] = np.log(np.array(MARKS, float))
ro.globalenv["covs"] = ro.StrVector(COVS)

# lambda(X) = Koeffizient auf p plus Interaktion mit der Spline-Basis.
# Der Sandwich laeuft ueber rowsum je Matchup, damit die 1,3 Mio. Zeilen
# nicht nach Python zurueckwandern muessen.
ro.r("""
B  <- ns(d$X, df = 4)
Bm <- predict(B, marks)
p  <- d$OddsMvt
Xd <- cbind(1, B, p, p * B, as.matrix(d[, covs]))
colnames(Xd) <- c("(Intercept)", paste0("ns", 1:4), "p",
                  paste0("p:ns", 1:4), covs)
y   <- d$Match
XtX <- crossprod(Xd)
XtXi <- solve(XtX)
b   <- as.vector(XtXi %*% crossprod(Xd, y))
u   <- as.vector(y - Xd %*% b)
g   <- as.integer(factor(d$Matchup))
S   <- rowsum(Xd * u, g)
G   <- nrow(S); N <- nrow(Xd); K <- ncol(Xd)
cf  <- (G / (G - 1)) * ((N - 1) / (N - K))
V   <- cf * (XtXi %*% crossprod(S) %*% XtXi)
ip  <- which(colnames(Xd) == "p")
iB  <- which(colnames(Xd) %in% paste0("p:ns", 1:4))
lam <- se <- numeric(nrow(Bm))
for (i in seq_len(nrow(Bm))) {
    gvec <- numeric(K); gvec[ip] <- 1; gvec[iB] <- Bm[i, ]
    lam[i] <- sum(gvec * b)
    se[i]  <- sqrt(as.numeric(t(gvec) %*% V %*% gvec))
}
""")

lam = np.asarray(ro.globalenv["lam"], float)
se = np.asarray(ro.globalenv["se"], float)
n_cl = int(ro.globalenv["G"][0])
print(f"\n  N = {int(ro.globalenv['N'][0]):,d}, G = {n_cl:,d} Matchups, "
      f"K = {int(ro.globalenv['K'][0])}")

print("\n  lambda(X): Kalibrierungssteigung an den Stundenmarken")
print(f"  {'Stunden':>8s} {'lambda':>8s} {'SE cl.':>8s} {'t vs 1':>8s} "
      f"{'p':>10s}")
rows = []
for h, l_, s_ in zip(MARKS, lam, se, strict=True):
    t = (l_ - 1) / s_
    p = 2 * (1 - stats.norm.cdf(abs(t)))
    print(f"  {h:>8.2f} {l_:>8.4f} {s_:>8.4f} {t:>8.2f} {p:>10.2e}")
    rows.append({"stunden": h, "lambda": l_, "se_cluster": s_,
                 "t_vs_1": t, "p_vs_1": p})
pd.DataFrame(rows).to_csv(f"{OUT}/continuous_calibration.csv", index=False)

# Dasselbe auf dem Gitter der beta_1-Kurve aus Comment 7, damit sich die
# beiden Abbildungen direkt nebeneinander stellen lassen.
grid = pd.read_csv("revision/snapshots/continuous_unbiasedness/main_spec/"
                   "ns4_final_band.csv")["hours"].to_numpy(float)
with localconverter(ro.default_converter + numpy2ri.converter):
    ro.globalenv["gmarks"] = np.log(grid)
ro.r("""
Bg <- predict(B, gmarks)
lam_g <- se_g <- numeric(nrow(Bg))
for (i in seq_len(nrow(Bg))) {
    gvec <- numeric(K); gvec[ip] <- 1; gvec[iB] <- Bg[i, ]
    lam_g[i] <- sum(gvec * b)
    se_g[i]  <- sqrt(as.numeric(t(gvec) %*% V %*% gvec))
}
""")
lam_g = np.asarray(ro.globalenv["lam_g"], float)
se_g = np.asarray(ro.globalenv["se_g"], float)
pd.DataFrame({"hours": grid, "lambda": lam_g, "se_cluster": se_g,
              "pw_lo": lam_g - 1.96 * se_g,
              "pw_up": lam_g + 1.96 * se_g}).to_csv(
    f"{OUT}/continuous_calibration_grid.csv", index=False)
print(f"\n  Gitter mit {len(grid)} Punkten geschrieben "
      f"({grid.max():.1f} bis {grid.min():.3f} h)")

# Steigt oder faellt die Kurve? Differenz zwischen erster und letzter Marke.
ro.r("""
gv1 <- numeric(K); gv1[ip] <- 1; gv1[iB] <- Bm[1, ]
gv2 <- numeric(K); gv2[ip] <- 1; gv2[iB] <- Bm[nrow(Bm), ]
gd  <- gv2 - gv1
dif <- sum(gd * b); sed <- sqrt(as.numeric(t(gd) %*% V %*% gd))
""")
dif = float(ro.globalenv["dif"][0])
sed = float(ro.globalenv["sed"][0])
print(f"\n  lambda(0.25 h) - lambda(24 h) = {dif:+.4f}   SE {sed:.4f}   "
      f"t = {dif / sed:+.2f}")
pd.DataFrame([{"differenz_letzte_erste_marke": dif, "se": sed,
               "t": dif / sed}]).to_csv(
    f"{OUT}/continuous_calibration_diff.csv", index=False)
print(f"\ngeschrieben nach {OUT}/")
