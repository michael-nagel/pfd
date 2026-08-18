#!/usr/bin/env python3
"""gamma auf Serien ohne fortgeschriebene Stuetzstellen. Rein diagnostisch.

Sauber = alle fuenf Stuetzstellen (OddsMvt26/31/36/41/46) liegen zeitlich
  - NICHT vor dem eigenen ersten Preis  (sonst imputiert)  und
  - NICHT nach dem eigenen letzten Preis (sonst fortgeschrieben).

Zwei Lesarten:
  (A) jede Variante auf IHRER eigenen sauberen Teilmenge
  (B) beide Varianten auf der SCHNITTMENGE - identische Serien, es bleibt
      allein die Neuvertaktung uebrig

Kein Eingriff in die Produktions-Pipeline.
"""

import sys
from functools import partial
from multiprocessing import Pool

import numpy as np
import pandas as pd
from omegaconf import OmegaConf

sys.path.insert(0, "src")
from pfd.helpers import fit_gmm_mod  # noqa: E402
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

OUT = "revision/snapshots/eq_window_scope"
N_PER, INCR = 51, 5
START = [np.array([0.01])]
SUPPORT = [26, 31, 36, 41, 46]
H = np.timedelta64(1, "h")
KEY = ["Matchup", "Bookies"]


def run_gmm(d, label):
    bookies = sorted(d["Bookies"].unique())
    with Pool(processes=6) as pool:
        res = pool.map(partial(fit_gmm_mod, d, N_PER, INCR, START, "cue"),
                       bookies)
    out = pd.DataFrame([e[0] for e in res], index=bookies).rename_axis("bookie")
    out["n"] = d.groupby("Bookies").size().reindex(bookies).to_numpy()
    t = out["gamma"] / out["std_gamma"]
    print(f"  {label:<34s} n={len(d):>7,d}  Bm={len(bookies):>2d}  "
          f"gamma {out['gamma'].mean():.6f}  Median {out['gamma'].median():.6f}"
          f"  neg {int((out['gamma'] < 0).sum()):>2d}  "
          f"sig {int((t.abs() > 1.96).sum()):>2d}/{len(bookies)}", flush=True)
    return out


