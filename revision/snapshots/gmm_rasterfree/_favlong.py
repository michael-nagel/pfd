#!/usr/bin/env python3
"""Bleiben Bookmaker-Ordnung und Favoriten/Longshot-Unterschied erhalten?

Prueft die Behauptung, die in die C2-Antwort soll, bevor sie geschrieben wird.
Verglichen werden die publizierte Fassung (V1|A) und die Kandidaten V2|A und
V2|B. Rein diagnostisch.
"""
import sys
import warnings

import numpy as np
import pandas as pd
from statsmodels.sandbox.regression.gmm import GMM

sys.path.insert(0, "src")
warnings.filterwarnings("ignore")
OUT = "revision/snapshots/gmm_rasterfree"
N_PER, INCR, K_MOMS = 51, 5, 14
SUP = {"A": [N_PER - i * INCR for i in (1, 2, 3, 4, 5)],
       "B": [N_PER - 1 - i * INCR for i in (0, 1, 2, 3, 4)]}


def build(df, cols):
    y = df["Match"].to_numpy(float)
    ex = [df[f"OddsMvt{c}"].to_numpy(float) for c in cols]
    inst = [np.ones(len(y))]
    for i in (4, 5):
        z = ex[i - 2] - ex[i - 1]
        inst.extend([z, z ** 2])
    ex.append(df["OddsMvt0"].to_numpy(float))
    z = ex[4] - ex[5]
    inst.extend([z, z ** 2])
    return y, np.column_stack(ex), np.column_stack(inst)


class Gmm(GMM):
    def momcond(self, params):
        g = float(params[0])
        y, X, Z = self.endog, self.exog, self.instrument
        t = self.tau
        r1, r2 = (t[1] / t[0]) ** (2 * g), (t[2] / t[1]) ** (2 * g)
        m1 = (X[:, 0] - y) ** 2 - r1 * (X[:, 1] - y) ** 2
        m2 = (X[:, 1] - y) ** 2 - r2 * (X[:, 2] - y) ** 2
        c = []
        for i in range(7):
            c.extend([m1 * Z[:, i], m2 * Z[:, i]])
        return np.column_stack(c)


def fit(d, cols, label):
    y, X, Z = build(d, cols)
    m = Gmm(endog=y, exog=X, instrument=Z, k_moms=K_MOMS, k_params=1)
    m.tau = [c + 1 for c in cols[:3]]
    try:
        r = m.fit(start_params=np.array([0.01]), maxiter="cue",
                  optim_method="nm")
        J, pJ, _ = r.jtest()
        print(f"    {label:<28s} n={len(y):>7,d}  gamma {r.params[0]:>9.6f}"
              f"  SE {r.bse[0]:.6f}  t {r.params[0] / r.bse[0]:>6.2f}"
              f"  J {J:6.2f} (p {pJ:.3f})", flush=True)
        return r.params[0], r.bse[0]
    except Exception as e:
        print(f"    {label:<28s} gescheitert: {type(e).__name__}")
        return np.nan, np.nan


frames = {
    "V1|A": (pd.read_hdf("revision/snapshots/C_normalized/wide_imputed.h5",
                         key="wide"), SUP["A"]),
    "V2|A": (pd.read_parquet("revision/snapshots/eq_window_scope/"
                             "wide_series_own.parquet"), SUP["A"]),
    "V2|B": (pd.read_parquet("revision/snapshots/eq_window_scope/"
                             "wide_series_own.parquet"), SUP["B"]),
}

print("=" * 76)
print("FAVORITEN vs. LONGSHOTS (gepoolt)")
print("=" * 76)
rows = []
for name, (fr, cols) in frames.items():
    print(f"\n  {name}")
    gf, sf = fit(fr[fr["IsFav"] == 1], cols, "Favoriten")
    gl, sl = fit(fr[fr["IsFav"] == 0], cols, "Longshots")
    diff = gf - gl
    se_d = np.sqrt(sf ** 2 + sl ** 2)
    print(f"    {'Differenz':<28s} {diff:>+9.6f}  SE {se_d:.6f}  "
          f"t {diff / se_d:>6.2f}")
    rows.append({"Spezifikation": name, "gamma_fav": gf, "gamma_long": gl,
                 "diff": diff, "se_diff": se_d, "t_diff": diff / se_d})
pd.DataFrame(rows).to_csv(f"{OUT}/favlong_by_spec.csv", index=False)

print("\n" + "=" * 76)
print("BOOKMAKER-ORDNUNG")
print("=" * 76)
g = pd.read_csv(f"{OUT}/support_shift_gamma.csv", index_col=0)
g.columns = ["V1|A", "V1|B", "V2|A", "V2|B"]
print("  Spearman gegen die publizierte Fassung V1|A:")
for c in ("V1|B", "V2|A", "V2|B"):
    print(f"    {c}: {g['V1|A'].corr(g[c], method='spearman'):.4f}   "
          f"Kendall {g['V1|A'].corr(g[c], method='kendall'):.4f}")
print("\n  Extremwerte:")
for c in g.columns:
    print(f"    {c}: argmin {g[c].idxmin():<12s} argmax {g[c].idxmax()}")
top = g["V1|A"].nlargest(5).index.tolist()
print(f"\n  Top-5 nach V1|A: {top}")
for c in ("V2|A", "V2|B"):
    print(f"    deren Raenge unter {c}: "
          f"{[int(g[c].rank(ascending=False)[b]) for b in top]}")
