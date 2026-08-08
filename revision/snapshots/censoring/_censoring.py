#!/usr/bin/env python3
"""Zensierung und der `NumOddsMvt < 20`-Filter (R1-v, vom AE priorisiert).

Referee 1 (Kommentar 5): Oddsportal liefert nur den Opening-Preis plus die
letzten 20 Updates. Der Preispfad ist damit zensiert, und der Filter auf
Serien mit weniger als 20 Preisaenderungen entfernt womoeglich genau die
aktivsten Maerkte. Gefordert: Zahl der verlorenen Beobachtungen, Vergleich
included gegen excluded, Robustheit der Schlussfolgerungen.

Dieses Skript liefert die ersten beiden Teile. Die Robustheit steht in
`_censoring_beta1.py`.

Wichtige Praezisierung vorab: der Filter sitzt NICHT in der Hauptpipeline,
sondern nur in `unbiasedness_regressions.py:55` und
`time_series_diagnostics.py:73`. Die Cross-Sections (RMSE, Tabellen 3-7) und
das GMM sehen ihn nicht.

Rein diagnostisch, kein Eingriff in die Produktions-Pipeline.
"""

import sys

import numpy as np
import pandas as pd
from omegaconf import OmegaConf

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

OUT = "revision/snapshots/censoring"
CAP = 20                                  # NumOddsMvt < 20

pd.set_option("display.width", 220)


def block(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78, flush=True)


cfg = OmegaConf.create({"estimation": {
    "spec": "BmHome", "normalize": True, "compets": None, "bm_quantile": 0.25,
    "ts_dur": [12, 72], "period": None, "resample_freq": "1min", "pctl": 2}})

raw = pd.read_hdf("data/processed/shaped_data.h5", "df")
for c in ("Date", "Update"):
    raw[c] = pd.to_datetime(raw[c])
n_raw_rows, n_raw_series = len(raw), raw.groupby(["Matchup", "Bookies"]).ngroups
df, desc, bookies, *_ = filter_and_shape_data(raw.copy(), cfg)
desc = desc.sort_values(["GroupId", "Update"])

g = desc.groupby("GroupId", sort=False)
d = pd.DataFrame({
    "Matchup": g["Matchup"].first(),
    "Bookies": g["Bookies"].first(),
    "Competition": g["Competition"].first(),
    "Match": g["Match"].first(),
    "IsFav": g["IsFav"].first(),
    "IsPro": g["IsPro"].first(),
    "OpnOdds": g["OpnOdds"].first(),
    "ClsOdds": g["ClsOdds"].first(),
    "NumOddsMvt": g["NumOddsMvt"].first(),
    "TsDurH": g["TsDur"].first(),
    "MarginOpn": g["Margin"].first(),
    "OpnHrs": ((g["Date"].first() - g["Update"].first())
               / np.timedelta64(1, "h")),
    "SdPrice": g["OddsMvt"].std(),
}).reset_index()
d["RtrnOpnCls"] = d["ClsOdds"] / d["OpnOdds"] - 1
d["AbsMove"] = (d["ClsOdds"] - d["OpnOdds"]).abs()
d.to_parquet(f"{OUT}/series_frame.parquet")

# ------------------------------------------------ 1) Wo greift der Filter
block("1) STUFEN DER STICHPROBE (Serienebene)")
zero_var = (d["SdPrice"].fillna(0) <= 0).sum()
kept_var = d[d["SdPrice"] > 0]
kept_cap = kept_var[kept_var["NumOddsMvt"] < CAP]
rows = [
    ("shaped_data (roh)", n_raw_series, n_raw_rows),
    ("nach filter_and_shape (Marge, Bookmaker, TsDur)", len(d), len(desc)),
    ("nach Nullvarianz-Filter (resample_and_impute)", len(kept_var), np.nan),
    (f"nach NumOddsMvt < {CAP} (nur Unbiasedness/GARCH)", len(kept_cap),
     np.nan),
]
prev = None
for lab, n, _ in rows:
    ch = "" if prev is None else f"   ({n - prev:+,d}, {n / prev * 100:.1f} %)"
    print(f"  {lab:<50s} {n:>8,d} Serien{ch}")
    prev = n
print(f"\n  Der Filter entfernt {len(kept_var) - len(kept_cap):,d} von "
      f"{len(kept_var):,d} Serien "
      f"({(1 - len(kept_cap) / len(kept_var)) * 100:.2f} %).")
print("  Er wirkt NUR auf die Unbiasedness-Regressionen (Figure 3) und die")
print("  GARCH-Diagnostik. RMSE, Tabellen 3-7 und GMM sind nicht betroffen.")
pd.DataFrame(rows, columns=["stufe", "n_serien", "n_zeilen"]).to_csv(
    f"{OUT}/sample_stages.csv", index=False)

