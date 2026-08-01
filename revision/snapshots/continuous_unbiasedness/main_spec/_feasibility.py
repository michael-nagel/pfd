#!/usr/bin/env python3
"""Datenaufbau und Machbarkeitsmessung für die Hauptspezifikation.

Rein diagnostisch. Zwei Schritte, KEIN Fit der vollen Hauptspezifikation:

  1) Frame nach der Hauptspezifikation bauen und kennzeichnen
     (X = log(Stunden bis Anpfiff), p_ref = erster echt beobachteter
     normalisierter Preis der EIGENEN Bookmaker-Serie)
  2) Speicher- und Laufzeitskalierung von `bam(..., discrete = TRUE)` mit
     Match-Random-Intercept: der Koeffizientenvektor wird vom Match-RE
     dominiert (ein Koeffizient je Matchup), und mgcv behandelt Random
     Effects DICHT -- laut `?random.effects`: "gam can be slow for fitting
     models with large numbers of random effects, because it does not
     exploit the sparsity that is often a feature of parametric random
     effects". Der Aufwand skaliert daher wie p^2 (Speicher) bzw. p^3
     (Cholesky). Gemessen wird auf Teilstichproben mit m Matchups, danach
     wird auf die vollen ~20.760 extrapoliert.

RLIMIT_AS-Backstop, damit ein entgleisender Fit sauber stirbt statt die
WSL-VM mitzunehmen (bei der Verspätungsanalyse hat ein zu großes Modell die
VM neu starten lassen).
"""

import resource
import sys
import threading
import time

import numpy as np
import pandas as pd
import rpy2.robjects as ro
from omegaconf import OmegaConf
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

OUT = "revision/snapshots/continuous_unbiasedness/main_spec"
FRAME = "/tmp/pfd_mainspec_frame.parquet"
LIMIT_GB = 8
MS = [400, 800, 1600, 3200]             # Matchups je Messpunkt
K = 6
COVS = ["TsDur", "Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
        "Compet_WTA"]

resource.setrlimit(resource.RLIMIT_AS, (LIMIT_GB << 30, LIMIT_GB << 30))
pd.set_option("display.width", 220)
ro.r("library(mgcv)")


