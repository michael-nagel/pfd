#!/usr/bin/env python3
"""2x2: {sauber, fortgeschrieben} x {V1, V2}. Rein diagnostisch.

Gruppenbildung nach dem V1-Raster:
  fortgeschrieben = mindestens eine der fuenf Stuetzstellen liegt zeitlich
                    hinter dem letzten echten Preis der Serie
Dieselben Serien sind unter V2 per Konstruktion alle sauber.

Zusaetzlich: wie viele der fuenf Stuetzstellen tragen denselben Wert?
Ties sind nicht automatisch Artefakt (ein Preis kann sich schlicht nicht
geaendert haben), deshalb wird die sauberen Gruppe als Kontrolle mitgefuehrt.

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
SCOLS = [f"OddsMvt{k}" for k in SUPPORT]
H = np.timedelta64(1, "h")
KEY = ["Matchup", "Bookies"]


def run_gmm(d, label):
    bookies = sorted(d["Bookies"].unique())
    with Pool(processes=6) as pool:
        res = pool.map(partial(fit_gmm_mod, d, N_PER, INCR, START, "cue"),
                       bookies)
    out = pd.DataFrame([e[0] for e in res], index=bookies).rename_axis("bookie")
    t = out["gamma"] / out["std_gamma"]
    print(f"  {label:<30s} n={len(d):>7,d}  gamma {out['gamma'].mean():.6f}"
          f"  Median {out['gamma'].median():.6f}  neg {int((out['gamma'] < 0).sum()):>2d}"
          f"  sig {int((t.abs() > 1.96).sum()):>2d}/{len(bookies)}", flush=True)
    return out


def tie_stats(fr, mask, label):
    v = fr.loc[mask, SCOLS].to_numpy()
    n_distinct = np.array([len(np.unique(np.round(r, 12))) for r in v])
    eq_last = (np.abs(v - v[:, [-1]]) < 1e-12).sum(axis=1)
    print(f"\n  {label}  (n = {len(v):,d})")
    print("    verschiedene Werte unter den 5 Stuetzstellen:")
    for k in range(1, 6):
        sh = (n_distinct == k).mean() * 100
        print(f"      {k} verschieden: {sh:6.2f} %")
    print(f"    Mittel verschiedener Werte: {n_distinct.mean():.3f}")
    print(f"    Stuetzstellen gleich der letzten (OddsMvt46), Mittel: "
          f"{eq_last.mean():.3f} von 5")
    print(f"    davon >= 2 gleich der letzten: {(eq_last >= 2).mean() * 100:.2f} %"
          f"   >= 3: {(eq_last >= 3).mean() * 100:.2f} %")
    return {"Gruppe": label, "n": len(v),
            "mittel_verschiedene_Werte": n_distinct.mean(),
            "anteil_alle5_gleich": (n_distinct == 1).mean(),
            "mittel_gleich_letzter": eq_last.mean(),
            "anteil_ge2_gleich_letzter": (eq_last >= 2).mean(),
            "anteil_ge3_gleich_letzter": (eq_last >= 3).mean()}


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

    ffill = pd.Series(False, index=s.index)
    for k in SUPPORT:
        f = k / (N_PER - 1)
        t1 = s["m_start"] + pd.to_timedelta(
            f * (s["m_end"] - s["m_start"]) / H, unit="h")
        ffill |= t1 > s["own_end"]
    s["ffill"] = ffill
    print("=" * 78)
    print("GRUPPEN (nach dem V1-Raster gebildet)")
    print("=" * 78)
    print(f"  sauber           {int((~ffill).sum()):>7,d} "
          f"({(~ffill).mean() * 100:5.1f} %)")
    print(f"  fortgeschrieben  {int(ffill.sum()):>7,d} "
          f"({ffill.mean() * 100:5.1f} %)")

    flag = s.set_index(KEY)["ffill"]
    v1 = pd.read_hdf("revision/snapshots/C_normalized/wide_imputed.h5",
                     key="wide")
    v2 = pd.read_parquet(f"{OUT}/wide_series_own.parquet")

    # gemeinsame Serien, damit die Gruppen in beiden Frames identisch sind
    i1 = pd.MultiIndex.from_frame(v1[KEY])
    i2 = pd.MultiIndex.from_frame(v2[KEY])
    common = i1.intersection(i2)
    v1 = v1[i1.isin(common)].copy()
    v2 = v2[pd.MultiIndex.from_frame(v2[KEY]).isin(common)].copy()
    f1 = flag.reindex(pd.MultiIndex.from_frame(v1[KEY])).fillna(False).to_numpy()
    f2 = flag.reindex(pd.MultiIndex.from_frame(v2[KEY])).fillna(False).to_numpy()
    print(f"  in beiden Frames: {len(common):,d} Serien "
          f"(davon fortgeschrieben {int(f1.sum()):,d})")

    print("\n" + "=" * 78)
    print("GAMMA JE GRUPPE UND VARIANTE")
    print("=" * 78)
    r = {}
    r["V1_sauber"] = run_gmm(v1[~f1], "V1 | sauber")
    r["V1_ffill"] = run_gmm(v1[f1], "V1 | fortgeschrieben")
    r["V2_sauber"] = run_gmm(v2[~f2], "V2 | dieselben sauberen")
    r["V2_ffill"] = run_gmm(v2[f2], "V2 | dieselben fortgeschr.")

    print("\n" + "=" * 78)
    print("STUETZSTELLEN MIT IDENTISCHEM WERT")
    print("=" * 78)
    rows = [tie_stats(v1, ~f1, "V1 | sauber"),
            tie_stats(v1, f1, "V1 | fortgeschrieben"),
            tie_stats(v2, f2, "V2 | dieselben fortgeschr. Serien")]
    pd.DataFrame(rows).to_csv(f"{OUT}/support_ties.csv", index=False)

    print("\n" + "=" * 78)
    print("ZUSAMMENFASSUNG")
    print("=" * 78)
    print(f"  {'':<22s} {'V1':>12s} {'V2':>12s} {'V2 - V1':>12s}")
    for grp in ("sauber", "ffill"):
        a, b = r[f"V1_{grp}"]["gamma"].mean(), r[f"V2_{grp}"]["gamma"].mean()
        print(f"  {grp:<22s} {a:>12.6f} {b:>12.6f} {b - a:>+12.6f}")
    print("\n  Hypothese: fortgeschriebene Serien haben unter V1 ein HOEHERES")
    print("  gamma als unter V2. Zutreffend? "
          f"{r['V1_ffill']['gamma'].mean() > r['V2_ffill']['gamma'].mean()}")

    out = pd.DataFrame({k: v["gamma"] for k, v in r.items()})
    out.to_csv(f"{OUT}/gmm_group_split.csv")
    print(f"\ngeschrieben: {OUT}/gmm_group_split.csv, {OUT}/support_ties.csv")
    print("FERTIG", flush=True)