if __name__ == "__main__":
    cfg = OmegaConf.create({"estimation": {
        "spec": "BmHome", "normalize": True, "compets": None,
        "bm_quantile": 0.25, "ts_dur": [12, 72], "period": None,
        "resample_freq": "1min", "pctl": 2}})
    raw = pd.read_hdf("data/processed/shaped_data.h5", "df")
    for c in ("Date", "Update"):
        raw[c] = pd.to_datetime(raw[c])
    df, *_ = filter_and_shape_data(raw.copy(), cfg)
    gstd = df.groupby("GroupId")["OddsMvt"].transform("std")
    df = df[gstd > 0].copy()

    g = df.groupby("GroupId")
    s = pd.DataFrame({"Matchup": g["Matchup"].first(),
                      "Bookies": g["Bookies"].first(),
                      "own_start": g["Update"].min(),
                      "own_end": g["Update"].max()})
    m = df.groupby("Matchup")["Update"].agg(["min", "max"])
    s = s.join(m.rename(columns={"min": "m_start", "max": "m_end"}),
               on="Matchup")

    # Rasterzeiten je Variante (1-min-Raster ist gleichabstaendig -> linear)
    ok_v1 = pd.Series(True, index=s.index)
    ok_v3 = pd.Series(True, index=s.index)
    for k in SUPPORT:
        f = k / (N_PER - 1)
        t1 = s["m_start"] + pd.to_timedelta(
            f * (s["m_end"] - s["m_start"]) / H, unit="h")
        t3 = s["own_start"] + pd.to_timedelta(
            f * (s["m_end"] - s["own_start"]) / H, unit="h")
        ok_v1 &= (t1 >= s["own_start"]) & (t1 <= s["own_end"])
        ok_v3 &= t3 <= s["own_end"]
    s["clean_v1"], s["clean_v3"] = ok_v1, ok_v3
    s["clean_both"] = ok_v1 & ok_v3

    print("=" * 78)
    print("SAUBERE SERIEN (alle fuenf Stuetzstellen beobachtet)")
    print("=" * 78)
    n = len(s)
    for c, lab in (("clean_v1", "V1 matchweit"), ("clean_v3", "V3 Start eigen"),
                   ("clean_both", "Schnittmenge V1 & V3")):
        print(f"  {lab:<24s} {int(s[c].sum()):>7,d} von {n:,d} "
              f"({s[c].mean() * 100:5.1f} %)")
    print("\n  V2 serieneigen ist per Konstruktion zu 100 % sauber.")

    frames = {
        "V1": pd.read_hdf("revision/snapshots/C_normalized/wide_imputed.h5",
                          key="wide"),
        "V2": pd.read_parquet(f"{OUT}/wide_series_own.parquet"),
        "V3": pd.read_parquet(f"{OUT}/wide_variant3.parquet"),
    }
    for v, fr in frames.items():
        print(f"  Frame {v}: {fr.shape[0]:,d} Serien")

    # Serien, die in ALLEN drei Frames vorkommen (Varianzfilter wirkt je Frame)
    common = None
    for fr in frames.values():
        idx = pd.MultiIndex.from_frame(fr[KEY])
        common = idx if common is None else common.intersection(idx)
    print(f"  in allen drei Frames: {len(common):,d} Serien")

    flags = s.set_index(KEY)[["clean_v1", "clean_v3", "clean_both"]]

    def sub(v, mask_col, restrict_common):
        fr = frames[v]
        ix = pd.MultiIndex.from_frame(fr[KEY])
        keep = flags[mask_col].reindex(ix).fillna(False).to_numpy()
        if restrict_common:
            keep &= ix.isin(common)
        return fr[keep]

    print("\n" + "=" * 78)
    print("(A) JEDE VARIANTE AUF IHRER EIGENEN SAUBEREN TEILMENGE")
    print("=" * 78)
    a1 = run_gmm(sub("V1", "clean_v1", False), "V1 | sauber unter V1")
    a3 = run_gmm(sub("V3", "clean_v3", False), "V3 | sauber unter V3")

    print("\n" + "=" * 78)
    print("(B) SCHNITTMENGE - IDENTISCHE SERIEN, NUR DIE VERTAKTUNG UNTERSCHEIDET")
    print("=" * 78)
    b1 = run_gmm(sub("V1", "clean_both", True), "V1 | Schnittmenge")
    b3 = run_gmm(sub("V3", "clean_both", True), "V3 | Schnittmenge")
    b2 = run_gmm(sub("V2", "clean_both", True), "V2 | Schnittmenge")

    print("\n" + "=" * 78)
    print("VERGLEICH")
    print("=" * 78)
    full = pd.read_csv(f"{OUT}/gmm_three_variants.csv", index_col=0)
    v1f = full["gamma_V1_matchweit"].mean()
    v3f = full["gamma_V3_start_eigen"].mean()
    v2f = full["gamma_V2_serieneigen"].mean()
    print(f"  volle Stichprobe    V1 {v1f:.6f}   V3 {v3f:.6f}   "
          f"V2 {v2f:.6f}   V3-V1 {v3f - v1f:+.6f} ({(v3f - v1f) / v1f * 100:+.1f} %)")
    print(f"  eigene saubere TM   V1 {a1['gamma'].mean():.6f}   "
          f"V3 {a3['gamma'].mean():.6f}                 "
          f"V3-V1 {a3['gamma'].mean() - a1['gamma'].mean():+.6f} "
          f"({(a3['gamma'].mean() - a1['gamma'].mean()) / a1['gamma'].mean() * 100:+.1f} %)")
    print(f"  Schnittmenge        V1 {b1['gamma'].mean():.6f}   "
          f"V3 {b3['gamma'].mean():.6f}   V2 {b2['gamma'].mean():.6f}   "
          f"V3-V1 {b3['gamma'].mean() - b1['gamma'].mean():+.6f} "
          f"({(b3['gamma'].mean() - b1['gamma'].mean()) / b1['gamma'].mean() * 100:+.1f} %)")
    print(f"\n  Spearman auf der Schnittmenge: V1 vs V3 "
          f"{b1['gamma'].corr(b3['gamma'], method='spearman'):.4f}   "
          f"V1 vs V2 {b1['gamma'].corr(b2['gamma'], method='spearman'):.4f}")
    print(f"  kleinste Bookmaker-n auf der Schnittmenge: "
          f"{sorted(b1['n'].tolist())[:5]}")

    res = pd.DataFrame({
        "gamma_V1_voll": full["gamma_V1_matchweit"],
        "gamma_V3_voll": full["gamma_V3_start_eigen"],
        "gamma_V1_sauber_eigen": a1["gamma"], "n_V1_sauber_eigen": a1["n"],
        "gamma_V3_sauber_eigen": a3["gamma"], "n_V3_sauber_eigen": a3["n"],
        "gamma_V1_schnitt": b1["gamma"], "gamma_V3_schnitt": b3["gamma"],
        "gamma_V2_schnitt": b2["gamma"], "n_schnitt": b1["n"],
        "se_V1_schnitt": b1["std_gamma"], "se_V3_schnitt": b3["std_gamma"]})
    res.to_csv(f"{OUT}/gmm_clean_subset.csv")
    print(f"\n  je Bookmaker auf der Schnittmenge:")
    print("    " + res[["gamma_V1_schnitt", "gamma_V3_schnitt",
                        "gamma_V2_schnitt", "n_schnitt"]].round(6)
          .to_string().replace("\n", "\n    "))
    print(f"\ngeschrieben: {OUT}/gmm_clean_subset.csv")
    print("FERTIG", flush=True)
