#!/usr/bin/env python3
"""Ökonomische Grössenordnung des RMSE-Rückgangs über das Wettfenster (R1-vii).

R1-vii, erster Teil: "the economic magnitude of the RMSE decline appears
modest". Der Einwand ist berechtigt, aber die Zahl steht im Paper ohne
Bezugspunkt. Hier wird sie eingeordnet und zusätzlich gegen die Imputation
abgesichert -- denn der beta_1-Pfad war laut `../README.md` (Nachtrag 2)
weitgehend ein Imputationsartefakt, und für die RMSE-Kurve war das noch nicht
geprüft.

Vier Teile:

  1) Was die RMSE-Kurve in Figur 3 überhaupt misst (Residual-RMSE der
     Unbiasedness-Regression) und wie gross ihr Rückgang ist.
  2) Dieselbe Grösse als Brier-Score und Brier Skill Score. Bei binärem
     Ausgang ist der RMSE-Wertebereich eng -- der Münzwurf liegt bei 0,5 --,
     der Skill Score ist die interpretierbare Fassung.
  3) Der direkte, unregressierte Vergleich auf ECHTEN Beobachtungen: RMSE
     des Preises p(t) selbst als Prognose, je Stundenbin. Dazu die
     kompositionsfreie Fassung -- je Serie erste gegen letzte echte
     Beobachtung, gepaart, matchup-cluster-robust getestet.
  4) Der ökonomische Massstab: wie viel der Prognosegüte steckt schon im
     Opening, und wie viel steuert das Fenster bei.

Rein diagnostisch, nichts an der Produktions-Pipeline.
"""

import sys
import tempfile

import numpy as np
import pandas as pd
from omegaconf import OmegaConf

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

OUT = "revision/snapshots/continuous_unbiasedness/main_spec"
BASE = "revision/snapshots/C_normalized/beta1_curve.csv"
FRAME = f"{tempfile.gettempdir()}/pfd_mainspec_frame2.parquet"
COVS = ["TsDur", "Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
        "Compet_WTA"]
BINS = [0, 1, 3, 6, 12, 24, 48, np.inf]

pd.set_option("display.width", 220)


def block(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78, flush=True)


def build():
    """Identisch zu `_cluster_inference.py:build()` -- echte Beobachtungen."""
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
    return d[keep].reset_index(drop=True)


def clustered_mean(x, g):
    """Mittelwert von x mit cluster-robustem SE (Cluster g)."""
    x = np.asarray(x, float)
    n = len(x)
    r = x - x.mean()
    s = pd.Series(r).groupby(np.asarray(g)).sum().to_numpy()
    se = float(np.sqrt((s ** 2).sum()) / n)
    return float(x.mean()), se, int(len(s))


# --------------------------------- 1) Was die Kurve in Figur 3 misst
block("1) DIE RMSE-KURVE DER PRODUKTION (Figur 3, rechtes Panel)")

pub = pd.read_csv(BASE)
r0, r1 = float(pub["rmse"].iloc[0]), float(pub["rmse"].iloc[-1])
print("Gemessen wird der Residual-RMSE der Unbiasedness-Regression "
      "(`fit_mixed_lm`),\nalso der Prognosefehler für den Ausgang bei "
      "Kenntnis des Preises in t.\n")
print(f"  Perzentil {pub['pctl'].iloc[0]:>3.0f}: RMSE {r0:.5f}")
print(f"  Perzentil {pub['pctl'].iloc[-1]:>3.0f}: RMSE {r1:.5f}")
print(f"  Rückgang        : {r1 - r0:+.5f}  ({(r1 / r0 - 1) * 100:+.2f} %)")
print("\nDer Referee hat recht: auf der RMSE-Skala ist das wenig.")

# --------------------------------- 2) Brier und Brier Skill Score
block("2) DIESELBE GRÖSSE ALS BRIER-SCORE UND SKILL SCORE")

