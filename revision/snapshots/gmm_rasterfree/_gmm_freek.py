#!/usr/bin/env python3
"""GMM mit freiem K (Biais). Drei Zugaenge, weil K schwach identifiziert ist.

  A) Profil: K auf einem Gitter FESTGEHALTEN, gamma 1-dimensional geschaetzt.
     Zeigt den gamma-K-Tradeoff und ob J ueber K ueberhaupt variiert.
  B) K frei, zwei Parameter, mehrere Startwerte (die literale Anfrage).
  C) K frei, aber auf das zulaessige Intervall (0, 0.25) reparametrisiert,
     K = 0.25 * logistic(kappa). Eine Bernoulli-Restvarianz kann nicht
     negativ und nicht groesser als 0.25 sein.

Rein diagnostisch, `src/pfd` bleibt unberuehrt.
"""

import sys
import warnings

import numpy as np
import pandas as pd
from statsmodels.sandbox.regression.gmm import GMM

sys.path.insert(0, "src")
from pfd.helpers import fit_gmm_mod  # noqa: E402
from pfd.utils import _create_gmm_data  # noqa: E402

warnings.filterwarnings("ignore")
OUT = "revision/snapshots/gmm_rasterfree"
N_PER, INCR, K_MOMS = 51, 5, 14
TAU = [N_PER - i * INCR + 1 for i in (1, 2, 3)]
R1, R2 = TAU[1] / TAU[0], TAU[2] / TAU[1]
KGRID = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25]
STARTS2 = [(g, k) for g in (0.005, 0.02, 0.05) for k in (0.05, 0.15, 0.24)]
OPT = {"maxiter": 5000, "maxfun": 5000, "xtol": 1e-10, "ftol": 1e-12}


def _moms(y, X, Z, g, K):
    r1, r2 = R1 ** (2 * g), R2 ** (2 * g)
    m1 = (X[:, 0] - y) ** 2 - r1 * (X[:, 1] - y) ** 2 - K * (1 - r1)
    m2 = (X[:, 1] - y) ** 2 - r2 * (X[:, 2] - y) ** 2 - K * (1 - r2)
    cols = []
    for i in range(7):
        cols.extend([m1 * Z[:, i], m2 * Z[:, i]])
    return np.column_stack(cols)


class GmmKfixed(GMM):
    """1 Parameter (gamma); K liegt fest in self.K_fixed."""
    def momcond(self, params):
        return _moms(self.endog, self.exog, self.instrument,
                     float(params[0]), self.K_fixed)


class GmmKfree(GMM):
    """2 Parameter: [gamma, K]."""
    def momcond(self, params):
        return _moms(self.endog, self.exog, self.instrument,
                     float(params[0]), float(params[1]))


class GmmKbounded(GMM):
    """2 Parameter: [gamma, kappa] mit K = 0.25 * logistic(kappa)."""
    def momcond(self, params):
        K = 0.25 / (1.0 + np.exp(-float(params[1])))
        return _moms(self.endog, self.exog, self.instrument,
                     float(params[0]), K)


def _fit(mod, start):
    r = mod.fit(start_params=np.asarray(start, float), maxiter="cue",
                optim_method="nm", optim_args=OPT)
    J, pJ, dfJ = r.jtest()
    return r, J, pJ, dfJ


def profile_K(y, X, Z, label, verbose=True):
    rows = []
    for K in KGRID:
        m = GmmKfixed(endog=y, exog=X, instrument=Z, k_moms=K_MOMS, k_params=1)
        m.K_fixed = K
        try:
            r, J, pJ, dfJ = _fit(m, [0.005])
            rows.append({"K_fest": K, "gamma": r.params[0], "se": r.bse[0],
                         "J": J, "pJ": pJ, "df": dfJ})
        except Exception as e:
            rows.append({"K_fest": K, "gamma": np.nan, "se": np.nan,
                         "J": np.nan, "pJ": np.nan, "df": np.nan,
                         "err": type(e).__name__})
    P = pd.DataFrame(rows)
    if verbose:
        print(f"\n  Profil {label}")
        print("    " + P.round(6).to_string(index=False)
              .replace("\n", "\n    "))
    return P


