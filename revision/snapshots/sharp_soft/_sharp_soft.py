#!/usr/bin/env python3
"""Sharp/Soft-Klassifikation dokumentieren und Robustheit pruefen (R1-iv).

Referee 1, Kommentar 4: die Liste enthaelt Pinnacle und Betfair, die
ueblicherweise als sharp bzw. als Exchange gelten, obwohl das Paper den
Soft-Markt untersucht. Gefordert ist, die Klassifikation zu dokumentieren
ODER die Robustheit gegen den Ausschluss sharper Haeuser zu zeigen.

Teil 1 liefert den datengetriebenen Klassifikationsproxy: die Median-Marge
je Bookmaker. Teil 2 rechnet die beiden Kernbefunde ohne die margenaermsten
Haeuser nach -- die GMM-Lernrate (je Bookmaker geschaetzt, der Ausschluss
betrifft also nur die Aggregation) und die kontinuierliche beta_1-Kurve
(muss neu geschaetzt werden).

Betfair wird NICHT ausgeschlossen: in diesen Daten ist es das Sportsbook,
nicht die Exchange, was die Marge bestaetigt.

Rein diagnostisch.
"""

import sys

import numpy as np
import pandas as pd
import rpy2.robjects as ro
from omegaconf import OmegaConf
from rpy2.robjects import numpy2ri, pandas2ri
from rpy2.robjects.conversion import localconverter

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

OUT = "revision/snapshots/sharp_soft"
GMM = "revision/snapshots/E_gmm_exponent_fix/gmm_by_bookie.csv"
FRAME = "data/interim/pfd_sharp_frame.parquet"
COVS = ["TsDur", "Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
        "Compet_WTA"]
MARKS = [24.0, 12.0, 6.0, 3.0, 1.0, 0.25]

pd.set_option("display.width", 220)
ro.r("library(splines)")


def block(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78, flush=True)


def build():
    """Frame fuer die Unbiasedness-Kurve, wie _censoring_thresholds.build."""
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
    keep = ["GroupId", "Matchup", "Bookies", "X", "Endog", "Exog"] + COVS
    d = d[keep].reset_index(drop=True)
    d.to_parquet(FRAME)
    return d


# --------------------------------------------- 1) Marge je Bookmaker
block("1) MEDIAN-MARGE JE BOOKMAKER (Klassifikationsproxy)")
cfg = OmegaConf.create({"estimation": {
    "spec": "BmHome", "normalize": True, "compets": None,
    "bm_quantile": 0.25, "ts_dur": [12, 72], "period": None,
    "resample_freq": "1min", "pctl": 2}})
raw = pd.read_hdf("data/processed/shaped_data.h5", "df")
for c in ("Date", "Update"):
    raw[c] = pd.to_datetime(raw[c])
raw["Margin"] = 1 / raw["OddsMvtHome"] + 1 / raw["OddsMvtAway"] - 1
d_full, *_ = filter_and_shape_data(raw.copy(), cfg)
# Marge haengt am Zeitpunkt, nicht an der gewaehlten Seite; sie wird auf
# demselben gefilterten Bestand gemessen, auf dem auch geschaetzt wird.
key = ["Matchup", "Bookies", "Update"]
m = d_full.merge(raw[key + ["Margin"]], on=key, how="left")
opn = m.groupby("GroupId").first()

tab = pd.DataFrame({
    "marge_median": m.groupby("Bookies")["Margin"].median(),
    "marge_median_opening": opn.groupby("Bookies")["Margin"].median(),
    "serien": m.groupby("Bookies")["GroupId"].nunique(),
}).sort_values("marge_median")
tab["anteil"] = tab["serien"] / tab["serien"].sum()
tab.to_csv(f"{OUT}/margin_by_bookie.csv")
print(f"  {'Bookmaker':<14s} {'Marge':>8s} {'Opening':>8s} {'Serien':>8s} "
      f"{'Anteil':>7s}")
for b, r in tab.iterrows():
    print(f"  {b:<14s} {r['marge_median'] * 100:>7.2f}% "
          f"{r['marge_median_opening'] * 100:>7.2f}% {int(r['serien']):>8,d} "
          f"{r['anteil'] * 100:>6.2f}%")
print(f"\n  Spanne: {tab['marge_median'].min() * 100:.2f}% "
      f"({tab.index[0]}) bis {tab['marge_median'].max() * 100:.2f}% "
      f"({tab.index[-1]})")
print(f"  Betfair: {tab.loc['Betfair', 'marge_median'] * 100:.2f}%, "
      f"Rang {list(tab.index).index('Betfair') + 1} von {len(tab)} "
      f"(1 = niedrigste Marge)")

low2 = list(tab.index[:2])
low4 = list(tab.index[:4])
print(f"\n  Zwei margenaermste:  {low2}")
print(f"  Vier margenaermste:  {low4}")

# ------------------------------------------ 2) GMM ohne die sharpen Haeuser
block("2) GMM-LERNRATE OHNE DIE MARGENAERMSTEN HAEUSER")
print("  gamma wird je Bookmaker geschaetzt; der Ausschluss betrifft nur\n"
      "  die Aggregation, es muss nichts neu geschaetzt werden.\n")
