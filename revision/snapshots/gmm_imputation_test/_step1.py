#!/usr/bin/env python3
"""Step 1: rebuild the masking sample of masking_test.py, bit-for-bit.

Same source frames, same seed, same donor draw -> the same 24,568 candidate
series with the same masked cells. Caches the truth matrix and the imputed
matrix (plus Bookies/Match/NumOddsMvt) so the GMM step can run separately.
"""

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from pfd.helpers import impute_missings  # noqa: E402

OUT = "revision/snapshots/gmm_imputation_test"
# NOT /tmp: WSL shuts down between wsl.exe invocations and wipes it.
CACHE = ("/mnt/c/Users/micha/AppData/Local/Temp/claude/"
         "C--Users-micha-OneDrive-Michi-pfd/"
         "a7ef249b-96b6-4348-a367-df03535e0ea1/scratchpad/gmm_mask_cache.h5")
SEED = 42
COLS = [f"OddsMvt{i}" for i in range(51)]
rng = np.random.default_rng(SEED)

# ---- rebuild the pre-imputation wide frame (identical to masking_test.py) --
r = pd.read_hdf("data/interim/data_resampled.h5")
r["t"] = r.groupby("GroupId").cumcount()
pre = r.pivot(index="GroupId", columns="t", values="OddsMvt")
pre.columns = COLS
key = r.groupby("GroupId").agg(Matchup=("Matchup", "first"),
                               Bookies=("Bookies", "first"))
pre = pre.join(key).reset_index()

wide = pd.read_hdf("revision/snapshots/C_normalized/wide_imputed.h5")
meta = wide.drop(columns=COLS)
w = meta.merge(pre.drop(columns="GroupId"), on=["Matchup", "Bookies"],
               how="inner")
assert len(w) == len(wide), f"join {len(w)} != {len(wide)}"
print(f"Pre-Imputations-Frame: {w.shape}, NaN-Anteil "
      f"{w[COLS].isna().values.mean() * 100:.2f}%")

na = w[COLS].isna()
lead = na.cumprod(axis=1).sum(axis=1)
cand = (~na.any(axis=1)) & (w["NumOddsMvt"] < 20)
donor = lead[(lead > 0) & (w["NumOddsMvt"] < 20)].to_numpy()
print(f"Kandidaten: {cand.sum():,d}   Spender-Blocklaengen: {len(donor):,d}")

# ---- mask leading blocks in the same pattern ------------------------------
truth = w.loc[cand, COLS].copy()
blk = rng.choice(donor, size=int(cand.sum()), replace=True)
mask = np.zeros((int(cand.sum()), 51), dtype=bool)
for i, b in enumerate(blk):
    mask[i, :b] = True
print(f"maskierte Zellen: {mask.sum():,d} "
      f"({mask.sum() / mask.size * 100:.2f}%), Blocklaenge median "
      f"{np.median(blk):.0f} mean {blk.mean():.1f} max {blk.max():.0f}")

w_mask = w.copy()
sub = w_mask.loc[cand, COLS].to_numpy()
sub[mask] = np.nan
w_mask.loc[cand, COLS] = sub

print("\nImputer laeuft (Produktionsfunktion, ohne Match, Seed 42) ...")
imp = impute_missings(df=w_mask.copy(), seed=SEED)
print("fertig.")

got = imp.loc[cand, COLS].to_numpy()
tru = truth.to_numpy()
err = got[mask] - tru[mask]
print(f"Kontrolle gegen masking_test.py: RMSE {np.sqrt((err ** 2).mean()):.5f}"
      f"  Bias {err.mean():+.5f}  corr {np.corrcoef(got[mask], tru[mask])[0, 1]:.4f}")

# ---- diagnostics that matter for the GMM support points -------------------
sup = [51 - i * 5 for i in range(1, 6)] + [0]          # 46 41 36 31 26 0
alt = [51 - i * 5 for i in range(1, 6)] + [21]         # 46 41 36 31 26 21

rate = pd.Series(mask.mean(axis=0), index=range(51))
print("\nMaskierungsanteil je Stuetzstelle (Masking-Design):")
for c in sorted(set(sup + alt)):
    print(f"  OddsMvt{c:<3d} {rate[c] * 100:6.2f}%")

# same, for the real production frame (share of originally-missing cells)
prod_na = wide[COLS].isna()  # imputed frame -> use the pre frame instead
prod_rate = w[COLS].isna().mean()
print("\nImputationsanteil je Stuetzstelle (Produktions-Baseline C_normalized):")
for c in sorted(set(sup + alt)):
    print(f"  OddsMvt{c:<3d} {prod_rate[f'OddsMvt{c}'] * 100:6.2f}%")
assert prod_na.values.sum() == 0

# ---- per-bookmaker candidate counts ---------------------------------------
bk = w.loc[cand, "Bookies"].value_counts().sort_index()
print(f"\nKandidaten je Bookmaker (gesamt {bk.sum():,d}, "
      f"{len(bk)} Bookmaker):")
for b, n in bk.items():
    print(f"  {b:<14s} {n:>7,d}")

# ---- cache -----------------------------------------------------------------
side = w.loc[cand, ["Bookies", "Match", "NumOddsMvt", "Matchup"]].reset_index(
    drop=True)
d_tru = pd.concat([side, pd.DataFrame(tru, columns=COLS)], axis=1)
d_imp = pd.concat([side, pd.DataFrame(got, columns=COLS)], axis=1)
d_tru.to_hdf(CACHE, key="true", mode="w")
d_imp.to_hdf(CACHE, key="imputed")
pd.DataFrame(mask, columns=COLS).to_hdf(CACHE, key="mask")
print(f"\ngecacht nach {CACHE}: {d_tru.shape}")