def fit_free(y, X, Z, cls, starts, clusters=None):
    sols = []
    mod = cls(endog=y, exog=X, instrument=Z, k_moms=K_MOMS, k_params=2)
    for st in starts:
        try:
            r, J, pJ, dfJ = _fit(mod, st)
            g = r.params[0]
            K = (0.25 / (1 + np.exp(-r.params[1]))
                 if cls is GmmKbounded else r.params[1])
            sols.append({"start": str(st), "gamma": g, "K": K, "J": J,
                         "pJ": pJ, "se_gamma": r.bse[0]})
        except Exception as e:
            sols.append({"start": str(st), "gamma": np.nan, "K": np.nan,
                         "J": np.inf, "pJ": np.nan, "se_gamma": np.nan,
                         "err": type(e).__name__})
    S = pd.DataFrame(sols)
    ok = S.dropna(subset=["gamma"])
    if ok.empty:
        return None, S
    best = ok.loc[ok["J"].idxmin()]
    out = {"gamma": best["gamma"], "K": best["K"], "J": best["J"],
           "pJ": best["pJ"], "se_gamma": best["se_gamma"],
           "n_ok": len(ok), "n_starts": len(starts),
           "spread_gamma": ok["gamma"].max() - ok["gamma"].min(),
           "spread_K": ok["K"].max() - ok["K"].min()}
    if clusters is not None:
        mm = mod.momcond(np.array([best["gamma"], best["K"]])
                         if cls is not GmmKbounded
                         else np.array([best["gamma"],
                                        np.log(best["K"] / (0.25 - best["K"]))]))
        n = mm.shape[0]
        G = np.zeros((K_MOMS, 2))
        th = np.array([best["gamma"], best["K"]])
        for j in range(2):
            e = np.zeros(2); e[j] = 1e-6
            G[:, j] = (_moms(y, X, Z, *(th + e)).mean(0)
                       - _moms(y, X, Z, *(th - e)).mean(0)) / 2e-6
        codes = pd.factorize(clusters, sort=False)[0]
        sums = np.zeros((codes.max() + 1, K_MOMS))
        np.add.at(sums, codes, mm)
        S_ = sums.T @ sums / n
        V = np.linalg.pinv(G.T @ np.linalg.pinv(S_) @ G) / n
        out["se_gamma_cl"], out["se_K_cl"] = np.sqrt(np.diag(V))
        out["n_cluster"] = int(codes.max() + 1)
    return out, S


