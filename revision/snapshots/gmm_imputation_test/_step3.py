#!/usr/bin/env python3
"""Step 3: the OddsMvt0 -> OddsMvt21 support-point swap on the FULL baseline.

The masking sample is a 14% subset of early-opening bookmakers.  The same swap
on the production frame (C_normalized, 183,210 series) answers the paper-level
question: how much of the published gamma hangs on the 86%-imputed support
point?  The unswapped run doubles as a reproduction check against the
committed gmm_by_bookie.csv.
"""

import sys
from functools import partial
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from pfd.helpers import fit_gmm_mod  # noqa: E402

OUT = "revision/snapshots/gmm_imputation_test"
N_PER, INCR = 51, 5
START = [np.array([0.01])]

df = pd.read_hdf("revision/snapshots/C_normalized/wide_imputed.h5", key="wide")
bookies = sorted(df["Bookies"].unique())
print(f"Baseline-Frame: {df.shape}, {len(bookies)} Bookmaker")


def run(d, label):
    with Pool() as pool:
        res = pool.map(
            partial(fit_gmm_mod, d, N_PER, INCR, START, "cue"), bookies)
    out = pd.DataFrame([e[0] for e in res], index=bookies).rename_axis("bookie")
    print(f"  {label:<22s} mean gamma {out['gamma'].mean():.4f}")
    return out


base = run(df, "OddsMvt0 (Baseline)")
d21 = df.copy()
d21["OddsMvt0"] = d21["OddsMvt21"]
swap = run(d21, "OddsMvt21")

ref = pd.read_csv(f"{OUT}/../C_normalized/gmm_by_bookie.csv", index_col=0)
dev = (base["gamma"] - ref["gamma"]).abs().max()
print(f"\nReproduktionscheck gegen C_normalized/gmm_by_bookie.csv: "
      f"max |Delta| = {dev:.2e}")

g = pd.DataFrame({"gamma_mvt0": base["gamma"], "gamma_mvt21": swap["gamma"],
                  "std_mvt0": base["std_gamma"], "std_mvt21": swap["std_gamma"],
                  "J_mvt0": base["J_stat"], "J_mvt21": swap["J_stat"],
                  "p_mvt0": base["p_value"], "p_mvt21": swap["p_value"]})
g["delta"] = g["gamma_mvt21"] - g["gamma_mvt0"]
g.to_csv(f"{OUT}/gmm_baseline_support_swap.csv")

pd.set_option("display.width", 200)
print("\n" + "=" * 80)
print("Baseline: Stuetzstelle OddsMvt0 (86% imputiert) vs OddsMvt21")
print("=" * 80)
print(g[["gamma_mvt0", "gamma_mvt21", "delta", "p_mvt0", "p_mvt21"]]
      .round(4).to_string())
print(f"\n  mean gamma  {g['gamma_mvt0'].mean():.4f} -> "
      f"{g['gamma_mvt21'].mean():.4f}  (Delta {g['delta'].mean():+.4f}, "
      f"{g['delta'].mean() / g['gamma_mvt0'].mean() * 100:+.1f}%)")
print(f"  Spanne      [{g['gamma_mvt0'].min():.4f}, {g['gamma_mvt0'].max():.4f}]"
      f" -> [{g['gamma_mvt21'].min():.4f}, {g['gamma_mvt21'].max():.4f}]")
print(f"  Vorzeichen der Delta: +{(g['delta'] > 0).sum()} / "
      f"-{(g['delta'] < 0).sum()}")
print(f"  J-Test verworfen (p<0.05): {(g['p_mvt0'] < 0.05).sum()} -> "
      f"{(g['p_mvt21'] < 0.05).sum()} von {len(g)}")