# ------------------------------------------- 2) Verteilung der Updatezahl
block("2) VERTEILUNG DER ZAHL DER PREISAENDERUNGEN")
vc = (kept_var["NumOddsMvt"].value_counts().sort_index()
      .rename("n_serien").to_frame())
vc["anteil"] = vc["n_serien"] / len(kept_var)
vc["kumuliert"] = vc["anteil"].cumsum()
print(vc.tail(12).round(4).to_string())
vc.reset_index().to_csv(f"{OUT}/num_updates_distribution.csv", index=False)
print(f"\n  Median {kept_var['NumOddsMvt'].median():.0f}   "
      f"Mittel {kept_var['NumOddsMvt'].mean():.2f}   "
      f"Maximum {kept_var['NumOddsMvt'].max():.0f}")
print(f"  genau {CAP}: {(kept_var['NumOddsMvt'] == CAP).sum():,d}   "
      f"ueber {CAP}: {(kept_var['NumOddsMvt'] > CAP).sum():,d}")
print("\n  Die Datenquelle liefert Opening plus die letzten 20 Updates. Eine")
print("  Serie mit 20 oder mehr Aenderungen ist deshalb genau die, deren")
print("  Pfadmitte wir nicht sehen. Der Filter entfernt also die zensierten")
print("  Serien -- das ist Absicht, aber es selektiert auf Marktaktivitaet.")

# --------------------------------------------- 3) included vs. excluded
block("3) INCLUDED GEGEN EXCLUDED")
kept_var = kept_var.assign(grp=np.where(kept_var["NumOddsMvt"] < CAP,
                                        "included", "excluded"))
VARS = {
    "NumOddsMvt": "Preisänderungen",
    "TsDurH": "Fensterlänge (h)",
    "OpnHrs": "Posting-Zeitpunkt (h vor Anpfiff)",
    "OpnOdds": "Opening-Wahrscheinlichkeit",
    "AbsMove": "|Opening - Closing|",
    "MarginOpn": "Marge beim Opening",
    "Match": "Gewinnrate",
    "IsFav": "Anteil Favoriten",
    "IsPro": "Anteil ATP/WTA",
}
agg = kept_var.groupby("grp")[list(VARS)].agg(["mean", "median"]).T
tab = pd.DataFrame({
    "included_mean": [kept_var.loc[kept_var["grp"] == "included", v].mean()
                      for v in VARS],
    "excluded_mean": [kept_var.loc[kept_var["grp"] == "excluded", v].mean()
                      for v in VARS],
    "included_median": [kept_var.loc[kept_var["grp"] == "included",
                                     v].median() for v in VARS],
    "excluded_median": [kept_var.loc[kept_var["grp"] == "excluded",
                                     v].median() for v in VARS],
}, index=list(VARS))
tab["diff_mean"] = tab["excluded_mean"] - tab["included_mean"]
# standardisierte Differenz: Vergleichbarkeit ueber Groessen mit
# unterschiedlichen Einheiten
sd = kept_var[list(VARS)].std()
tab["std_diff"] = tab["diff_mean"] / sd
tab.index = [VARS[v] for v in tab.index]
print(tab.round(4).to_string())
tab.to_csv(f"{OUT}/included_vs_excluded.csv")
print(f"\n  n included {(kept_var['grp'] == 'included').sum():,d}   "
      f"n excluded {(kept_var['grp'] == 'excluded').sum():,d}")

# Matchups, die ganz verloren gehen
mu_all = kept_var["Matchup"].nunique()
mu_inc = kept_var.loc[kept_var["grp"] == "included", "Matchup"].nunique()
print(f"  Matchups gesamt {mu_all:,d}, davon mit mindestens einer "
      f"included-Serie {mu_inc:,d} ({mu_inc / mu_all * 100:.2f} %)")
print(f"  vollstaendig verlorene Matchups: {mu_all - mu_inc:,d}")

# --------------------------------------- 4) Wen trifft es, wo faellt es an
block("4) AUSSCHLUSSQUOTE JE BOOKMAKER UND WETTBEWERB")
for key, lab in (("Bookies", "Bookmaker"), ("Competition", "Wettbewerb")):
    t = (kept_var.assign(exc=(kept_var["grp"] == "excluded").astype(float))
         .groupby(key).agg(n=("exc", "size"), anteil_exc=("exc", "mean")))
    t = t.sort_values("anteil_exc", ascending=False)
    print(f"\n  {lab}:")
    print("    " + t.round(4).to_string().replace("\n", "\n    "))
    t.reset_index().to_csv(f"{OUT}/exclusion_by_{key.lower()}.csv",
                           index=False)

print(f"\ngeschrieben: {OUT}/sample_stages.csv, num_updates_distribution.csv, "
      f"included_vs_excluded.csv, exclusion_by_*.csv, series_frame.parquet")