b0, b1 = r0 ** 2, r1 ** 2
bss0, bss1 = 1 - b0 / 0.25, 1 - b1 / 0.25
print(f"  Brier Anfang / Ende : {b0:.5f} / {b1:.5f}   "
      f"(Rückgang {b1 - b0:+.5f}, {(b1 / b0 - 1) * 100:+.2f} %)")
print(f"  Brier Skill Score   : {bss0 * 100:.2f} % -> {bss1 * 100:.2f} %   "
      f"(+{(bss1 - bss0) * 100:.2f} Prozentpunkte)")
print(f"\n  Das Fenster steuert {(bss1 - bss0) / bss0 * 100:.1f} % dessen "
      f"bei, was der Preis am Anfang\n  des Fensters schon weiss "
      f"({bss0 * 100:.1f} % aufgelöste Ergebnisunsicherheit).")

curve = pd.DataFrame({
    "pctl": pub["pctl"], "rmse": pub["rmse"],
    "brier": pub["rmse"] ** 2, "bss": 1 - pub["rmse"] ** 2 / 0.25,
})
curve.to_csv(f"{OUT}/rmse_magnitude_curve.csv", index=False)

# ------------------- 3) Echte Beobachtungen, ohne Imputation, ohne Regression
block("3) ECHTE BEOBACHTUNGEN: RMSE DES PREISES p(t) SELBST")

try:
    df = pd.read_parquet(FRAME)
    print(f"Frame aus Cache: {len(df):,d} Zeilen")
except (FileNotFoundError, OSError):
    df = build()
    df.to_parquet(FRAME)
    print(f"Frame neu gebaut: {len(df):,d} Zeilen")

df["P"] = df["PRef"] + df["Exog"]
df["SqErr"] = (df["Match"] - df["P"]) ** 2
print(f"  {df['GroupId'].nunique():,d} Serien, "
      f"{df['Matchup'].nunique():,d} Matchups")

df["Bin"] = pd.cut(df["HoursToKick"], BINS)
agg = df.groupby("Bin", observed=True).agg(
    n=("SqErr", "size"), serien=("GroupId", "nunique"),
    brier=("SqErr", "mean"))
agg["rmse"] = np.sqrt(agg["brier"])
agg["bss_pct"] = (1 - agg["brier"] / 0.25) * 100
print("\nJe Stundenbin (Population wechselt zwischen den Bins!):")
print(agg.to_string(float_format=lambda v: f"{v:,.5f}"))
agg.to_csv(f"{OUT}/rmse_by_hour_bin.csv")

# Kompositionsfrei: je Serie erste gegen letzte echte Beobachtung.
first = df.groupby("GroupId", sort=False).first()
last = df.groupby("GroupId", sort=False).last()
d = last["SqErr"].to_numpy() - first["SqErr"].to_numpy()
m, se, ng = clustered_mean(d, first["Matchup"].to_numpy())

print(f"\nGepaart je Serie (erste vs. letzte echte Beobachtung), "
      f"{len(d):,d} Serien:")
print(f"  Brier erste Beobachtung : {first['SqErr'].mean():.5f}  "
      f"(im Mittel {first['HoursToKick'].mean():.1f} h vor Anpfiff)")
print(f"  Brier letzte Beobachtung: {last['SqErr'].mean():.5f}  "
      f"(im Mittel {last['HoursToKick'].mean():.2f} h vor Anpfiff)")
print(f"  Differenz               : {m:+.5f}   SE (Cluster, {ng:,d} Matchups) "
      f"{se:.5f}   t = {m / se:+.2f}")
print(f"  entspricht RMSE {np.sqrt(first['SqErr'].mean()):.5f} -> "
      f"{np.sqrt(last['SqErr'].mean()):.5f}")
print(f"  Brier Skill Score       : "
      f"{(1 - first['SqErr'].mean() / 0.25) * 100:.2f} % -> "
      f"{(1 - last['SqErr'].mean() / 0.25) * 100:.2f} %")

