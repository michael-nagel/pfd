#!/usr/bin/env python3
"""Cluster-robuste Inferenz für die DISKRETE Unbiasedness-Spezifikation (R1-ii).

Warum das hier noch fehlte: die bisher berichteten Cluster-Zahlen für die
Unbiasedness-Regression stammen aus der kontinuierlichen Spezifikation
(`../continuous_unbiasedness/main_spec/`). Die wechselt gleichzeitig die
Zeitachse (log-Stunden statt Perzentile), die Datenbasis (echte
Beobachtungen statt Perzentilraster) und den Schätzer (GAM statt 50
Mixed-LM-Fits). Der SE-Faktor dort vermengt also Clusterung UND
Achsenwechsel.

Dieses Skript isoliert die Clusterung: dieselbe Produktionsspezifikation,
dieselben Daten (`revision-baseline`, `C_normalized/wide_imputed.h5`),
derselbe Punktschätzer -- nur die Kovarianzmatrix wechselt von modellbasiert
auf CR1-Sandwich, geclustert auf Matchup.

Vorgehen wie in `../cluster_inference_eq12/`:
  1) Gate: reproduziert OLS den Mixed-LM-Punktschätzer der Baseline?
  2) CR1-Sandwich je Perzentil, Faktor gegen die modellbasierte SE.

Rein diagnostisch, nichts an der Produktions-Pipeline.
"""

import numpy as np
import pandas as pd

WIDE = "revision/snapshots/C_normalized/wide_imputed.h5"
CURVE = "revision/snapshots/C_normalized/beta1_curve.csv"
OUT = "revision/snapshots/cluster_inference_unbiased"
COVS = ["TsDur", "Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
        "Compet_WTA"]
GATE = 0.01

pd.set_option("display.width", 220)


def cr1(X, y, g):
    """OLS mit CR1-Cluster-Sandwich. Gibt beta, SE_iid, SE_cluster zurück."""
    n, k = X.shape
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ (X.T @ y)
    u = y - X @ beta

    se_iid = np.sqrt(np.diag(xtx_inv) * (u @ u) / (n - k))

    # Sum_g X_g' u_g u_g' X_g  ueber die Cluster
    Xu = X * u[:, None]
    meat = np.zeros((k, k))
    order = np.argsort(g)
    Xu, gs = Xu[order], g[order]
    bounds = np.flatnonzero(np.r_[True, gs[1:] != gs[:-1], True])
    for a, b in zip(bounds[:-1], bounds[1:]):
        s = Xu[a:b].sum(axis=0)
        meat += np.outer(s, s)

    G = len(bounds) - 1
    c = (G / (G - 1)) * ((n - 1) / (n - k))
    V = c * xtx_inv @ meat @ xtx_inv
    return beta, se_iid, np.sqrt(np.diag(V)), G


df = pd.read_hdf(WIDE)
df = df[df["NumOddsMvt"] < 20].reset_index(drop=True)
curve = pd.read_csv(CURVE)

cols = [f"OddsMvt{i}" for i in range(51)]
endog = (df["Match"] - df["OddsMvt0"]).to_numpy(float)
g = pd.factorize(df["Matchup"])[0]
C = df[COVS].to_numpy(float)
base = df["OddsMvt0"].to_numpy(float)

print(f"{len(df):,d} Serien, {df['Matchup'].nunique():,d} Matchups, "
      f"{df['Bookies'].nunique()} Bookmaker")
print(f"Perzentile: {len(cols) - 1}\n")

rows = []
for i, col in enumerate(cols[1:], start=1):
    exog = df[col].to_numpy(float) - base
    X = np.column_stack([np.ones(len(df)), exog, C])
    beta, se_iid, se_cl, G = cr1(X, endog, g)
    ref = curve.iloc[i - 1]
    rows.append({
        "pctl": int(ref["pctl"]),
        "beta_1_mixedlm": ref["beta_1"],
        "beta_1_ols": beta[1],
        "gate_diff": abs(beta[1] - ref["beta_1"]),
        "se_model": ref["std_beta_1"],
        "se_iid": se_iid[1],
        "se_cluster": se_cl[1],
        "factor_vs_model": se_cl[1] / ref["std_beta_1"],
        "factor_vs_iid": se_cl[1] / se_iid[1],
    })

r = pd.DataFrame(rows)
r["t_model"] = (r["beta_1_mixedlm"] - 1) / r["se_model"]
r["t_cluster"] = (r["beta_1_ols"] - 1) / r["se_cluster"]
r["sig_model"] = r["t_model"].abs() > 1.959964
r["sig_cluster"] = r["t_cluster"].abs() > 1.959964
r.to_csv(f"{OUT}/discrete_cluster_beta1.csv", index=False)

print("=" * 78)
print("1) GATE: OLS GEGEN DEN MIXED-LM-PUNKTSCHÄTZER DER BASELINE")
print("=" * 78)
print(f"max |beta_1(OLS) - beta_1(MixedLM)| = {r['gate_diff'].max():.6f}   "
      f"Median {r['gate_diff'].median():.6f}")
print(f"Schwelle {GATE}  ->  Gate "
      f"{'HÄLT' if r['gate_diff'].max() < GATE else 'HÄLT NICHT'}")

print("\n" + "=" * 78)
print("2) CR1-SANDWICH AUF MATCHUP")
print("=" * 78)
print(f"Faktor Cluster / modellbasiert: Median {r['factor_vs_model'].median():.2f}"
      f"   Spanne {r['factor_vs_model'].min():.2f}-{r['factor_vs_model'].max():.2f}")
print(f"Faktor Cluster / iid          : Median {r['factor_vs_iid'].median():.2f}"
      f"   Spanne {r['factor_vs_iid'].min():.2f}-{r['factor_vs_iid'].max():.2f}")
print(f"\nPerzentile mit beta_1 signifikant != 1:")
print(f"  modellbasiert : {int(r['sig_model'].sum())} / {len(r)}")
print(f"  cluster-robust: {int(r['sig_cluster'].sum())} / {len(r)}")

show = [2, 10, 25, 50, 75, 100]
print("\n" + r[r["pctl"].isin(show)][
    ["pctl", "beta_1_mixedlm", "beta_1_ols", "se_model", "se_cluster",
     "factor_vs_model", "t_model", "t_cluster"]
].to_string(index=False, float_format=lambda v: f"{v:9.4f}"))

print(f"\nDatei: {OUT}/discrete_cluster_beta1.csv")
