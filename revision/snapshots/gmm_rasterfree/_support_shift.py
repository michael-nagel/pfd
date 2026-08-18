#!/usr/bin/env python3
"""Stuetzstellen 46/41/36/31/26 (aktuell) vs. 50/45/40/35/30 (voll).

Hintergrund: solange endog = OddsMvt50 war (Biais), MUSSTEN die Stuetzstellen
darunter liegen. Seit endog = Match ist, waere OddsMvt50 verwendbar. Commit
d175c70 hat den Offset nur von (1 + i*incr) auf (0 + i*incr) geschoben und
zwei TODO-Marker hinterlassen.

Rein diagnostisch, `src/pfd` bleibt unberuehrt.
"""

import sys
import warnings
from functools import partial
from multiprocessing import Pool

import numpy as np
import pandas as pd
from omegaconf import OmegaConf
from statsmodels.sandbox.regression.gmm import GMM

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

warnings.filterwarnings("ignore")
OUT = "revision/snapshots/gmm_rasterfree"
N_PER, INCR, K_MOMS = 51, 5, 14
H = np.timedelta64(1, "h")
KEY = ["Matchup", "Bookies"]

# Variante A: aktuell.  Variante B: um incr nach hinten, bis zum Schlusspunkt.
VARIANTS = {
    "A 46/41/36/31/26 (aktuell)": [N_PER - i * INCR for i in (1, 2, 3, 4, 5)],
    "B 50/45/40/35/30 (voll)": [N_PER - 1 - i * INCR for i in (0, 1, 2, 3, 4)],
}


def build(df, cols):
    y = df["Match"].to_numpy(float)
    ex = [df[f"OddsMvt{c}"].to_numpy(float) for c in cols]
    inst = [np.ones(len(y))]
    for i in (4, 5):                       # wie im Original: nur i > 3
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
        cols = []
        for i in range(7):
            cols.extend([m1 * Z[:, i], m2 * Z[:, i]])
        return np.column_stack(cols)


def fit_one(args):
    d, cols, tau, b = args
    sub = d.loc[d["Bookies"] == b]
    y, X, Z = build(sub, cols)
    m = Gmm(endog=y, exog=X, instrument=Z, k_moms=K_MOMS, k_params=1)
    m.tau = tau
    try:
        r = m.fit(start_params=np.array([0.01]), maxiter="cue",
                  optim_method="nm")
        J, pJ, _ = r.jtest()
        return {"bookie": b, "gamma": r.params[0], "se": r.bse[0],
                "J": J, "pJ": pJ, "n": len(y)}
    except Exception as e:
        return {"bookie": b, "gamma": np.nan, "se": np.nan, "J": np.nan,
                "pJ": np.nan, "n": len(y), "err": type(e).__name__}


def run(d, cols, tau, label):
    bks = sorted(d["Bookies"].unique())
    with Pool(processes=6) as pool:
        res = pool.map(fit_one, [(d, cols, tau, b) for b in bks])
    o = pd.DataFrame(res).set_index("bookie")
    t = o["gamma"] / o["se"]
    print(f"  {label:<44s} gamma {o['gamma'].mean():.6f}  "
          f"Median {o['gamma'].median():.6f}  neg {int((o['gamma'] < 0).sum())}"
          f"  sig {int((t.abs() > 1.96).sum())}/{len(o)}  "
          f"J verw. {int((o['pJ'] < 0.05).sum())}/{len(o)}", flush=True)
    return o


if __name__ == "__main__":
    print("=" * 80)
    print("(2) STUETZSTELLEN UND ZERFALLSFAKTOREN")
    print("=" * 80)
    for name, cols in VARIANTS.items():
        tau = [c + 1 for c in cols[:3]]
        print(f"  {name:<30s} Spalten {cols}")
        print(f"  {'':<30s} tau     {tau}   Faktoren "
              f"{tau[1] / tau[0]:.5f} / {tau[2] / tau[1]:.5f}")
    a = [c + 1 for c in VARIANTS['A 46/41/36/31/26 (aktuell)'][:3]]
    b = [c + 1 for c in VARIANTS['B 50/45/40/35/30 (voll)'][:3]]
    print(f"\n  ln-Verhaeltnis A/B: {np.log(a[1] / a[0]) / np.log(b[1] / b[0]):.4f}"
          f"  -> gamma muesste in B um diesen Faktor groesser sein,"
          f" um denselben Zerfall abzubilden")

    # ------------------------------------------- (3) Fortschreibungsquoten
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
    s = s.join(m.rename(columns={"min": "m_start", "max": "m_end"}), on="Matchup")

    print("\n" + "=" * 80)
    print("(3) FORTSCHREIBUNGSQUOTE JE STUETZSTELLE")
    print("=" * 80)
    print("  Anteil der Serien, deren Rasterzelle NACH dem letzten echten "
          "Preis liegt\n")
    rows = []
    for wname, (t0, t1) in (("V1 matchweit", (s["m_start"], s["m_end"])),
                            ("V2 serieneigen", (s["own_start"], s["own_end"]))):
        win = (t1 - t0) / H
        print(f"  {wname}")
        for vname, cols in VARIANTS.items():
            sh = []
            for c in cols:
                tk = t0 + pd.to_timedelta((c / (N_PER - 1)) * win, unit="h")
                sh.append((tk > s["own_end"]).mean() * 100)
            print(f"    {vname:<30s} " + "  ".join(
                f"{c}: {v:5.2f} %" for c, v in zip(cols, sh, strict=True)))
            rows.append({"Fenster": wname, "Variante": vname,
                         **{f"OddsMvt{c}": v for c, v in
                            zip(cols, sh, strict=True)}})
        print()
    pd.DataFrame(rows).to_csv(f"{OUT}/support_shift_ffill.csv", index=False)

    # -------------------------------------------------------- (4) gamma
    print("=" * 80)
    print("(4) GAMMA: BEIDE VARIANTEN, BEIDE FENSTER")
    print("=" * 80)
    frames = {
        "V1 matchweit": pd.read_hdf(
            "revision/snapshots/C_normalized/wide_imputed.h5", key="wide"),
        "V2 serieneigen": pd.read_parquet(
            "revision/snapshots/eq_window_scope/wide_series_own.parquet")}
    res = {}
    for wname, fr in frames.items():
        for vname, cols in VARIANTS.items():
            tau = [c + 1 for c in cols[:3]]
            res[(wname, vname)] = run(fr, cols, tau, f"{wname} | {vname}")
    out = pd.DataFrame({f"{w} | {v[:1]}": r["gamma"] for (w, v), r in res.items()})
    out.to_csv(f"{OUT}/support_shift_gamma.csv")
    print("\n  je Bookmaker:")
    print("    " + out.round(6).to_string().replace("\n", "\n    "))
    print("\n  Rangkorrelationen (Spearman):")
    cs = list(out.columns)
    for i in range(len(cs)):
        for j in range(i + 1, len(cs)):
            print(f"    {cs[i]:<22s} vs {cs[j]:<22s} "
                  f"{out[cs[i]].corr(out[cs[j]], method='spearman'):.4f}")
    print(f"\ngeschrieben: {OUT}/support_shift_gamma.csv, "
          f"{OUT}/support_shift_ffill.csv")
    print("FERTIG", flush=True)