if __name__ == "__main__":
    df = pd.read_hdf("revision/snapshots/C_normalized/wide_imputed.h5",
                     key="wide")
    bookies = sorted(df["Bookies"].unique())
    print(f"Frame: {df.shape[0]:,d} Serien, {len(bookies)} Bookmaker")
    print(f"tau = {TAU}, Zerfallsfaktoren {R1:.4f} / {R2:.4f}")
    print(f"K-Koeffizienten (1-r): {1 - R1**0.01:.6f} / {1 - R2**0.01:.6f} "
          f"bei gamma = 0,005\n")

    y, X, Z = _create_gmm_data(df.assign(Bookies="ALL"), N_PER, INCR)
    print("=" * 78)
    print("(A) PROFIL UEBER FESTES K, GEPOOLT")
    print("=" * 78)
    Pp = profile_K(y, X, Z, "gepoolt")
    Pp.to_csv(f"{OUT}/freek_profile_pooled.csv", index=False)

    print("\n" + "=" * 78)
    print("(B)/(C) K FREI, GEPOOLT, CLUSTER-ROBUST AUF MATCHUP")
    print("=" * 78)
    for cls, nm in ((GmmKfree, "unbeschraenkt"), (GmmKbounded, "auf (0;0,25)")):
        st = STARTS2 if cls is GmmKfree else [(g, 0.0) for g in
                                              (0.005, 0.02, 0.05)]
        o, S = fit_free(y, X, Z, cls, st, clusters=df["Matchup"])
        S.to_csv(f"{OUT}/freek_starts_pooled_{nm[:6]}.csv", index=False)
        if o is None:
            print(f"  {nm:<16s} gescheitert")
            continue
        print(f"  {nm:<16s} gamma {o['gamma']:>10.6f}  K {o['K']:>9.5f}  "
              f"J {o['J']:6.2f} (p {o['pJ']:.3f})  konv {o['n_ok']}/"
              f"{o['n_starts']}  Streuung g {o['spread_gamma']:.2e} "
              f"K {o['spread_K']:.2e}")
        print(f"  {'':<16s} SE gamma {o['se_gamma']:.6f} (Modell)  "
              f"{o['se_gamma_cl']:.6f} (Cluster, G = {o['n_cluster']:,d})  "
              f"t_cl {o['gamma'] / o['se_gamma_cl']:.2f}")

    p0 = fit_gmm_mod(df.assign(Bookies="ALL"), N_PER, INCR,
                     [np.array([0.01])], "cue", "ALL")[0]
    print(f"\n  Referenz K = 0:  gamma {p0['gamma']:.6f}  "
          f"SE {p0['std_gamma']:.6f}  J {p0['J_stat']:.2f} "
          f"(p {p0['p_value']:.3f}, df 13)")

    print("\n" + "=" * 78)
    print("JE BOOKMAKER")
    print("=" * 78)
    rows = []
    for b in bookies:
        d = df.loc[df["Bookies"] == b]
        yb, Xb, Zb = _create_gmm_data(d, N_PER, INCR)
        P = profile_K(yb, Xb, Zb, b, verbose=False)
        ob, _ = fit_free(yb, Xb, Zb, GmmKbounded,
                         [(g, 0.0) for g in (0.005, 0.02, 0.05)])
        r0 = fit_gmm_mod(df, N_PER, INCR, [np.array([0.01])], "cue", b)[0]
        rows.append({
            "bookie": b, "n": len(yb), "gamma_K0": r0["gamma"],
            "J_K0": r0["J_stat"], "p_K0": r0["p_value"],
            "gamma_K020": float(P.loc[P["K_fest"] == 0.20, "gamma"].iloc[0]),
            "gamma_Kbound": ob["gamma"] if ob else np.nan,
            "K_bound": ob["K"] if ob else np.nan,
            "J_Kbound": ob["J"] if ob else np.nan,
            "p_Kbound": ob["pJ"] if ob else np.nan,
            "spread_g": ob["spread_gamma"] if ob else np.nan,
            "J_spread_ueber_K": P["J"].max() - P["J"].min()})
        print(f"  {b:<14s} gamma K0 {rows[-1]['gamma_K0']:>9.6f}  "
              f"K=0,20 {rows[-1]['gamma_K020']:>9.6f}  "
              f"K frei {rows[-1]['gamma_Kbound']:>9.6f} "
              f"(K {rows[-1]['K_bound']:.4f})  "
              f"J-Spanne ueber K {rows[-1]['J_spread_ueber_K']:.3f}", flush=True)
    C = pd.DataFrame(rows).set_index("bookie")
    C.to_csv(f"{OUT}/gmm_freek_by_bookie.csv")

    print("\n" + "=" * 78)
    print("AGGREGATE")
    print("=" * 78)
    for c, lab in (("gamma_K0", "K = 0 (Produktion)"),
                   ("gamma_K020", "K = 0,20 fest"),
                   ("gamma_Kbound", "K frei auf (0;0,25)")):
        v = C[c]
        print(f"  {lab:<22s} Mittel {v.mean():.6f}  Median {v.median():.6f}  "
              f"Spanne [{v.min():.6f}, {v.max():.6f}]  neg {int((v < 0).sum())}")
    print(f"\n  K geschaetzt: Mittel {C['K_bound'].mean():.5f}  "
          f"Median {C['K_bound'].median():.5f}  "
          f"Spanne [{C['K_bound'].min():.5f}, {C['K_bound'].max():.5f}]")
    print(f"\n  Spearman gamma_K0 vs gamma_K020:  "
          f"{C['gamma_K0'].corr(C['gamma_K020'], method='spearman'):.4f}")
    print(f"  Spearman gamma_K0 vs gamma_Kbound: "
          f"{C['gamma_K0'].corr(C['gamma_Kbound'], method='spearman'):.4f}")
    print(f"\n  J-Test verworfen (p<0,05): K=0 "
          f"{int((C['p_K0'] < 0.05).sum())}/24   K frei "
          f"{int((C['p_Kbound'] < 0.05).sum())}/24")
    print(f"  J-Spanne ueber das K-Gitter je Bookmaker: Median "
          f"{C['J_spread_ueber_K'].median():.3f}  max "
          f"{C['J_spread_ueber_K'].max():.3f}")
    print(f"  Streuung gamma ueber Startwerte (K frei): Median "
          f"{C['spread_g'].median():.2e}  max {C['spread_g'].max():.2e}")
    print(f"\ngeschrieben: {OUT}/gmm_freek_by_bookie.csv, "
          f"{OUT}/freek_profile_pooled.csv")
    print("FERTIG", flush=True)
