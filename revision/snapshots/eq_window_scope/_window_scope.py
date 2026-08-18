#!/usr/bin/env python3
"""Diagnose: matchweites vs. serieneigenes Zeitfenster (rein diagnostisch).

Aktuell setzt resample_and_impute.py
    TsStart = groupby("Matchup")["Update"].transform("min")
    TsEnd   = groupby("Matchup")["Update"].transform("max")
Bei serieneigenem Fenster waere es das Minimum/Maximum je GroupId
(= Matchup x Bookies).

Beantwortet:
  (A) Wie viele Serien starten spaeter als ihr Match, und wie stark?
  (B) Wie viele Rasterzellen sind dadurch NaN (= Imputationsmasse)?
  (C) Bleiben bei serieneigenem Fenster Rest-NaN uebrig? (direkt an
      resample() geprueft, beide Regime, identische Serien)
Kein Schreibzugriff auf die Pipeline.
"""

import sys

import numpy as np
import pandas as pd
from omegaconf import OmegaConf

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402
from pfd.utils import resample  # noqa: E402

OUT = "revision/snapshots/eq_window_scope"
PCTL = 2.0
PCTLS = np.arange(0, 1 + PCTL / 100, PCTL / 100)
N_PER = len(PCTLS)

cfg = OmegaConf.create({"estimation": {
    "spec": "BmHome", "normalize": True, "compets": None,
    "bm_quantile": 0.25, "ts_dur": [12, 72], "period": None,
    "resample_freq": "1min", "pctl": PCTL}})

raw = pd.read_hdf("data/processed/shaped_data.h5", "df")
for c in ("Date", "Update"):
    raw[c] = pd.to_datetime(raw[c])
df, *_ = filter_and_shape_data(raw.copy(), cfg)
print(f"nach filter_and_shape: {len(df):,d} Zeilen, "
      f"{df['GroupId'].nunique():,d} Serien, "
      f"{df['Matchup'].nunique():,d} Matchups", flush=True)

# resample_and_impute entfernt Serien ohne Preisvarianz (Zeile 96-97)
gstd = df.groupby("GroupId")["OddsMvt"].transform("std")
df = df[gstd > 0].copy()
print(f"nach Varianzfilter:   {len(df):,d} Zeilen, "
      f"{df['GroupId'].nunique():,d} Serien", flush=True)

print(f"\nRaster: pctl={PCTL} -> n_per={N_PER} Stuetzstellen (OddsMvt0..{N_PER-1})")

# ------------------------------------------------ (A) Eintrittsverspaetung
g = df.groupby("GroupId")
own = pd.DataFrame({
    "Matchup": g["Matchup"].first(),
    "own_start": g["Update"].min(),
    "own_end": g["Update"].max(),
})
m = df.groupby("Matchup")["Update"].agg(["min", "max"])
own = own.join(m.rename(columns={"min": "m_start", "max": "m_end"}),
               on="Matchup")

H = np.timedelta64(1, "h")
own["delay_h"] = (own["own_start"] - own["m_start"]) / H
own["tail_h"] = (own["m_end"] - own["own_end"]) / H
own["m_win_h"] = (own["m_end"] - own["m_start"]) / H
own["own_win_h"] = (own["own_end"] - own["own_start"]) / H
own["delay_frac"] = own["delay_h"] / own["m_win_h"]
own["tail_frac"] = own["tail_h"] / own["m_win_h"]

print("\n" + "=" * 72)
print("(A) EINTRITTSVERSPAETUNG (eigener Start vs. Matchup-Start)")
print("=" * 72)
late = own["delay_h"] > 0
print(f"  Serien insgesamt:              {len(own):,d}")
print(f"  Serien mit Verspaetung > 0:    {late.sum():,d} "
      f"({late.mean() * 100:.1f} %)")
print(f"  Serien exakt zeitgleich:       {(~late).sum():,d} "
      f"({(~late).mean() * 100:.1f} %)")
print("\n  Verspaetung in Stunden:")
print("    " + own["delay_h"].describe(
    percentiles=[.25, .5, .75, .9, .99]).round(3).to_string().replace(
    "\n", "\n    "))
print("\n  Fensterlaengen (Stunden, Median):")
print(f"    Matchup-Fenster {own['m_win_h'].median():.2f}   "
      f"eigenes Fenster {own['own_win_h'].median():.2f}   "
      f"Anteil {(own['own_win_h'] / own['m_win_h']).median():.4f}")