pd.DataFrame([{
    "brier_first": first["SqErr"].mean(), "brier_last": last["SqErr"].mean(),
    "diff": m, "se_cluster": se, "t": m / se, "n_series": len(d),
    "n_matchups": ng, "hours_first": first["HoursToKick"].mean(),
    "hours_last": last["HoursToKick"].mean(),
}]).to_csv(f"{OUT}/rmse_paired_first_last.csv", index=False)

# ------------------ 3b) Dieselbe Grösse auf dem imputierten Perzentilraster
block("3b) GEGENPROBE: DERSELBE BRIER AUF DEM IMPUTIERTEN PERZENTILRASTER")

# Teil 1 und Teil 3 messen nicht dasselbe Objekt (Residual-RMSE einer
# Regression gegen Brier des rohen Preises). Damit die Aussage "die Imputation
# vergrössert den Rückgang" belastbar ist, wird hier exakt die Grösse aus
# Teil 3 -- Brier des Preises selbst, erste gegen letzte Spalte -- auf dem
# Produktionsraster gerechnet.
wide = pd.read_hdf("revision/snapshots/C_normalized/wide_imputed.h5")
wide = wide[wide["NumOddsMvt"] < 20]
sq0 = (wide["Match"] - wide["OddsMvt0"]) ** 2
sq1 = (wide["Match"] - wide["OddsMvt50"]) ** 2
mg, seg, ngg = clustered_mean(sq1 - sq0, wide["Matchup"].to_numpy())

print(f"{len(wide):,d} Serien, {ngg:,d} Matchups (Produktionsraster)")
print(f"  Brier OddsMvt0  : {sq0.mean():.5f}   RMSE {np.sqrt(sq0.mean()):.5f}")
print(f"  Brier OddsMvt50 : {sq1.mean():.5f}   RMSE {np.sqrt(sq1.mean()):.5f}")
print(f"  Differenz       : {mg:+.5f}   SE (Cluster) {seg:.5f}   "
      f"t = {mg / seg:+.2f}")
print(f"\n  echt beobachtet (Teil 3): {m:+.5f}")
print(f"  imputiertes Raster      : {mg:+.5f}   "
      f"-> Faktor {mg / m:.2f}")

pd.DataFrame([
    {"Fassung": "echte Beobachtungen, erste vs. letzte",
     "brier_early": first["SqErr"].mean(), "brier_late": last["SqErr"].mean(),
     "diff": m, "se_cluster": se, "t": m / se, "n": len(d)},
    {"Fassung": "imputiertes Perzentilraster, OddsMvt0 vs. OddsMvt50",
     "brier_early": sq0.mean(), "brier_late": sq1.mean(),
     "diff": mg, "se_cluster": seg, "t": mg / seg, "n": len(wide)},
]).to_csv(f"{OUT}/rmse_real_vs_imputed.csv", index=False)

# --------------------------------------------- 4) Der ökonomische Massstab
block("4) EINORDNUNG")

print("  Münzwurf (p = 0,5)            : Brier 0,25000   RMSE 0,50000")
print(f"  Preis bei erster Beobachtung  : Brier "
      f"{first['SqErr'].mean():.5f}   RMSE "
      f"{np.sqrt(first['SqErr'].mean()):.5f}")
print(f"  Preis bei letzter Beobachtung : Brier "
      f"{last['SqErr'].mean():.5f}   RMSE "
      f"{np.sqrt(last['SqErr'].mean()):.5f}")
share = m / (first["SqErr"].mean() - 0.25)
print(f"\n  Anteil des Fensters an der gesamten Prognoseleistung des Preises:"
      f"\n  {share * 100:.1f} % -- die übrigen {100 - share * 100:.1f} % "
      f"stehen schon bei der ersten Beobachtung fest.")

print("\nDateien: rmse_magnitude_curve.csv, rmse_by_hour_bin.csv, "
      "rmse_paired_first_last.csv")
