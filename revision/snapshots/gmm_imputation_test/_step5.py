#!/usr/bin/env python3
"""Step 5: is the whole pooled shift carried by the 800 long-block series?

gamma is not additive across subsamples, so the bin table of step 4 does not
by itself prove that.  Direct test: pooled gamma with and without the 800
series whose masked block reaches into the support points.
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

tru = pd.read_hdf(CACHE, key="true")
imp = pd.read_hdf(CACHE, key="imputed")
blk = pd.read_hdf(CACHE, key="mask").to_numpy().sum(axis=1)


def pooled(df, sel):
    return fit_gmm_mod(df.loc[sel].assign(Bookies="P"), N_PER, INCR, START,
                       "cue", "P")[0]["gamma"]


rows = []
for name, sel in {"alle 24.568": np.ones(len(blk), bool),
                  "ohne Blocklaenge >=22 (n=23.768)": blk <= 21,
                  "nur Blocklaenge >=22 (n=800)": blk >= 22}.items():
    a = pooled(tru, sel)
    b = pooled(imp, sel)
    rows.append({"Teilstichprobe": name, "n": int(sel.sum()),
                 "gamma_true": a, "gamma_imputed": b, "diff": b - a})
    print(f"  {name:<34s} A {a:+.4f}  B {b:+.4f}  Diff {b - a:+.4f}",
          flush=True)

res = pd.DataFrame(rows)
res.to_csv(f"{OUT}/gmm_masking_influence.csv", index=False)
print("\n" + res.round(4).to_string(index=False))
