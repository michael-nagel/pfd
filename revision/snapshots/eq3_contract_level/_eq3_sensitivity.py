#!/usr/bin/env python3
"""Zwei Ergänzungen zur Eq.-3-Kontraktebenen-Analyse (R2-C1).

  1) Sensitivität gegenüber dem Produktionsfilter `|RtrnOpnCls| > 0`.
     Die Frage "trägt die Preisbewegung Information" wird sonst auf einer
     Stichprobe beantwortet, die auf bewegte Preise selektiert ist.
  2) Bookmaker-FIXED-Effects statt Random Effects. In S4 waren die
     Bookmaker-REs exakt null (`boundary (singular) fit`); FE mit
     Interaktion prüft, ob eine Heterogenität existiert, die der
     RE-Ansatz nicht sieht.

Rein diagnostisch.
"""

import sys
import tempfile

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "src")

OUT = "revision/snapshots/eq3_contract_level"
FRAME = f"{tempfile.gettempdir()}/pfd_eq3_frame.parquet"
COMPETS = ["Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
           "Compet_WTA"]
BASE = ["OpnOdds", "DltOpnCls", "TsDur"] + COMPETS

pd.set_option("display.width", 220)


def block(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78, flush=True)


def fit(d, X, names):
    """OLS + CR1-Sandwich auf Matchup-Ebene."""
    y = d["Match"].to_numpy(float)
    XtXi = np.linalg.inv(X.T @ X)
    b = XtXi @ (X.T @ y)
    u = y - X @ b
    N, K = X.shape
    s2 = (u @ u) / (N - K)
    se_m = np.sqrt(np.diag(s2 * XtXi))
    codes = pd.factorize(d["Matchup"], sort=False)[0]
    G = codes.max() + 1
    S = np.zeros((G, K))
    np.add.at(S, codes, X * u[:, None])
    cf = (G / (G - 1)) * ((N - 1) / (N - K))
    V = cf * (XtXi @ (S.T @ S) @ XtXi)
    r2 = 1 - (u @ u) / ((y - y.mean()) @ (y - y.mean()))
    return b, se_m, np.sqrt(np.diag(V)), V, r2, G, names


def design(d, cols):
    X = np.column_stack([np.ones(len(d))]
                        + [d[c].to_numpy(float) for c in cols])
    return X, ["(Intercept)"] + cols


d_all = pd.read_parquet(FRAME)
d_flt = d_all[d_all["RtrnOpnCls"].abs() > 0].reset_index(drop=True)

# ------------------------------------------- 1) Filter-Sensitivität
block("1) SENSITIVITÄT GEGENÜBER DEM FILTER |RtrnOpnCls| > 0")
rows = []
for lab, d in (("gefiltert (Produktion)", d_flt),
               ("ungefiltert (alle Kontrakte)", d_all)):
    X, nm = design(d, BASE)
    b, se_m, se_c, _, r2, G, _ = fit(d, X, nm)
    i1, i2 = nm.index("OpnOdds"), nm.index("DltOpnCls")
    zero = int((d["DltOpnCls"] == 0).sum())
    rows.append({"Stichprobe": lab, "n": len(d), "G_matchups": G,
                 "n_ohne_Bewegung": zero, "R2": r2,
                 "eta_0": b[0], "se_eta_0_cl": se_c[0],
                 "eta_1": b[i1], "se_eta_1_m": se_m[i1],
                 "se_eta_1_cl": se_c[i1],
                 "eta_2": b[i2], "se_eta_2_m": se_m[i2],
                 "se_eta_2_cl": se_c[i2]})
    print(f"\n  {lab}:  n = {len(d):,d}  ({zero:,d} ohne Bewegung)  "
          f"G = {G:,d}  R2 = {r2:.5f}")
    print(f"    eta_0 = {b[0]:>9.5f}  (Cluster {se_c[0]:.5f})")
    print(f"    eta_1 = {b[i1]:>9.5f}  (Modell {se_m[i1]:.5f}, "
          f"Cluster {se_c[i1]:.5f})   gegen 1: "
          f"t = {(b[i1] - 1) / se_c[i1]:+.2f}")
    print(f"    eta_2 = {b[i2]:>9.5f}  (Modell {se_m[i2]:.5f}, "
          f"Cluster {se_c[i2]:.5f})   gegen 0: "
          f"t = {b[i2] / se_c[i2]:+.2f}")

