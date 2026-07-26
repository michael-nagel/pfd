#!/usr/bin/env python3
"""Step 2: GMM (CUE) on the masking sample -- true vs imputed early values.

Four estimations on the SAME 24,568 fully-observed series:

  A  true      standard support points (..., OddsMvt0)
  B  imputed   standard support points          -> A vs B = imputation effect
  C  true      OddsMvt0 replaced by OddsMvt21
  D  imputed   OddsMvt0 replaced by OddsMvt21   -> C vs D = same, without the
                                                   imputed support point

The support point is swapped by overwriting the OddsMvt0 column, which is the
only place _create_gmm_data reads it (exog_list[5]); everything else is
untouched.  Per bookmaker and pooled.  Estimator settings mirror the baseline
gmm step exactly: n_per=51, incr=5, max_iter="cue", start 0.01.
"""

import sys
from functools import partial
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from pfd.helpers import fit_gmm_mod  # noqa: E402

CACHE = ("/mnt/c/Users/micha/AppData/Local/Temp/claude/"
         "C--Users-micha-OneDrive-Michi-pfd/"
         "a7ef249b-96b6-4348-a367-df03535e0ea1/scratchpad/gmm_mask_cache.h5")
OUT = "revision/snapshots/gmm_imputation_test"
N_PER, INCR = 51, 5
START = [np.array([0.01])]

SPECS = {"A_true_0": "A true    / OddsMvt0",
         "B_imp_0": "B imputed / OddsMvt0",
         "C_true_21": "C true    / OddsMvt21",
         "D_imp_21": "D imputed / OddsMvt21"}


def run(df, key):
    """Per-bookmaker CUE plus one pooled fit."""
    bookies = sorted(df["Bookies"].unique())
    with Pool() as pool:
        res = pool.map(
            partial(fit_gmm_mod, df, N_PER, INCR, START, "cue"), bookies)
    out = pd.DataFrame([e[0] for e in res], index=bookies).rename_axis("bookie")

    pooled = fit_gmm_mod(df.assign(Bookies="POOLED"), N_PER, INCR, START,
                         "cue", "POOLED")[0]
    out.loc["POOLED"] = pd.Series(pooled)

    out["n"] = df["Bookies"].value_counts().reindex(out.index)
    out.loc["POOLED", "n"] = len(df)
    out["spec"] = key
    print(f"  {SPECS[key]:<24s} mean gamma (je Bookie) "
          f"{out.drop(index='POOLED')['gamma'].mean():.4f}   "
          f"pooled {pooled['gamma']:.4f}", flush=True)
    return out


tru = pd.read_hdf(CACHE, key="true")
imp = pd.read_hdf(CACHE, key="imputed")
print(f"Sample: {len(tru):,d} Serien, {tru['Bookies'].nunique()} Bookmaker\n")

tru21, imp21 = tru.copy(), imp.copy()
tru21["OddsMvt0"] = tru21["OddsMvt21"]
imp21["OddsMvt0"] = imp21["OddsMvt21"]

frames = {"A_true_0": tru, "B_imp_0": imp, "C_true_21": tru21,
          "D_imp_21": imp21}
res = pd.concat([run(f, k) for k, f in frames.items()]).reset_index()
res.to_csv(f"{OUT}/gmm_masking_by_bookie.csv", index=False)

# ---- comparison table ------------------------------------------------------
g = res.pivot(index="bookie", columns="spec", values="gamma")[list(SPECS)]
g.insert(0, "n", res[res["spec"] == "A_true_0"].set_index("bookie")["n"]
         .astype(int))
g["B-A"] = g["B_imp_0"] - g["A_true_0"]
g["D-C"] = g["D_imp_21"] - g["C_true_21"]
g["C-A"] = g["C_true_21"] - g["A_true_0"]
g = g.sort_values("n", ascending=False)
g.to_csv(f"{OUT}/gmm_masking_gamma_compare.csv")

pd.set_option("display.width", 220)
print("\n" + "=" * 92)
print("gamma je Bookmaker  (B-A = Imputationseffekt, D-C = dito ohne "
      "imputierte Stuetzstelle)")
print("=" * 92)
print(g.round(4).to_string())

bo = g.drop(index="POOLED")
print("\n" + "=" * 92)
print("Zusammenfassung (24 Bookmaker, ohne POOLED)")
print("=" * 92)
for c in SPECS:
    print(f"  {c:<10s} mean {bo[c].mean():.4f}  median {bo[c].median():.4f}  "
          f"[{bo[c].min():.4f}, {bo[c].max():.4f}]")
for c in ["B-A", "D-C", "C-A"]:
    s = bo[c]
    print(f"  {c:<10s} mean {s.mean():+.4f}  median {s.median():+.4f}  "
          f"[{s.min():+.4f}, {s.max():+.4f}]  "
          f"Vorzeichen +{(s > 0).sum()}/-{(s < 0).sum()}")
p = g.loc["POOLED"]
print(f"\n  POOLED (n={int(p['n']):,d}): A {p['A_true_0']:.4f}  "
      f"B {p['B_imp_0']:.4f}  (B-A {p['B-A']:+.4f})   "
      f"C {p['C_true_21']:.4f}  D {p['D_imp_21']:.4f}  (D-C {p['D-C']:+.4f})")
