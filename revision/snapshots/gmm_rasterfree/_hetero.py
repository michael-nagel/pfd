#!/usr/bin/env python3
"""Wie stabil sind die bookmakerspezifischen gamma? Rein diagnostisch.

(1) gamma je Bookmaker mit SE und 95-%-Intervall, sortiert
(2) Heterogenitaetstest: Cochran-Q, I^2, DerSimonian-Laird tau^2
    plus paarweise Kontraste
Verglichen: publizierte Fassung V1|A und Kandidat V2|B.
"""
import sys
import warnings
from functools import partial
from multiprocessing import Pool

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.sandbox.regression.gmm import GMM

sys.path.insert(0, "src")
warnings.filterwarnings("ignore")
OUT = "revision/snapshots/gmm_rasterfree"
N_PER, INCR, K_MOMS = 51, 5, 14
SUP = {"A": [N_PER - i * INCR for i in (1, 2, 3, 4, 5)],
       "B": [N_PER - 1 - i * INCR for i in (0, 1, 2, 3, 4)]}


def build(d, cols):
    y = d["Match"].to_numpy(float)
    ex = [d[f"OddsMvt{c}"].to_numpy(float) for c in cols]
    inst = [np.ones(len(y))]
    for i in (4, 5):
        z = ex[i - 2] - ex[i - 1]
        inst.extend([z, z ** 2])
    ex.append(d["OddsMvt0"].to_numpy(float))
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
        c = []
        for i in range(7):
            c.extend([m1 * Z[:, i], m2 * Z[:, i]])
        return np.column_stack(c)


def one(args):
    d, cols, b = args
    sub = d if b is None else d.loc[d["Bookies"] == b]
    y, X, Z = build(sub, cols)
    m = Gmm(endog=y, exog=X, instrument=Z, k_moms=K_MOMS, k_params=1)
    m.tau = [c + 1 for c in cols[:3]]
    try:
        r = m.fit(start_params=np.array([0.01]), maxiter="cue",
                  optim_method="nm")
        return {"bookie": b or "POOLED", "gamma": r.params[0],
                "se": r.bse[0], "n": len(y)}
    except Exception:
        return {"bookie": b or "POOLED", "gamma": np.nan, "se": np.nan,
                "n": len(y)}


def analyse(d, cols, label):
    bks = sorted(d["Bookies"].unique())
    with Pool(processes=6) as pool:
        res = pool.map(one, [(d, cols, b) for b in bks])
    o = pd.DataFrame(res).set_index("bookie").sort_values("gamma")
    pooled = one((d.assign(Bookies="X"), cols, None))
    o["lo"] = o["gamma"] - 1.96 * o["se"]
    o["hi"] = o["gamma"] + 1.96 * o["se"]

    g, se = o["gamma"].to_numpy(), o["se"].to_numpy()
    w = 1 / se ** 2
    gw = (w * g).sum() / w.sum()
    Q = (w * (g - gw) ** 2).sum()
    dfQ = len(g) - 1
    pQ = 1 - stats.chi2.cdf(Q, dfQ)
    I2 = max(0.0, (Q - dfQ) / Q) * 100
    tau2 = max(0.0, (Q - dfQ) / (w.sum() - (w ** 2).sum() / w.sum()))

    print("\n" + "=" * 78)
    print(f"{label}")
    print("=" * 78)
    print(f"  gepoolt: gamma {pooled['gamma']:.6f}  SE {pooled['se']:.6f}"
          f"   (Mittel je Bookmaker {g.mean():.6f})")
    print(f"\n  {'Bookmaker':<14s} {'gamma':>10s} {'SE':>9s} "
          f"{'95%-Intervall':>22s}  {'n':>6s}  enth. gepoolt?")
    n_excl = 0
    for b, r in o.iterrows():
        inc = r["lo"] <= pooled["gamma"] <= r["hi"]
        n_excl += (not inc)
        print(f"  {b:<14s} {r['gamma']:>10.6f} {r['se']:>9.6f} "
              f"[{r['lo']:>9.6f}, {r['hi']:>9.6f}]  {int(r['n']):>6,d}"
              f"  {'ja' if inc else 'NEIN'}")
    print(f"\n  Intervalle, die den gepoolten Wert NICHT enthalten: "
          f"{n_excl} von {len(o)}")

    # paarweise Kontraste
    sig = 0
    tot = 0
    for i in range(len(g)):
        for j in range(i + 1, len(g)):
            tot += 1
            t = (g[i] - g[j]) / np.sqrt(se[i] ** 2 + se[j] ** 2)
            sig += abs(t) > 1.96
    print(f"  paarweise Kontraste signifikant (|t|>1,96): {sig} von {tot} "
          f"({sig / tot * 100:.1f} %)")
    print(f"\n  Cochran-Q = {Q:.2f}  df = {dfQ}  p = {pQ:.4g}")
    print(f"  I^2 = {I2:.1f} %   tau (zwischen Bookmakern) = "
          f"{np.sqrt(tau2):.6f}")
    print(f"  beobachtete sd der gamma = {g.std(ddof=1):.6f}   "
          f"mittlere SE = {se.mean():.6f}")
    o["spec"] = label
    return o, {"spec": label, "Q": Q, "df": dfQ, "p": pQ, "I2": I2,
               "tau": np.sqrt(tau2), "sd_gamma": g.std(ddof=1),
               "mean_se": se.mean(), "n_excl": n_excl, "pairs_sig": sig,
               "pairs_tot": tot, "gamma_pooled": pooled["gamma"]}


if __name__ == "__main__":
    v1 = pd.read_hdf("revision/snapshots/C_normalized/wide_imputed.h5",
                     key="wide")
    v2 = pd.read_parquet("revision/snapshots/eq_window_scope/"
                         "wide_series_own.parquet")
    tabs, summ = [], []
    for d, cols, lab in ((v1, SUP["A"], "V1|A  (publizierte Fassung)"),
                         (v2, SUP["B"], "V2|B  (Kandidat)")):
        t, s = analyse(d, cols, lab)
        tabs.append(t)
        summ.append(s)
    pd.concat(tabs).to_csv(f"{OUT}/hetero_by_bookie.csv")
    pd.DataFrame(summ).to_csv(f"{OUT}/hetero_summary.csv", index=False)
    print(f"\ngeschrieben: {OUT}/hetero_by_bookie.csv, "
          f"{OUT}/hetero_summary.csv")
