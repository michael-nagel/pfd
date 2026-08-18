#!/usr/bin/env python3
"""Fortsetzung: Leiter nach n_fill mit Fehlerbehandlung + Kovariatenvergleich.

Bei >=3 fortgeschriebenen Stuetzstellen wird die Momentkovarianz singulaer
(mehrere Instrumente sind Differenzen identischer Werte, also exakt 0). Der
CUE-Schaetzer bricht dann ab; als Rueckfall wird die Ein-Schritt-Schaetzung
mit Identitaetsgewichten benutzt (inv_weights = I, wie max_iter = 1).
Das Scheitern selbst ist Teil des Befundes.
"""

import sys

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


def gmm_pooled(d, label):
    dd = d.copy()
    dd["Bookies"] = "ALL"
    for mode, tag in (("cue", "CUE"), (1, "1-Schritt")):
        try:
            r = fit_gmm_mod(dd, N_PER, INCR, START, mode, "ALL")[0]
            t = r["gamma"] / r["std_gamma"] if r["std_gamma"] else np.nan
            print(f"  {label:<34s} n={len(d):>7,d}  gamma {r['gamma']:>9.6f}"
                  f"  SE {r['std_gamma']:.6f}  t {t:>7.2f}  [{tag}]", flush=True)
            return {"Gruppe": label, "n": len(d), "gamma": r["gamma"],
                    "se": r["std_gamma"], "t": t, "modus": tag}
        except Exception as e:
            if mode == "cue":
                print(f"  {label:<34s} n={len(d):>7,d}  CUE gescheitert: "
                      f"{type(e).__name__} -> Rueckfall", flush=True)
            else:
                print(f"  {label:<34s} n={len(d):>7,d}  BEIDE gescheitert: "
                      f"{type(e).__name__}", flush=True)
                return {"Gruppe": label, "n": len(d), "gamma": np.nan,
                        "se": np.nan, "t": np.nan, "modus": "gescheitert"}


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
        "NumOddsMvt": g["NumOddsMvt"].first(), "OpnOdds": g["OpnOdds"].first(),
        "IsFav": g["IsFav"].first(), "IsPro": g["IsPro"].first(),
        "Match": g["Match"].first()})
    m = df.groupby("Matchup")["Update"].agg(["min", "max"])
    s = s.join(m.rename(columns={"min": "m_start", "max": "m_end"}), on="Matchup")
    s["own_win_h"] = (s["own_end"] - s["own_start"]) / H
    s["m_win_h"] = (s["m_end"] - s["m_start"]) / H
    nf = pd.Series(0, index=s.index)
    for k in SUPPORT:
        t1 = s["m_start"] + pd.to_timedelta(
            (k / (N_PER - 1)) * (s["m_end"] - s["m_start"]) / H, unit="h")
        nf += (t1 > s["own_end"]).astype(int)
    s["n_fill"], s["ffill"] = nf, nf > 0

    v1 = pd.read_hdf("revision/snapshots/C_normalized/wide_imputed.h5", key="wide")
    v2 = pd.read_parquet(f"{OUT}/wide_series_own.parquet")
    i1, i2 = pd.MultiIndex.from_frame(v1[KEY]), pd.MultiIndex.from_frame(v2[KEY])
    common = i1.intersection(i2)
    v1, v2 = v1[i1.isin(common)].copy(), v2[i2.isin(common)].copy()
    sk = s.set_index(KEY)
    for fr in (v1, v2):
        fr["n_fill"] = sk["n_fill"].reindex(
            pd.MultiIndex.from_frame(fr[KEY])).fillna(0).to_numpy()

    print("=" * 78)
    print("LEITER: GAMMA NACH ANZAHL FORTGESCHRIEBENER STUETZSTELLEN")
    print("=" * 78)
    print("  Verteilung von n_fill (V1):")
    print("    " + v1["n_fill"].value_counts().sort_index().to_string()
          .replace("\n", "\n    "))
    print()
    lad = []
    for k in range(0, 6):
        sub = v1[v1["n_fill"] == k]
        if len(sub) >= 300:
            lad.append(gmm_pooled(sub, f"V1 | n_fill = {k}"))
    print()
    for k in range(0, 6):
        sub = v2[v2["n_fill"] == k]
        if len(sub) >= 300:
            lad.append(gmm_pooled(sub, f"V2 | dieselben, n_fill = {k}"))
    pd.DataFrame(lad).to_csv(f"{OUT}/gmm_fill_ladder.csv", index=False)

    print("\n" + "=" * 78)
    print("SIND ES ANDERE MAERKTE? KOVARIATENVERGLEICH")
    print("=" * 78)
    a, b = s[~s["ffill"]], s[s["ffill"]]
    print(f"  {'Merkmal':<28s} {'sauber':>11s} {'fortgeschr.':>12s} {'Diff':>10s}")
    for lab, col in (("NumOddsMvt (Median)", "NumOddsMvt"),
                     ("NumOddsMvt (Mittel)", "NumOddsMvt"),
                     ("eigenes Fenster h (Med)", "own_win_h"),
                     ("Matchup-Fenster h (Med)", "m_win_h"),
                     ("OpnOdds (Median)", "OpnOdds")):
        f = (lambda x: x.mean()) if "Mittel" in lab else (lambda x: x.median())
        x, y = f(a[col]), f(b[col])
        print(f"  {lab:<28s} {x:>11.3f} {y:>12.3f} {y - x:>+10.3f}")
    for lab, col in (("Favoritenanteil", "IsFav"), ("Pro-Anteil", "IsPro"),
                     ("Gewinnrate", "Match")):
        x, y = a[col].mean(), b[col].mean()
        print(f"  {lab:<28s} {x:>11.4f} {y:>12.4f} {y - x:>+10.4f}")

    print("\n  Anteil fortgeschriebener Serien je Bookmaker:")
    bk = s.groupby("Bookies")["ffill"].agg(["mean", "size"]).sort_values("mean")
    bk["mean"] = (bk["mean"] * 100).round(2)
    print("    " + bk.rename(columns={"mean": "Anteil_%", "size": "n"})
          .to_string().replace("\n", "\n    "))
    bk.to_csv(f"{OUT}/ffill_by_bookie.csv")
    print(f"\n  Spannweite: {bk['mean'].min():.1f} % bis "
          f"{bk['mean'].max():.1f} %")
    print("FERTIG", flush=True)
