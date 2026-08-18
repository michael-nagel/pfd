#!/usr/bin/env python3
"""GMM auf serieneigenem Zeitfenster vs. Baseline (rein diagnostisch).

Aenderung gegenueber v1: der matchweite Wide-Frame wird NICHT komplett neu
gebaut. Die matchweite Seite ist der committete `C_normalized/wide_imputed.h5`
(dieselbe Datenbasis, auf der auch `E_gmm_exponent_fix` rechnet); der eigene
Resample-Pfad wird stattdessen auf einer Teilstichprobe von Matchups gegen
genau diesen Frame geprueft. Das spart einen vollen Resample-Durchgang.

WICHTIG zur Referenz: der aktuelle Code enthaelt den Zerfallsexponenten-Fix
(Commit d8d26bc, gamma 0,032 -> 0,005). Die passende Referenz ist deshalb
`E_gmm_exponent_fix/gmm_by_bookie.csv`, NICHT `C_normalized/gmm_by_bookie.csv`.
"""

import sys
import time
from functools import partial
from multiprocessing import Pool

import numpy as np
import pandas as pd
from omegaconf import OmegaConf

sys.path.insert(0, "src")
from pfd.helpers import fit_gmm_mod  # noqa: E402
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402
from pfd.utils import pivot_df, resample  # noqa: E402

OUT = "revision/snapshots/eq_window_scope"
N_PER, INCR = 51, 5
START = [np.array([0.01])]
PCTLS = np.arange(0, 1 + 2 / 100, 2 / 100)
SUPPORT = [0, 26, 31, 36, 41, 46]


def _proc(df_sub):
    return df_sub.groupby("GroupId").apply(
        resample, period=None, freq="1min", pctls=PCTLS, include_groups=False)


def _partition(lst, n):
    avg, out, last = len(lst) / float(n), [], 0.0
    while last < len(lst):
        out.append(lst[int(last):int(last + avg)])
        last += avg
    return out


def build_wide(df, key, exog_cols, label):
    t0 = time.time()
    d = df.copy()
    d["TsStart"] = d.groupby(key)["Update"].transform("min")
    d["TsEnd"] = d.groupby(key)["Update"].transform("max")
    d = d.set_index("Update")
    parts = _partition(list(d["Matchup"].unique()), 6)
    with Pool(processes=6) as pool:
        res = pool.map(_proc, [d.loc[d["Matchup"].isin(p)] for p in parts])
    d = pd.concat(res, ignore_index=False)
    d = d.reset_index(level=1, drop=True).reset_index(drop=False)
    gstd = d.groupby("GroupId")["OddsMvt"].transform("std")
    d = d[gstd > 0]
    n_nan = int(d["OddsMvt"].isna().sum())
    d["CumCount"] = d.groupby("GroupId").cumcount()
    n_per = int(d.shape[0] / d.groupby("GroupId").ngroups)
    wide = pivot_df(d, exog_cols + ["NumOddsMvt", "IsPro", "IsFav", "Match"],
                    n_per)
    print(f"  {label:<22s} {time.time() - t0:6.1f} s  Serien {wide.shape[0]:,d}"
          f"  n_per {n_per}  NaN(long) {n_nan:,d} "
          f"({n_nan / len(d) * 100:.2f} %)", flush=True)
    return wide


def run_gmm(d, bookies, label):
    t0 = time.time()
    with Pool(processes=6) as pool:
        res = pool.map(partial(fit_gmm_mod, d, N_PER, INCR, START, "cue"),
                       bookies)
    out = pd.DataFrame([e[0] for e in res], index=bookies).rename_axis("bookie")
    print(f"  {label:<26s} mean gamma {out['gamma'].mean():.6f}  "
          f"({time.time() - t0:.1f} s)", flush=True)
    return out


