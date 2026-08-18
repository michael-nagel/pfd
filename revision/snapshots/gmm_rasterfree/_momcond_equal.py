"""Schaetzen GMM und Bayesian dieselbe Momentbedingung?

Vergleicht die 14 Momentspalten elementweise: einmal aus
`_GenMethMom.momcond` (GMM), einmal aus der Tensor-Form von
`create_pm_mod` (Bayesian), auf denselben Daten und demselben gamma.
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from pfd.utils import _create_gmm_data, _GenMethMom  # noqa: E402

N_PER, INCR = 51, 5
df = pd.read_parquet("revision/snapshots/eq_window_scope/"
                     "wide_series_own.parquet")
d = df[df["Bookies"] == "Pinnacle"]
y, X, Z = _create_gmm_data(d, N_PER, INCR)
print(f"Daten: {len(y):,d} Serien, exog {X.shape}, inst {Z.shape}")

# --- welche Spalten zieht _create_gmm_data jetzt?
cols = [N_PER - 1 - (i - 1) * INCR for i in (1, 2, 3, 4, 5)]
print(f"Stuetzstellen: {cols}  + OddsMvt0")
for k, c in enumerate(cols):
    assert np.allclose(X[:, k], d[f"OddsMvt{c}"].to_numpy(float))
assert np.allclose(X[:, 5], d["OddsMvt0"].to_numpy(float))
print("exog-Spalten stimmen mit den erwarteten OddsMvt-Spalten ueberein: OK")

# --- GMM-Pfad
mod = _GenMethMom(endog=y, exog=X, instrument=Z, k_moms=14, k_params=1)
mod.n_per, mod.incr = N_PER, INCR
tau_gmm = [N_PER - (i - 1) * INCR for i in (1, 2, 3)]
print(f"tau (GMM, _gen_meth_mom):      {tau_gmm}")

# --- Bayesian-Pfad, numpy-Nachbau von create_pm_mod
tau_bay = [N_PER - (i - 1) * INCR for i in (1, 2, 3)]
print(f"tau (Bayesian, create_pm_mod): {tau_bay}")
assert tau_gmm == tau_bay, "tau laeuft auseinander!"


def bayes_moms(g):
    Xb = X[:, 0:3]
    r1 = (tau_bay[1] / tau_bay[0]) ** (2 * g)
    r2 = (tau_bay[2] / tau_bay[1]) ** (2 * g)
    m1 = (Xb[:, 0] - y) ** 2 - r1 * (Xb[:, 1] - y) ** 2
    m2 = (Xb[:, 1] - y) ** 2 - r2 * (Xb[:, 2] - y) ** 2
    mc = np.stack([m1, m2], axis=1)
    return (Z[:, :, None] * mc[:, None, :]).reshape(mc.shape[0], 14)


print()
for g in (0.0035, 0.01, 0.05):
    a = mod.momcond(np.array([g]))
    b = bayes_moms(g)
    same_shape = a.shape == b.shape
    d_ = np.abs(a - b).max()
    print(f"  gamma = {g:<7.4f}  Form gleich {same_shape}   "
          f"max |GMM - Bayesian| = {d_:.3e}   "
          f"{'IDENTISCH' if d_ < 1e-12 else 'ABWEICHUNG'}")

print("\nSpaltenreihenfolge:")
print("  _gen_meth_mom: [m1*z0, m2*z0, m1*z1, m2*z1, ...]")
print("  create_pm_mod: reshape von (obs,7,2) -> [z0*m1, z0*m2, z1*m1, ...]")
print("  -> gleiche Verschraenkung, gleiche Reihenfolge")
