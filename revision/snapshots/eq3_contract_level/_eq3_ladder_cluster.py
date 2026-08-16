#!/usr/bin/env python3
"""Cluster-robuste SEs fuer die Stufen S1 und S2 der R2-C1-Leiter.

Die Snapshot-Skripte rechnen den CR1-Sandwich nur fuer die S3/S4-Designmatrix
(`cluster_robust.csv`); fuer die Antwortstabelle werden die cluster-robusten
SEs auch fuer S1 und S2 gebraucht. Rein diagnostisch, gleiche Datenbasis und
gleicher Code-Pfad wie `_eq3_contract.py`.

Kontrolle: S3 muss `ladder.csv` und `cluster_robust.csv` exakt reproduzieren.
"""

import importlib.util
import sys
import tempfile
import types

import numpy as np
import pandas as pd
from omegaconf import OmegaConf

sys.path.insert(0, "src")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# `import pfd.models.filter_and_shape` would run the package __init__ chain,
# which pulls in statsmodels/hydra and does not import in any Python on this
# machine. filter_and_shape itself needs only three light helpers, so we load
# it directly and hand it a `pfd.utils` module carrying just those three.
_pfd = types.ModuleType("pfd")
_pfd.__path__ = ["src/pfd"]
sys.modules["pfd"] = _pfd
_utils = types.ModuleType("pfd.utils")
_utils.PFDConfig = _load("_fas_config", "src/pfd/utils/config.py").PFDConfig
_utils.enc_categ_var = _load(
    "_fas_enc", "src/pfd/utils/enc_categ_var.py").enc_categ_var
_utils.scale_vars = _load(
    "_fas_scale", "src/pfd/utils/scale_vars.py").scale_vars
sys.modules["pfd.utils"] = _utils

filter_and_shape_data = _load(
    "_fas", "src/pfd/models/filter_and_shape.py").filter_and_shape_data

SNAP = "revision/snapshots/eq3_contract_level"
FRAME = f"{tempfile.gettempdir()}/pfd_eq3_frame.parquet"
COMPETS = ["Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
           "Compet_WTA"]


def build():
    cfg = OmegaConf.create({"estimation": {
        "spec": "BmHome", "normalize": True, "compets": None,
        "bm_quantile": 0.25, "ts_dur": [12, 72], "period": None,
        "resample_freq": "1min", "pctl": 2}})
    raw = pd.read_hdf("data/processed/shaped_data.h5", "df")
    for c in ("Date", "Update"):
        raw[c] = pd.to_datetime(raw[c])
    df, *_ = filter_and_shape_data(raw.copy(), cfg)
    d = df.groupby("GroupId", as_index=False).first()
    d["DltOpnCls"] = d["ClsOdds"] - d["OpnOdds"]
    d["RtrnOpnCls"] = d["ClsOdds"] / d["OpnOdds"] - 1
    keep = ["GroupId", "Matchup", "Bookies", "Match", "OpnOdds", "ClsOdds",
            "DltOpnCls", "RtrnOpnCls", "TsDur"] + COMPETS
    d = d[keep].reset_index(drop=True)
    d.to_parquet(FRAME)
    return d


try:
    d_all = pd.read_parquet(FRAME)
    print(f"Frame aus Cache: {len(d_all):,d} Kontrakte", flush=True)
except (FileNotFoundError, OSError):
    d_all = build()
    print(f"Frame neu gebaut: {len(d_all):,d} Kontrakte", flush=True)

d = d_all[d_all["RtrnOpnCls"].abs() > 0].reset_index(drop=True)
print(f"  nach Filter: {len(d):,d} Kontrakte, "
      f"{d['Matchup'].nunique():,d} Matchups", flush=True)

X_COLS = {
    "S1": ["DltOpnCls"],
    "S2": ["OpnOdds", "DltOpnCls"],
    "S3": ["OpnOdds", "DltOpnCls", "TsDur"] + COMPETS,
}

y = d["Match"].to_numpy(float)
codes = pd.factorize(d["Matchup"], sort=False)[0]
G = codes.max() + 1

out = []
for s, cols in X_COLS.items():
    X = np.column_stack([np.ones(len(d))] + [d[c].to_numpy(float)
                                             for c in cols])
    XtXi = np.linalg.inv(X.T @ X)
    b = XtXi @ (X.T @ y)
    u = y - X @ b
    N, K = len(y), X.shape[1]
    se_m = np.sqrt(np.diag((u @ u) / (N - K) * XtXi))
    S = np.zeros((G, K))
    np.add.at(S, codes, X * u[:, None])
    cf = (G / (G - 1)) * ((N - 1) / (N - K))
    se_cr = np.sqrt(np.diag(cf * (XtXi @ (S.T @ S) @ XtXi)))
    r2 = 1 - (u @ u) / ((y - y.mean()) @ (y - y.mean()))
    names = ["(Intercept)"] + cols
    print(f"\n{s}   R2 = {r2:.6f}   N = {N:,d}  G = {G:,d}  K = {K}")
    for nm, bi, sm, sc in zip(names, b, se_m, se_cr, strict=True):
        print(f"   {nm:<24s} {bi:>10.5f}  SE_m {sm:.5f}  SE_cl {sc:.5f}"
              f"   t_cl = {bi / sc:>7.2f}")
        rec = {"Stufe": s, "term": nm, "beta": bi, "se_model": sm,
               "se_cluster": sc, "t_cluster": bi / sc, "R2": r2}
        if nm == "OpnOdds":
            rec["t_cluster_vs_1"] = (bi - 1.0) / sc
        out.append(rec)

res = pd.DataFrame(out)
res.to_csv(f"{SNAP}/ladder_cluster.csv", index=False)

# ------------------------------------------------ Kontrolle gegen Snapshot
print("\n" + "=" * 70 + "\nKONTROLLE GEGEN SNAPSHOT (S3 muss exakt stimmen)\n"
      + "=" * 70)
lad = pd.read_csv(f"{SNAP}/ladder.csv").set_index("Stufe")
cr = pd.read_csv(f"{SNAP}/cluster_robust.csv").set_index("term")
s3 = res[res["Stufe"] == "S3"].set_index("term")
for nm, col in (("(Intercept)", "eta_0"), ("OpnOdds", "eta_1"),
                ("DltOpnCls", "eta_2")):
    print(f"  {nm:<12s} beta  neu {s3.loc[nm, 'beta']:.10f}  "
          f"snapshot {lad.loc['S3', col]:.10f}  "
          f"diff {abs(s3.loc[nm, 'beta'] - lad.loc['S3', col]):.2e}")
    print(f"  {'':<12s} SE_cl neu {s3.loc[nm, 'se_cluster']:.10f}  "
          f"snapshot {cr.loc[nm, 'se_cluster']:.10f}  "
          f"diff {abs(s3.loc[nm, 'se_cluster'] - cr.loc[nm, 'se_cluster']):.2e}")
for st, col in (("S1", "eta_2"), ("S2", "eta_2"), ("S2", "eta_1")):
    nm = "DltOpnCls" if col == "eta_2" else "OpnOdds"
    got = res[(res["Stufe"] == st) & (res["term"] == nm)]["beta"].iloc[0]
    print(f"  {st} {col:<6s} beta  neu {got:.10f}  "
          f"snapshot {lad.loc[st, col]:.10f}  "
          f"diff {abs(got - lad.loc[st, col]):.2e}")
print(f"\ngeschrieben: {SNAP}/ladder_cluster.csv")
