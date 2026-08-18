#!/usr/bin/env python3
"""Variante 3: TsStart serieneigen, TsEnd matchweit. Rein diagnostisch.

Trennt die beiden Kanaele, die Variante 2 (beides serieneigen) vermengt:
  - Fensteranfang -> Imputation (entfaellt in Variante 2 UND 3)
  - Fensterende   -> Neuvertaktung der Stuetzstellen (nur in Variante 2)

Zusaetzlich:
  (1) Verteilung von (Matchup-Ende - eigenes Ende)
  (2) Anteil der Stuetzstellen HINTER dem letzten beobachteten Preis,
      je Variante und je Stuetzstelle, plus Staleness
  (3) gamma je Bookmaker, alle drei Varianten, Spearman

Kein Eingriff in die Produktions-Pipeline.
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
SUPPORT = [26, 31, 36, 41, 46]
H = np.timedelta64(1, "h")


def _proc(df_sub):
    return df_sub.groupby("GroupId").apply(
        resample, period=None, freq="1min", pctls=PCTLS, include_groups=False)


def _partition(lst, n):
    avg, out, last = len(lst) / float(n), [], 0.0
    while last < len(lst):
        out.append(lst[int(last):int(last + avg)])
        last += avg
    return out


def build_wide(df, start_key, end_key, exog_cols, label):
    t0 = time.time()
    d = df.copy()
    d["TsStart"] = d.groupby(start_key)["Update"].transform("min")
    d["TsEnd"] = d.groupby(end_key)["Update"].transform("max")
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
    print(f"  {label:<28s} {time.time() - t0:6.1f} s  Serien {wide.shape[0]:,d}"
          f"  n_per {n_per}  NaN {n_nan:,d} ({n_nan / len(d) * 100:.2f} %)",
          flush=True)
    return wide


def run_gmm(d, bookies, label):
    with Pool(processes=6) as pool:
        res = pool.map(partial(fit_gmm_mod, d, N_PER, INCR, START, "cue"),
                       bookies)
    out = pd.DataFrame([e[0] for e in res], index=bookies).rename_axis("bookie")
    print(f"  {label:<28s} mean gamma {out['gamma'].mean():.6f}", flush=True)
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
          f"{df['Matchup'].nunique():,d} Matchups\n", flush=True)

    # ============================================ (1) Schwanz am Fensterende
    g = df.groupby("GroupId")
    s = pd.DataFrame({"Matchup": g["Matchup"].first(),
                      "own_start": g["Update"].min(),
                      "own_end": g["Update"].max()})
    m = df.groupby("Matchup")["Update"].agg(["min", "max"])
    s = s.join(m.rename(columns={"min": "m_start", "max": "m_end"}), on="Matchup")
    s["tail_h"] = (s["m_end"] - s["own_end"]) / H
    s["delay_h"] = (s["own_start"] - s["m_start"]) / H
    s["m_win_h"] = (s["m_end"] - s["m_start"]) / H
    s["own_win_h"] = (s["own_end"] - s["own_start"]) / H
    s["v3_win_h"] = (s["m_end"] - s["own_start"]) / H

    print("=" * 74)
    print("(1) SERIEN, DIE VOR DEM MATCHUP-ENDE AUFHOEREN")
    print("=" * 74)
    early = s["tail_h"] > 0
    print(f"  Serien insgesamt:                {len(s):,d}")
    print(f"  enden vor dem Matchup-Ende:      {early.sum():,d} "
          f"({early.mean() * 100:.1f} %)")
    print(f"  enden exakt am Matchup-Ende:     {(~early).sum():,d} "
          f"({(~early).mean() * 100:.1f} %)")
    print("\n  Abstand eigenes Ende -> Matchup-Ende (Stunden):")
    print("    " + s["tail_h"].describe(
        percentiles=[.25, .5, .75, .9, .99]).round(3).to_string().replace(
        "\n", "\n    "))
    print(f"\n  Anteil des Matchup-Fensters, der hinter dem eigenen Ende "
          f"liegt:\n    Median {(s['tail_h'] / s['m_win_h']).median() * 100:.2f} %"
          f"   Mittel {(s['tail_h'] / s['m_win_h']).mean() * 100:.2f} %")

    # ================================ (2) Stuetzstellen hinter dem letzten Preis
    print("\n" + "=" * 74)
    print("(2) STUETZSTELLEN HINTER DEM LETZTEN BEOBACHTETEN PREIS")
    print("=" * 74)
    print("  Definition: die Rasterzelle liegt zeitlich NACH dem letzten")
    print("  tatsaechlichen Update der Serie; ihr Wert ist dann eine ueber")
    print("  das Quotierungsende hinaus fortgeschriebene Konstante.\n")

    # Fenstergrenzen je Variante: (Startzeit, Endzeit)
    variants = {
        "V1 matchweit":   (s["m_start"], s["m_end"]),
        "V2 serieneigen": (s["own_start"], s["own_end"]),
        "V3 Start eigen / Ende matchweit": (s["own_start"], s["m_end"]),
    }
    rows = []
    for vname, (t0_, t1_) in variants.items():
        win = (t1_ - t0_) / H
        print(f"  {vname}")
        for k in SUPPORT:
            tk = t0_ + pd.to_timedelta((k / (N_PER - 1)) * win, unit="h")
            beyond = tk > s["own_end"]
            stale = ((tk - s["own_end"]) / H).where(beyond)
            print(f"    OddsMvt{k:<3d} hinter dem letzten Preis: "
                  f"{beyond.mean() * 100:6.2f} %   "
                  f"Staleness Median {stale.median() if beyond.any() else 0:6.2f} h"
                  f"   p90 {stale.quantile(.9) if beyond.any() else 0:6.2f} h")
            rows.append({"Variante": vname, "Stuetzstelle": f"OddsMvt{k}",
                         "Anteil_hinter_letztem_Preis": beyond.mean(),
                         "Staleness_Median_h": stale.median(),
                         "Staleness_p90_h": stale.quantile(.9)})
        print()
    pd.DataFrame(rows).to_csv(f"{OUT}/support_beyond_last_price.csv",
                              index=False)

    # ---------------------------------------------------- (3) GMM Variante 3
    print("=" * 74)
    print("(3) GMM, VARIANTE 3")
    print("=" * 74)
    w3 = build_wide(df, "GroupId", "Matchup", exog_cols, "V3 (Start eigen)")
    w3.to_parquet(f"{OUT}/wide_variant3.parquet")

    base = pd.read_hdf("revision/snapshots/C_normalized/wide_imputed.h5",
                       key="wide")
    bookies = sorted(base["Bookies"].unique())
    g3 = run_gmm(w3, sorted(w3["Bookies"].unique()), "V3")

    prev = pd.read_csv(f"{OUT}/gmm_window_scope.csv", index_col=0)
    out = pd.DataFrame({
        "gamma_V1_matchweit": prev["gamma_matchweit"],
        "gamma_V2_serieneigen": prev["gamma_serieneigen"],
        "gamma_V3_start_eigen": g3["gamma"],
        "se_V3": g3["std_gamma"], "p_V3": g3["p_value"],
        "se_V1": prev["se_matchweit"], "se_V2": prev["se_serieneigen"],
        "p_V1": prev["p_matchweit"], "p_V2": prev["p_serieneigen"]})
    out.to_csv(f"{OUT}/gmm_three_variants.csv")

    pd.set_option("display.width", 220)
    print("\n" + "=" * 74)
    print("GAMMA JE BOOKMAKER, DREI VARIANTEN")
    print("=" * 74)
    cols = ["gamma_V1_matchweit", "gamma_V2_serieneigen", "gamma_V3_start_eigen"]
    print(out[cols].round(6).to_string())
    print("\n  Zusammenfassung:")
    for c in cols:
        v = out[c]
        t = v / out["se_" + c.split("_")[1]]
        print(f"    {c:<24s} Mittel {v.mean():.6f}  Median {v.median():.6f}  "
              f"Spanne [{v.min():.6f}, {v.max():.6f}]  "
              f"negativ {int((v < 0).sum())}  "
              f"signifikant {int((t.abs() > 1.96).sum())}/24")
    print("\n  Differenzen zum Baseline-Mittel (V1 = "
          f"{out[cols[0]].mean():.6f}):")
    for c in cols[1:]:
        d_ = out[c].mean() - out[cols[0]].mean()
        print(f"    {c:<24s} {d_:+.6f}  ({d_ / out[cols[0]].mean() * 100:+.1f} %)")
    print("\n  Spearman-Rangkorrelationen:")
    for a, b in ((0, 1), (0, 2), (1, 2)):
        print(f"    {cols[a]:<24s} vs {cols[b]:<24s} "
              f"{out[cols[a]].corr(out[cols[b]], method='spearman'):.4f}")
    print("\n  argmin / argmax:")
    for c in cols:
        print(f"    {c:<24s} min {out[c].idxmin():<12s} max {out[c].idxmax()}")
    print(f"\ngeschrieben: {OUT}/gmm_three_variants.csv, "
          f"{OUT}/support_beyond_last_price.csv")
    print("FERTIG", flush=True)