s = pd.DataFrame(rows)
s.to_csv(f"{OUT}/filter_sensitivity.csv", index=False)
print(f"\n  Delta eta_1 (ungefiltert - gefiltert): "
      f"{s['eta_1'].iloc[1] - s['eta_1'].iloc[0]:+.5f}")
print(f"  Delta eta_2 (ungefiltert - gefiltert): "
      f"{s['eta_2'].iloc[1] - s['eta_2'].iloc[0]:+.5f}")

# ------------------------------------------ 2) Bookmaker-Fixed-Effects
block("2) BOOKMAKER-FIXED-EFFECTS STATT RANDOM EFFECTS (gefilterte Stichprobe)")
d = d_flt.copy()
bk = sorted(d["Bookies"].unique())
ref = bk[0]
print(f"  {len(bk)} Bookmaker, Referenzkategorie '{ref}'")

dum = {f"B_{b}": (d["Bookies"] == b).astype(float) for b in bk[1:]}
itr = {f"BxD_{b}": dum[f"B_{b}"] * d["DltOpnCls"] for b in bk[1:]}
for k, v in {**dum, **itr}.items():
    d[k] = v
cols = BASE + list(dum) + list(itr)
X, nm = design(d, cols)
b, se_m, se_c, V, r2, G, _ = fit(d, X, nm)

X0, nm0 = design(d, BASE)
_, _, _, _, r2_0, _, _ = fit(d, X0, nm0)
print(f"  R2:  S3 (ohne Bookmaker) {r2_0:.6f}   FE + Interaktion {r2:.6f}"
      f"   Zuwachs {r2 - r2_0:.6f}")


def wald(idx):
    """Cluster-robuster Wald-Test: alle Koeffizienten in idx = 0."""
    bb = b[idx]
    VV = V[np.ix_(idx, idx)]
    w = float(bb @ np.linalg.solve(VV, bb))
    return w, len(idx), 1 - stats.chi2.cdf(w, len(idx))


i_dum = [nm.index(k) for k in dum]
i_itr = [nm.index(k) for k in itr]
for lab, idx in (("Bookmaker-Dummies (Niveau)", i_dum),
                 ("Interaktionen mit DltOpnCls (Steigung)", i_itr),
                 ("beide gemeinsam", i_dum + i_itr)):
    w, q, p = wald(idx)
    print(f"  Wald (cluster-robust) {lab:<40s} chi2({q:>2d}) = {w:>8.2f}"
          f"   p = {p:.4g}")

slopes = pd.DataFrame({
    "bookie": bk,
    "slope": [b[nm.index("DltOpnCls")]] + [b[nm.index("DltOpnCls")]
                                           + b[nm.index(f"BxD_{x}")]
                                           for x in bk[1:]],
    "se_interaktion_cl": [np.nan] + [se_c[nm.index(f"BxD_{x}")]
                                     for x in bk[1:]],
})
slopes["t_vs_ref"] = (slopes["slope"] - slopes["slope"].iloc[0]) / slopes[
    "se_interaktion_cl"]
slopes = slopes.sort_values("slope")
slopes.to_csv(f"{OUT}/bookie_fe_slopes.csv", index=False)
ref_slope = float(slopes.loc[slopes["bookie"] == ref, "slope"].iloc[0])
print(f"\n  Bookmaker-spezifische Steigungen auf DltOpnCls "
      f"(Referenz {ref} = {ref_slope:.4f}):")
print("  " + slopes.to_string(index=False,
                              float_format=lambda v: f"{v:,.4f}")
      .replace("\n", "\n  "))
print(f"\n  Spanne {slopes['slope'].min():.4f} - {slopes['slope'].max():.4f}"
      f"   sd {slopes['slope'].std():.4f}")
sig = int((slopes["t_vs_ref"].abs() > 1.96).sum())
print(f"  einzeln signifikant von der Referenz verschieden: {sig} von "
      f"{len(bk) - 1}")

print(f"\ngeschrieben: {OUT}/filter_sensitivity.csv, bookie_fe_slopes.csv")
