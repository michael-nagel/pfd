#!/usr/bin/env python3
"""Woher kommt der gamma-Effekt der fortgeschriebenen Serien?

(1) paarweise Differenzen P46-P41 und P41-P36, sauber vs fortgeschrieben
(2) gamma nur auf den fortgeschriebenen Serien, V1 und V2
(3) unterscheiden sich diese Serien als Maerkte? Kovariatenvergleich
(4) Diskriminierender Test: gamma nach ANZAHL fortgeschriebener Stuetzstellen.
    Terminal-Stempel-These sagt: bei 1-2 gefuellten Stellen am hoechsten,
    bei 5 gefuellten gegen null (dann sind alle identisch).

Rein diagnostisch, kein Eingriff in die Produktions-Pipeline.
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
SCOLS = [f"OddsMvt{k}" for k in SUPPORT]
H = np.timedelta64(1, "h")
KEY = ["Matchup", "Bookies"]


def gmm_pooled(d, label):
    """Gepoolte Schaetzung: fit_gmm_mod filtert auf Bookies, also alle auf
    denselben Dummy setzen."""
    dd = d.copy()
    dd["Bookies"] = "ALL"
    res = fit_gmm_mod(dd, N_PER, INCR, START, "cue", "ALL")[0]
    t = res["gamma"] / res["std_gamma"] if res["std_gamma"] else np.nan
    print(f"  {label:<38s} n={len(d):>7,d}  gamma {res['gamma']:>9.6f}  "
          f"SE {res['std_gamma']:.6f}  t {t:>6.2f}", flush=True)
    return {"Gruppe": label, "n": len(d), "gamma": res["gamma"],
            "se": res["std_gamma"], "t": t, "J": res["J_stat"],
            "p": res["p_value"]}


def gmm_by_bookie(d, label):
    bks = sorted(d["Bookies"].unique())
    with Pool(processes=6) as pool:
        r = pool.map(partial(fit_gmm_mod, d, N_PER, INCR, START, "cue"), bks)
    o = pd.DataFrame([e[0] for e in r], index=bks)
    t = o["gamma"] / o["std_gamma"]
    print(f"  {label:<38s} n={len(d):>7,d}  gamma {o['gamma'].mean():.6f}  "
          f"Median {o['gamma'].median():.6f}  sig "
          f"{int((t.abs() > 1.96).sum())}/{len(bks)}", flush=True)
    return o


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
    s = pd.DataFrame({
        "Matchup": g["Matchup"].first(), "Bookies": g["Bookies"].first(),
        "own_start": g["Update"].min(), "own_end": g["Update"].max(),
        "NumOddsMvt": g["NumOddsMvt"].first(),
        "OpnOdds": g["OpnOdds"].first(), "IsFav": g["IsFav"].first(),
        "IsPro": g["IsPro"].first(), "Match": g["Match"].first()})
    m = df.groupby("Matchup")["Update"].agg(["min", "max"])
    s = s.join(m.rename(columns={"min": "m_start", "max": "m_end"}),
               on="Matchup")
    s["own_win_h"] = (s["own_end"] - s["own_start"]) / H
    s["m_win_h"] = (s["m_end"] - s["m_start"]) / H

    n_fill = pd.Series(0, index=s.index)
    for k in SUPPORT:
        t1 = s["m_start"] + pd.to_timedelta(
            (k / (N_PER - 1)) * (s["m_end"] - s["m_start"]) / H, unit="h")
        n_fill += (t1 > s["own_end"]).astype(int)
    s["n_fill"] = n_fill
    s["ffill"] = n_fill > 0

    v1 = pd.read_hdf("revision/snapshots/C_normalized/wide_imputed.h5",
                     key="wide")
    v2 = pd.read_parquet(f"{OUT}/wide_series_own.parquet")
    i1, i2 = pd.MultiIndex.from_frame(v1[KEY]), pd.MultiIndex.from_frame(v2[KEY])
    common = i1.intersection(i2)
    v1, v2 = v1[i1.isin(common)].copy(), v2[i2.isin(common)].copy()
    sk = s.set_index(KEY)
    for fr in (v1, v2):
        ix = pd.MultiIndex.from_frame(fr[KEY])
        fr["n_fill"] = sk["n_fill"].reindex(ix).fillna(0).to_numpy()
        fr["ffill"] = fr["n_fill"] > 0

    # ================================================ (1) paarweise Differenzen
    print("=" * 80)
    print("(1) PAARWEISE DIFFERENZEN DER BENACHBARTEN STUETZSTELLEN")
    print("=" * 80)
    rows = []
    for vn, fr in (("V1", v1), ("V2", v2)):
        for gl, mask in (("sauber", ~fr["ffill"]), ("fortgeschr.", fr["ffill"])):
            d = fr[mask]
            for lab, a, b in (("P46-P41", "OddsMvt46", "OddsMvt41"),
                              ("P41-P36", "OddsMvt41", "OddsMvt36")):
                x = (d[a] - d[b]).to_numpy(float)
                zero = np.mean(np.abs(x) < 1e-12) * 100
                print(f"  {vn} {gl:<12s} {lab}   exakt 0: {zero:6.2f} %   "
                      f"mean|d| {np.mean(np.abs(x)):.5f}   sd {x.std():.5f}   "
                      f"p90|d| {np.quantile(np.abs(x), .9):.5f}")
                rows.append({"Variante": vn, "Gruppe": gl, "Paar": lab,
                             "anteil_exakt_null": zero / 100,
                             "mean_abs": np.mean(np.abs(x)), "sd": x.std()})
        print()
    pd.DataFrame(rows).to_csv(f"{OUT}/pairwise_diffs.csv", index=False)

    # ============================= (2) gamma nur auf fortgeschriebenen Serien
    print("=" * 80)
    print("(2) GAMMA NUR AUF DEN FORTGESCHRIEBENEN SERIEN")
    print("=" * 80)
    pooled = [gmm_pooled(v1[~v1["ffill"]], "V1 | sauber (gepoolt)"),
              gmm_pooled(v1[v1["ffill"]], "V1 | fortgeschrieben (gepoolt)"),
              gmm_pooled(v2[~v2["ffill"]], "V2 | dieselben sauberen"),
              gmm_pooled(v2[v2["ffill"]], "V2 | dieselben fortgeschr.")]

    # ============================================= (4) Leiter nach n_fill
    print("\n" + "=" * 80)
    print("(4) GAMMA NACH ANZAHL FORTGESCHRIEBENER STUETZSTELLEN (V1, gepoolt)")
    print("=" * 80)
    print("  Terminal-Stempel-These: Maximum bei wenigen gefuellten Stellen,")
    print("  Zusammenbruch gegen 0 bei 5 gefuellten (dann alle identisch).\n")
    ladder = []
    for k in range(0, 6):
        sub = v1[v1["n_fill"] == k]
        if len(sub) < 300:
            print(f"  n_fill = {k}: nur {len(sub):,d} Serien - uebersprungen")
            continue
        ladder.append(gmm_pooled(sub, f"V1 | n_fill = {k}"))
    print()
    for k in range(1, 6):
        sub = v2[v2["n_fill"] == k]
        if len(sub) >= 300:
            ladder.append(gmm_pooled(sub, f"V2 | dieselben, n_fill = {k}"))
    pd.DataFrame(pooled + ladder).to_csv(f"{OUT}/gmm_fill_ladder.csv",
                                         index=False)

    # ==================================== (3) sind es andere Maerkte?
    print("\n" + "=" * 80)
    print("(3) UNTERSCHEIDEN SICH DIE FORTGESCHRIEBENEN SERIEN ALS MAERKTE?")
    print("=" * 80)
    a, b = s[~s["ffill"]], s[s["ffill"]]
    print(f"  {'Merkmal':<26s} {'sauber':>12s} {'fortgeschr.':>12s} {'Diff':>10s}")
    for lab, col in (("NumOddsMvt (Median)", "NumOddsMvt"),
                     ("eigenes Fenster h (Med)", "own_win_h"),
                     ("Matchup-Fenster h (Med)", "m_win_h"),
                     ("OpnOdds (Median)", "OpnOdds")):
        x, y = a[col].median(), b[col].median()
        print(f"  {lab:<26s} {x:>12.3f} {y:>12.3f} {y - x:>+10.3f}")
    for lab, col in (("Favoritenanteil", "IsFav"), ("Pro-Anteil", "IsPro"),
                     ("Gewinnrate", "Match")):
        x, y = a[col].mean(), b[col].mean()
        print(f"  {lab:<26s} {x:>12.4f} {y:>12.4f} {y - x:>+10.4f}")

    print("\n  Bookmaker: Anteil fortgeschriebener Serien je Bookmaker")
    bk = s.groupby("Bookies")["ffill"].agg(["mean", "size"]).sort_values("mean")
    bk["mean"] = (bk["mean"] * 100).round(2)
    print("    " + bk.rename(columns={"mean": "Anteil_%", "size": "n"})
          .to_string().replace("\n", "\n    "))
    bk.to_csv(f"{OUT}/ffill_by_bookie.csv")
    print(f"\n  Spannweite ueber Bookmaker: {bk['Anteil_%'].min():.1f} % bis "
          f"{bk['Anteil_%'].max():.1f} %")

    print(f"\ngeschrieben: {OUT}/pairwise_diffs.csv, {OUT}/gmm_fill_ladder.csv, "
          f"{OUT}/ffill_by_bookie.csv")
    print("FERTIG", flush=True)