def peak_gb():
    """Höchststand des Resident Set (Python + eingebettetes R) in GB."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2


class Watch:
    """Peak-RSS-Sampling während eines Fits (VmHWM ist monoton, daher
    reicht der Endwert; gesampelt wird für den Verlauf bei Abbruch)."""

    def __init__(self):
        self.peak, self.stop = 0.0, False

    def __enter__(self):
        self.t0 = time.time()
        self.th = threading.Thread(target=self.run, daemon=True)
        self.th.start()
        return self

    def run(self):
        while not self.stop:
            self.peak = max(self.peak, peak_gb())
            time.sleep(0.25)

    def __exit__(self, *a):
        self.stop = True
        self.th.join(timeout=2)
        self.peak = max(self.peak, peak_gb())
        self.secs = time.time() - self.t0


def build():
    """Frame der Hauptspezifikation."""
    cfg = OmegaConf.create({"estimation": {
        "spec": "BmHome", "normalize": True, "compets": None,
        "bm_quantile": 0.25, "ts_dur": [12, 72], "period": None,
        "resample_freq": "1min", "pctl": 2}})

    raw = pd.read_hdf("data/processed/shaped_data.h5", "df")
    for c in ("Date", "Update"):
        raw[c] = pd.to_datetime(raw[c])
    kick = raw.groupby("Matchup")["Date"].first()
    df, *_ = filter_and_shape_data(raw.copy(), cfg)
    n0 = len(df)

    # Anpfiff je Matchup und Stunden bis Anpfiff
    df["Kick"] = df["Matchup"].map(kick)
    df["HoursToKick"] = (df["Kick"] - df["Update"]).dt.total_seconds() / 3600.0

    # Updates nach Anpfiff raus (log braucht echte Positivität)
    n_after = int((df["HoursToKick"] <= 0).sum())
    df = df[df["HoursToKick"] > 0]

    # Nullvarianz raus, NumOddsMvt < 20
    df = df[df.groupby("GroupId")["OddsMvt"].transform("std") > 0]
    df = df[df["NumOddsMvt"] < 20]

    # p_ref = erster ECHT beobachteter Preis der EIGENEN Serie
    df = df.sort_values(["GroupId", "Update"])
    df["PRef"] = df.groupby("GroupId", sort=False)["OddsMvt"].transform("first")
    df["Endog"] = df["Match"] - df["PRef"]
    df["Exog"] = df["OddsMvt"] - df["PRef"]

    # Referenzbeobachtung raus
    df["ObsIdx"] = df.groupby("GroupId").cumcount()
    df = df[df["ObsIdx"] > 0]

    df["X"] = np.log(df["HoursToKick"])
    keep = ["GroupId", "Matchup", "Bookies", "X", "HoursToKick", "Endog",
            "Exog", "NumOddsMvt"] + COVS
    df = df[keep].reset_index(drop=True)
    df.to_parquet(FRAME)
    print(f"  nach filter_and_shape       {n0:>10,d} Zeilen")
    print(f"  Updates nach Anpfiff raus   {n_after:>10,d}")
    print(f"  Endframe                    {len(df):>10,d} Zeilen", flush=True)
    return df


FML = ("Endog ~ s(X, k = kk, bs = 'cr') + s(X, by = Exog, k = kk, bs = 'cr')"
       " + " + " + ".join(COVS)
       + " + s(Bookies, bs = 're') + s(Exog, Bookies, bs = 're')"
       + " + s(Matchup, bs = 're')")


def fit_sub(d, label):
    """M_d-Struktur auf einer Teilstichprobe; Laufzeit und Peak-RSS."""
    dd = d.copy()
    dd["Bookies"] = dd["Bookies"].astype(str)
    dd["Matchup"] = dd["Matchup"].astype(str)
    with localconverter(ro.default_converter + pandas2ri.converter):
        ro.globalenv["d"] = dd
    ro.globalenv["kk"] = K
    ro.globalenv["fml"] = FML
    with Watch() as w:
        ro.r("""
        d$Bookies <- factor(d$Bookies); d$Matchup <- factor(d$Matchup)
        m <- bam(as.formula(fml), data = d, method = "fREML",
                 discrete = TRUE, nthreads = 2)
        np <- length(coef(m))
        """)
    p = int(ro.globalenv["np"][0])
    print(f"  {label:<22s} n={len(dd):>9,d}  p={p:>7,d}  "
          f"{w.secs:>7.1f} s  Peak {w.peak:>5.2f} GB", flush=True)
    ro.r("rm(m); gc()")
    return {"label": label, "n": len(dd), "p": p, "secs": w.secs,
            "peak_gb": w.peak}


print(f"RLIMIT_AS = {LIMIT_GB} GB\n")
print("1) FRAME DER HAUPTSPEZIFIKATION")
try:
    df = pd.read_parquet(FRAME)
    print(f"  aus Cache: {len(df):,d} Zeilen")
except (FileNotFoundError, OSError):
    df = build()

n_m = df["Matchup"].nunique()
print(f"\n  Serien   {df['GroupId'].nunique():>10,d}")
print(f"  Matchups {n_m:>10,d}")
print(f"  Bookies  {df['Bookies'].nunique():>10,d}")
print(f"  Stunden bis Anpfiff: Median {df['HoursToKick'].median():.2f}"
      f"  min {df['HoursToKick'].min():.4f}  max {df['HoursToKick'].max():.1f}")
print(f"  X = log(h): min {df['X'].min():.2f}  max {df['X'].max():.2f}")
print(f"  Endog sd {df['Endog'].std():.4f}   Exog sd {df['Exog'].std():.4f}")

print(f"\n2) SKALIERUNG (Struktur M_d, nthreads=2, RLIMIT_AS {LIMIT_GB} GB)")
print(f"  {FML}\n")
mus = df["Matchup"].drop_duplicates().to_numpy()
rng = np.random.default_rng(42)
rng.shuffle(mus)

rows = []
for m in MS:
    sub = df[df["Matchup"].isin(mus[:m])]
    try:
        r = fit_sub(sub, f"m={m:,d} Matchups")
        r["m"] = m
        rows.append(r)
    except Exception as e:                              # noqa: BLE001
        print(f"  m={m:,d}: ABBRUCH -- {type(e).__name__}: "
              f"{str(e).strip().splitlines()[-1]}", flush=True)
        break

res = pd.DataFrame(rows)
res.to_csv(f"{OUT}/feasibility_scaling.csv", index=False)

if len(res) >= 3:
    # p = (Koeffizienten ohne Match-RE) + ein Koeffizient je Matchup.
    # Speicher ~ a + b*p^2 (dichte p x p Matrizen), Cholesky ~ p^3.
    p_fix = int(res["p"].iloc[-1] - res["m"].iloc[-1])
    p_full = n_m + p_fix
    A = np.column_stack([np.ones(len(res)), res["p"] ** 2])
    b_mem = np.linalg.lstsq(A, res["peak_gb"], rcond=None)[0]
    b_sec = np.linalg.lstsq(A, res["secs"], rcond=None)[0]
    print(f"\n  Extrapolation auf p = {p_full:,d} (volle {n_m:,d} Matchups):")
    print(f"    Peak-Speicher  ~ {b_mem[0] + b_mem[1] * p_full**2:6.1f} GB")
    print(f"    Laufzeit       ~ {(b_sec[0] + b_sec[1] * p_full**2) / 60:6.1f} "
          f"min   (Cholesky ~p^3, daher eher Untergrenze)")
    print("    verfügbar auf dieser Maschine: ~11,4 GB / 6 Kerne")
else:
    print("\n  zu wenige Messpunkte für eine Extrapolation")

print(f"\ngeschrieben: {OUT}/feasibility_scaling.csv")
