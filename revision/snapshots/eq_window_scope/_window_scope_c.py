#!/usr/bin/env python3
"""Teil (C) korrigiert + Aufwandsschaetzung fuer den GMM-Lauf.

Korrektur gegenueber dem ersten Lauf: dort wurden EINZELNE SERIEN gesampelt.
Das matchweite Fenster wird aber aus den im Frame vorhandenen Serien eines
Matchups gebildet - bei einer gesampelten Serie je Matchup ist es faktisch
das serieneigene. Hier werden deshalb GANZE MATCHUPS gezogen.
"""

import sys
import time

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
gstd = df.groupby("GroupId")["OddsMvt"].transform("std")
df = df[gstd > 0].copy()
n_series_tot = df["GroupId"].nunique()
n_match_tot = df["Matchup"].nunique()
print(f"Basis: {len(df):,d} Zeilen, {n_series_tot:,d} Serien, "
      f"{n_match_tot:,d} Matchups", flush=True)

# ------------------------------------------- (C) auf GANZEN Matchups
rng = np.random.default_rng(42)
match_sample = rng.choice(df["Matchup"].unique(), size=800, replace=False)
sub = df[df["Matchup"].isin(match_sample)].copy()
print(f"\nStichprobe: {len(match_sample)} Matchups, "
      f"{sub['GroupId'].nunique():,d} Serien, {len(sub):,d} Zeilen")
print(f"  Serien je Matchup: "
      f"{sub.groupby('Matchup')['GroupId'].nunique().mean():.1f} im Mittel")

print("\n" + "=" * 72)
print("(C) REST-NaN, MATCHUP-WEISE GEZOGEN")
print("=" * 72)
store = {}
for regime, key in (("matchweit", "Matchup"), ("serieneigen", "GroupId")):
    d = sub.copy()
    d["TsStart"] = d.groupby(key)["Update"].transform("min")
    d["TsEnd"] = d.groupby(key)["Update"].transform("max")
    d = d.set_index("Update")
    t0 = time.time()
    out = d.groupby("GroupId").apply(
        resample, period=None, freq="1min", pctls=PCTLS,
        include_groups=False)
    secs = time.time() - t0
    n_nan = int(out["OddsMvt"].isna().sum())
    store[regime] = (out, secs)
    print(f"  {regime:<12s} Zeilen {len(out):,d}  NaN {n_nan:,d} "
          f"({n_nan / len(out) * 100:.2f} %)  "
          f"Serien mit NaN {out['OddsMvt'].isna().groupby(level=0).any().sum():,d}"
          f"  |  {secs:.1f} s")

a, b = store["matchweit"][0], store["serieneigen"][0]
la = a.groupby(level=0)["OddsMvt"].last().to_numpy()
lb = b.groupby(level=0)["OddsMvt"].last().to_numpy()
print(f"\n  Schlusspreis identisch:        {np.allclose(la, lb)}")
print(f"  Startpreis serieneigen NaN-frei: "
      f"{b.groupby(level=0)['OddsMvt'].first().notna().all()}")

# Wie stark unterscheiden sich die GMM-Stuetzstellen zwischen den Regimen?
print("\n  Abweichung der GMM-Stuetzstellen (serieneigen vs. matchweit):")
for k in (0, 26, 31, 36, 41, 46):
    va = a.groupby(level=0)["OddsMvt"].nth(k).to_numpy()
    vb = b.groupby(level=0)["OddsMvt"].nth(k).to_numpy()
    ok = ~(np.isnan(va) | np.isnan(vb))
    d_ = np.abs(va[ok] - vb[ok])
    print(f"    OddsMvt{k:<3d}  mittel {d_.mean():.5f}  median "
          f"{np.median(d_):.5f}  max {d_.max():.4f}  "
          f"identisch {np.mean(d_ < 1e-12) * 100:5.1f} %")

# ------------------------------------------------ Aufwandsschaetzung
print("\n" + "=" * 72)
print("AUFWANDSSCHAETZUNG FUER DEN VOLLEN LAUF")
print("=" * 72)
secs_800 = store["serieneigen"][1]
scale = n_match_tot / len(match_sample)
print(f"  resample fuer 800 Matchups (1 Kern): {secs_800:.1f} s")
print(f"  Hochrechnung auf {n_match_tot:,d} Matchups, 1 Kern: "
      f"{secs_800 * scale / 60:.1f} min")
print(f"  bei 6 Kernen (Pool wie in der Pipeline): "
      f"~{secs_800 * scale / 60 / 6:.1f} min je Regime")
print("  + GMM je Bookmaker (24x, CUE) und Pivot: aus Erfahrung der")
print("    Pipeline die kleinere Position.")