g = pd.read_csv(GMM).set_index("bookie")
rows = []
for lab, drop in (("volles Sample", []), ("ohne 2 margenaermste", low2),
                  ("ohne 4 margenaermste", low4)):
    s = g.drop(index=drop)
    rows.append({"variante": lab, "ausgeschlossen": ", ".join(drop) or "--",
                 "n_bookies": len(s), "gamma_mittel": s["gamma"].mean(),
                 "gamma_min": s["gamma"].min(), "gamma_max": s["gamma"].max(),
                 "argmin": s["gamma"].idxmin(), "argmax": s["gamma"].idxmax()})
    print(f"  {lab:<22s} n = {len(s):>2d}   gamma {s['gamma'].mean():.5f}   "
          f"Spanne {s['gamma'].min():.5f}-{s['gamma'].max():.5f}   "
          f"min {s['gamma'].idxmin()}, max {s['gamma'].idxmax()}")
pd.DataFrame(rows).to_csv(f"{OUT}/gmm_without_sharp.csv", index=False)

# ------------------------------- 3) beta_1-Kurve ohne die sharpen Haeuser
block("3) KONTINUIERLICHE beta_1-KURVE OHNE DIE MARGENAERMSTEN HAEUSER")
try:
    d = pd.read_parquet(FRAME)
    print(f"  Frame aus Cache: {len(d):,d} Zeilen", flush=True)
except (FileNotFoundError, OSError):
    d = build()
    print(f"  Frame neu gebaut: {len(d):,d} Zeilen", flush=True)


def curve(sub, lab):
    """ns(df=4)-Kurve mit CR1 auf Matchup, wie in der R1-vii-Antwort."""
    with localconverter(ro.default_converter + pandas2ri.converter):
        ro.globalenv["d"] = sub[["Endog", "Exog", "X", "Matchup"] + COVS]
    with localconverter(ro.default_converter + numpy2ri.converter):
        ro.globalenv["marks"] = np.log(np.array(MARKS, float))
    ro.globalenv["covs"] = ro.StrVector(COVS)
    ro.r("""
    B  <- ns(d$X, df = 4)
    Bm <- predict(B, marks)
    e  <- d$Exog
    Xd <- cbind(1, B, e, e * B, as.matrix(d[, covs]))
    y  <- d$Endog
    XtXi <- solve(crossprod(Xd))
    b  <- as.vector(XtXi %*% crossprod(Xd, y))
    u  <- as.vector(y - Xd %*% b)
    gg <- as.integer(factor(d$Matchup))
    S  <- rowsum(Xd * u, gg)
    G  <- nrow(S); N <- nrow(Xd); K <- ncol(Xd)
    V  <- (G/(G-1)) * ((N-1)/(N-K)) * (XtXi %*% crossprod(S) %*% XtXi)
    ip <- 6; iB <- 7:10
    lam <- se <- numeric(nrow(Bm))
    for (i in seq_len(nrow(Bm))) {
        gv <- numeric(K); gv[ip] <- 1; gv[iB] <- Bm[i, ]
        lam[i] <- sum(gv * b)
        se[i]  <- sqrt(as.numeric(t(gv) %*% V %*% gv))
    }
    """)
    # np.asarray liefert bei einem rpy2-FloatVector eine VIEW in den
    # R-Speicher. Der naechste Aufruf bindet `lam`/`se` in R neu, womit die
    # View ins Leere zeigt -- deshalb hier kopieren, nicht referenzieren.
    lam = np.array(ro.globalenv["lam"], dtype=float)
    se = np.array(ro.globalenv["se"], dtype=float)
    print(f"  {lab:<22s} {len(sub):>9,d} Zeilen, "
          f"{sub['GroupId'].nunique():>7,d} Serien, "
          f"{int(ro.globalenv['G'][0]):>6,d} Matchups", flush=True)
    return lam, se


res = {}
for lab, drop in (("voll", []), ("ohne2", low2), ("ohne4", low4)):
    sub = d[~d["Bookies"].isin(drop)]
    res[lab] = curve(sub, lab)

print(f"\n  {'Stunden':>8s} {'voll':>8s} {'ohne 2':>8s} {'Diff':>8s} "
      f"{'ohne 4':>8s} {'Diff':>8s} {'SE voll':>8s}")
out = []
for i, h in enumerate(MARKS):
    lv, sv = res["voll"][0][i], res["voll"][1][i]
    l2 = res["ohne2"][0][i]
    l4 = res["ohne4"][0][i]
    print(f"  {h:>8.2f} {lv:>8.4f} {l2:>8.4f} {l2 - lv:>+8.4f} "
          f"{l4:>8.4f} {l4 - lv:>+8.4f} {sv:>8.4f}")
    out.append({"stunden": h, "beta1_voll": lv, "se_voll": sv,
                "beta1_ohne2": l2, "diff_ohne2": l2 - lv,
                "beta1_ohne4": l4, "diff_ohne4": l4 - lv,
                "diff_ohne2_in_se": (l2 - lv) / sv,
                "diff_ohne4_in_se": (l4 - lv) / sv})
o = pd.DataFrame(out)
o.to_csv(f"{OUT}/beta1_without_sharp.csv", index=False)
print(f"\n  groesste Abweichung ohne 2: {o['diff_ohne2'].abs().max():.4f} "
      f"({o['diff_ohne2_in_se'].abs().max():.2f} SE)")
print(f"  groesste Abweichung ohne 4: {o['diff_ohne4'].abs().max():.4f} "
      f"({o['diff_ohne4_in_se'].abs().max():.2f} SE)")
print(f"\ngeschrieben nach {OUT}/")
