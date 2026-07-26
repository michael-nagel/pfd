#!/usr/bin/env python3
"""Step 4: where does the pooled gamma shift of the masking test come from?

B-A (+0.0130) and D-C (+0.0113) are almost equal, although spec D barely uses
an imputed support point.  So the shift cannot run through OddsMvt0.  This
splits the sample by masked-block length: a series only differs between the
true and the imputed run in its masked cells, so a series with block length 1
can move gamma ONLY via OddsMvt0, one with block >= 22 also via OddsMvt21 etc.
"""

import sys

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
COLS = [f"OddsMvt{i}" for i in range(51)]
SUP_0 = [46, 41, 36, 31, 26, 0]
SUP_21 = [46, 41, 36, 31, 26, 21]

tru = pd.read_hdf(CACHE, key="true")
imp = pd.read_hdf(CACHE, key="imputed")
mask = pd.read_hdf(CACHE, key="mask").to_numpy()

# ---- 1) observed cells must be untouched by the imputer -------------------
a, b = tru[COLS].to_numpy(), imp[COLS].to_numpy()
print(f"max |imputiert - wahr| auf NICHT maskierten Zellen: "
      f"{np.abs(a[~mask] - b[~mask]).max():.2e}")
print(f"max |imputiert - wahr| auf     maskierten Zellen: "
      f"{np.abs(a[mask] - b[mask]).max():.4f}")

blk = mask.sum(axis=1)
print(f"\nBlocklaenge: median {np.median(blk):.0f} mean {blk.mean():.1f} "
      f"max {blk.max():.0f}")
print(f"Serien mit mind. einer maskierten Stuetzstelle: "
      f"Spec OddsMvt0 {mask[:, SUP_0].any(axis=1).sum():,d}   "
      f"Spec OddsMvt21 {mask[:, SUP_21].any(axis=1).sum():,d}")


def pooled(df, sel, label):
    d = df.loc[sel].assign(Bookies="P")
    r = fit_gmm_mod(d, N_PER, INCR, START, "cue", "P")[0]
    return r["gamma"]


bins = {"1 (nur OddsMvt0)": blk == 1,
        "2-5": (blk >= 2) & (blk <= 5),
        "6-21": (blk >= 6) & (blk <= 21),
        ">=22 (auch OddsMvt21)": blk >= 22,
        "alle": np.ones(len(blk), bool)}

rows = []
for name, sel in bins.items():
    tr0 = pooled(tru, sel, name)
    im0 = pooled(imp, sel, name)
    tr21 = pooled(tru.assign(OddsMvt0=tru["OddsMvt21"]), sel, name)
    im21 = pooled(imp.assign(OddsMvt0=imp["OddsMvt21"]), sel, name)
    rows.append({"Blocklaenge": name, "n": int(sel.sum()),
                 "A_true_0": tr0, "B_imp_0": im0, "B-A": im0 - tr0,
                 "C_true_21": tr21, "D_imp_21": im21, "D-C": im21 - tr21})
    print(f"  {name:<24s} n={sel.sum():>6,d}  A {tr0:+.4f} B {im0:+.4f} "
          f"(B-A {im0 - tr0:+.4f})   C {tr21:+.4f} D {im21:+.4f} "
          f"(D-C {im21 - tr21:+.4f})", flush=True)

res = pd.DataFrame(rows)
res.to_csv(f"{OUT}/gmm_masking_by_blocklength.csv", index=False)

pd.set_option("display.width", 200)
print("\n" + "=" * 96)
print("gepoolte gamma je Blocklaenge (nur die maskierten Zellen einer Serie "
      "koennen A/B trennen)")
print("=" * 96)
print(res.round(4).to_string(index=False))
print("\nErwartung: bei Blocklaenge <= 21 sind in Spec C/D ALLE Stuetzstellen "
      "\n(46,41,36,31,26,21) echt beobachtet -> D-C muss exakt 0 sein.")