if __name__ == "__main__":
    cfg = OmegaConf.create({"estimation": {
        "spec": "BmHome", "normalize": True, "compets": None,
        "bm_quantile": 0.25, "ts_dur": [12, 72], "period": None,
        "resample_freq": "1min", "pctl": 2}})
    raw = pd.read_hdf("data/processed/shaped_data.h5", "df")
    for c in ("Date", "Update"):
        raw[c] = pd.to_datetime(raw[c])
    df, _, _, exog_cols, *_ = filter_and_shape_data(raw.copy(), cfg)
    gstd = df.groupby("GroupId")["OddsMvt"].transform("std")
    df = df[gstd > 0].copy()
    print(f"Basis: {df['GroupId'].nunique():,d} Serien, "
          f"{df['Matchup'].nunique():,d} Matchups", flush=True)

    base = pd.read_hdf("revision/snapshots/C_normalized/wide_imputed.h5",
                       key="wide")
    print(f"Baseline-Frame (matchweit, imputiert): {base.shape[0]:,d} Serien",
          flush=True)

    # ---- Kontrolle des eigenen Resample-Pfads auf einer Matchup-Teilmenge
    print("\n=== Kontrolle: eigener Resample-Pfad vs. wide_imputed.h5 ===",
          flush=True)
    rng = np.random.default_rng(42)
    ms = rng.choice(df["Matchup"].unique(), size=2000, replace=False)
    chk = build_wide(df[df["Matchup"].isin(ms)].copy(), "Matchup", exog_cols,
                     "matchweit (2000 Mu)")
    k = ["Matchup", "Bookies"]
    m = base[k + [f"OddsMvt{i}" for i in SUPPORT]].merge(
        chk[k + [f"OddsMvt{i}" for i in SUPPORT]], on=k,
        suffixes=("_base", "_mine"))
    print(f"  gemeinsame Serien: {len(m):,d}")
    for i in SUPPORT:
        a = m[f"OddsMvt{i}_base"].to_numpy()
        b = m[f"OddsMvt{i}_mine"].to_numpy()
        ok = ~np.isnan(b)
        d_ = np.abs(a[ok] - b[ok])
        print(f"    OddsMvt{i:<3d} beobachtet {ok.sum():>7,d}  max|diff| "
              f"{d_.max():.3e}  identisch {np.mean(d_ < 1e-12) * 100:6.2f} %",
              flush=True)
    del chk, m

    # ---- serieneigener Frame, voll
    print("\n=== Serieneigenen Wide-Frame bauen ===", flush=True)
    w_own = build_wide(df, "GroupId", exog_cols, "serieneigen (voll)")
    w_own.to_parquet(f"{OUT}/wide_series_own.parquet")

    # ---- GMM
    bookies = sorted(base["Bookies"].unique())
    print(f"\n=== GMM, {len(bookies)} Bookmaker ===", flush=True)
    g_base = run_gmm(base, bookies, "matchweit (Baseline)")
    ref = pd.read_csv(
        "revision/snapshots/E_gmm_exponent_fix/gmm_by_bookie.csv", index_col=0)
    print(f"  Reproduktionscheck gegen E_gmm_exponent_fix: max |Delta| = "
          f"{(g_base['gamma'] - ref['gamma']).abs().max():.2e}", flush=True)
    ref_old = pd.read_csv(
        "revision/snapshots/C_normalized/gmm_by_bookie.csv", index_col=0)
    print(f"  (zum Vergleich gegen C_normalized, VOR dem Exponenten-Fix: "
          f"{(g_base['gamma'] - ref_old['gamma']).abs().max():.2e})", flush=True)

    g_own = run_gmm(w_own, sorted(w_own["Bookies"].unique()), "serieneigen")

    out = pd.DataFrame({
        "gamma_matchweit": g_base["gamma"], "gamma_serieneigen": g_own["gamma"],
        "se_matchweit": g_base["std_gamma"], "se_serieneigen": g_own["std_gamma"],
        "J_matchweit": g_base["J_stat"], "J_serieneigen": g_own["J_stat"],
        "p_matchweit": g_base["p_value"], "p_serieneigen": g_own["p_value"]})
    out["delta"] = out["gamma_serieneigen"] - out["gamma_matchweit"]
    out.to_csv(f"{OUT}/gmm_window_scope.csv")

    pd.set_option("display.width", 200)
    print("\n" + "=" * 78)
    print("GAMMA: MATCHWEITES vs. SERIENEIGENES FENSTER")
    print("=" * 78)
    print(out[["gamma_matchweit", "gamma_serieneigen", "delta",
               "p_matchweit", "p_serieneigen"]].round(5).to_string())
    mw, so = out["gamma_matchweit"], out["gamma_serieneigen"]
    print(f"\n  Mittel      {mw.mean():.6f} -> {so.mean():.6f}   "
          f"(Delta {out['delta'].mean():+.6f}, "
          f"{out['delta'].mean() / mw.mean() * 100:+.1f} %)")
    print(f"  Median      {mw.median():.6f} -> {so.median():.6f}")
    print(f"  Spanne      [{mw.min():.6f}, {mw.max():.6f}] -> "
          f"[{so.min():.6f}, {so.max():.6f}]")
    print(f"  Vorzeichen der Delta: +{(out['delta'] > 0).sum()} / "
          f"-{(out['delta'] < 0).sum()}")
    print(f"  Rangkorrelation (Spearman): {mw.corr(so, method='spearman'):.4f}")
    print(f"  argmin {mw.idxmin()} -> {so.idxmin()}   "
          f"argmax {mw.idxmax()} -> {so.idxmax()}")
    print(f"  negative gamma: {(mw < 0).sum()} -> {(so < 0).sum()}")
    print(f"  J-Test verworfen (p<0.05): {(out['p_matchweit'] < 0.05).sum()} -> "
          f"{(out['p_serieneigen'] < 0.05).sum()} von {len(out)}")
    print(f"\ngeschrieben: {OUT}/gmm_window_scope.csv", flush=True)
    print("FERTIG", flush=True)