# ------------------------------------------- (B) Rasterzellen = Imputation
# Das 1-min-Raster ist gleichabstaendig, die Perzentile davon also linear in
# der Zeit: Stuetzstelle k liegt bei m_start + k/(n_per-1) * Fensterlaenge.
pos = np.arange(N_PER) / (N_PER - 1)
frac = own["delay_frac"].to_numpy()[:, None]
imputed_mask = pos[None, :] < frac          # Zelle liegt VOR eigenem Start
n_imp_per_series = imputed_mask.sum(axis=1)
own["n_imputed"] = n_imp_per_series

print("\n" + "=" * 72)
print("(B) IMPUTATIONSMASSE AUF DEM PERZENTILRASTER")
print("=" * 72)
tot_cells = len(own) * N_PER
print(f"  Zellen gesamt:                 {tot_cells:,d}")
print(f"  davon vor eigenem Start (NaN): {n_imp_per_series.sum():,d} "
      f"({n_imp_per_series.sum() / tot_cells * 100:.2f} %)")
print(f"  berichteter frac_missings:     7.84 %  (reports/values/values.dat)")
print(f"  Serien mit >= 1 imputierter Zelle: "
      f"{(n_imp_per_series > 0).sum():,d} "
      f"({(n_imp_per_series > 0).mean() * 100:.1f} %)")
print("\n  imputierte Stuetzstellen je Serie:")
print("    " + pd.Series(n_imp_per_series).describe(
    percentiles=[.5, .75, .9, .99]).round(2).to_string().replace(
    "\n", "\n    "))

print("\n  Anteil imputierter Serien je GMM-Stuetzstelle:")
gmm_pts = [N_PER - i * 5 for i in (1, 2, 3, 4, 5)] + [0]
for k in sorted(gmm_pts):
    share = imputed_mask[:, k].mean() * 100
    print(f"    OddsMvt{k:<3d} (= {pos[k] * 100:5.1f} % des Fensters): "
          f"{share:6.2f} % der Serien imputiert")

own.to_csv(f"{OUT}/window_scope_per_series.csv", index=True)

# --------------------------- (C) Rest-NaN bei serieneigenem Fenster?
print("\n" + "=" * 72)
print("(C) REST-NaN BEI SERIENEIGENEM FENSTER (direkt an resample())")
print("=" * 72)
rng = np.random.default_rng(42)
# bewusst Serien MIT Verspaetung ziehen - dort entsteht die Imputation
cand_late = own.index[own["n_imputed"] > 0].to_numpy()
cand_ontime = own.index[own["n_imputed"] == 0].to_numpy()
sample = np.concatenate([
    rng.choice(cand_late, size=min(300, len(cand_late)), replace=False),
    rng.choice(cand_ontime, size=min(100, len(cand_ontime)), replace=False)])
sub = df[df["GroupId"].isin(sample)].copy()

res = {}
for regime, keys in (("matchweit", "Matchup"), ("serieneigen", "GroupId")):
    d = sub.copy()
    d["TsStart"] = d.groupby(keys)["Update"].transform("min")
    d["TsEnd"] = d.groupby(keys)["Update"].transform("max")
    d = d.set_index("Update")
    out = d.groupby("GroupId").apply(
        resample, period=None, freq="1min", pctls=PCTLS,
        include_groups=False)
    n_nan = int(out["OddsMvt"].isna().sum())
    rows_per = out.groupby(level=0).size()
    res[regime] = (out, n_nan, rows_per)
    print(f"  {regime:<12s} Zeilen {len(out):,d}   NaN in OddsMvt {n_nan:,d}"
          f"   ({n_nan / len(out) * 100:.2f} %)   "
          f"Zeilen/Serie: min {rows_per.min()} max {rows_per.max()}")

a, b = res["matchweit"][0], res["serieneigen"][0]
print(f"\n  Serien im Test: {len(sample)} "
      f"({(own.loc[sample, 'n_imputed'] > 0).sum()} davon mit Verspaetung)")
print(f"  -> matchweit  imputationsbeduerftig: {res['matchweit'][1]:,d} Zellen")
print(f"  -> serieneigen imputationsbeduerftig: {res['serieneigen'][1]:,d} Zellen")

# Beobachtete (nicht ffill-erzeugte) Werte: stimmt der letzte Wert ueberein?
last_a = a.groupby(level=0)["OddsMvt"].last()
last_b = b.groupby(level=0)["OddsMvt"].last()
print(f"\n  Schlusspreis identisch in beiden Regimen: "
      f"{np.allclose(last_a.to_numpy(), last_b.to_numpy())}")
first_b = b.groupby(level=0)["OddsMvt"].first()
print(f"  Startpreis serieneigen nie NaN: {first_b.notna().all()}")
print(f"\ngeschrieben: {OUT}/window_scope_per_series.csv")
