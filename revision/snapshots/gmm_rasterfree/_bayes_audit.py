#!/usr/bin/env python3
"""Vorpruefung des Bayesian-Modells vor dem Lauf. Rein diagnostisch."""
import numpy as np
import pandas as pd
from scipy import stats

OUT = "revision/snapshots/gmm_rasterfree"
KEY = ["Matchup", "Bookies"]

print("=" * 76)
print("(1) PRIORS GEGEN DEN ERWARTETEN POSTERIOR-BEREICH")
print("=" * 76)
g_exp = 0.003474          # erwartetes gamma quer unter V2|B
print(f"  erwartetes gamma (V2|B, GMM):            {g_exp:.6f}")
print(f"  publizierte Kalibrierungsgrundlage:      0.032 (vor Exponenten-Fix)")
print()
hn = stats.halfnorm(scale=1.0)
print("  mean_gamma ~ Truncated(Normal(0, 1), lower=0)  = HalfNormal(sd 1)")
for q in (0.5, 0.9, 0.99):
    print(f"    {q * 100:4.0f}-%-Quantil: {hn.ppf(q):.4f}")
print(f"    P(mean_gamma < {g_exp:.4f}) = {hn.cdf(g_exp) * 100:.3f} %")
print(f"    Dichte bei 0: {hn.pdf(0):.4f}   bei {g_exp:.4f}: "
      f"{hn.pdf(g_exp):.4f}   Verhaeltnis {hn.pdf(g_exp) / hn.pdf(0):.6f}")
print("    -> auf der relevanten Skala praktisch flach, also unkritisch flach,")
print("       aber die Prior-Masse liegt zu >99,7 % oberhalb des Posteriors")
print()
ex = stats.expon(scale=1 / 2.5)
print("  sd_gamma ~ Exponential(lam=2.5), Mittel 0.4")
for q in (0.5, 0.9):
    print(f"    {q * 100:4.0f}-%-Quantil: {ex.ppf(q):.4f}")
print(f"    empirische Streuung zwischen Bookmakern (tau):")
print(f"      V1|A 0.000410   V2|B 0.000000  (I^2 = 3,9 % bzw. 0 %)")
print(f"    P(sd_gamma < 0.001) = {ex.cdf(0.001) * 100:.3f} %")
print("    -> Prior-Mittel ist rund 1000-fach groesser als die tatsaechliche")
print("       Streuung; im hierarchischen Modell zieht das die geschaetzte")
print("       Heterogenitaet nach oben")

print("\n" + "=" * 76)
print("(2) HARTE GRENZE lower=0 AUF gamma -- wie bindend?")
print("=" * 76)
h = pd.read_csv(f"{OUT}/hetero_by_bookie.csv")
for spec in h["spec"].unique():
    s = h[h["spec"] == spec]
    t = s["gamma"] / s["se"]
    print(f"  {spec}")
    print(f"    gamma/SE: Median {t.median():.2f}   min {t.min():.2f}   "
          f"max {t.max():.2f}")
    print(f"    Bookmaker mit gamma < 2 SE ueber null: "
          f"{int((t < 2).sum())} von {len(s)}")
    print(f"    mittlere Prior-Masse unterhalb null (Normal-Approx): "
          f"{stats.norm.cdf(-t).mean() * 100:.1f} %")
print("  -> bei gamma ~ 0.03 lag der Schaetzer ~15 SE ueber null, die")
print("     Truncation war folgenlos. Bei ~0.0035 ist sie es nicht mehr.")

print("\n" + "=" * 76)
print("(3) DEZILGRENZEN AUF OddsMvt0: V1 (86 % imputiert) vs. V2 (echt)")
print("=" * 76)
v1 = pd.read_hdf("revision/snapshots/C_normalized/wide_imputed.h5", key="wide")
v2 = pd.read_parquet("revision/snapshots/eq_window_scope/"
                     "wide_series_own.parquet")
i1, i2 = pd.MultiIndex.from_frame(v1[KEY]), pd.MultiIndex.from_frame(v2[KEY])
common = i1.intersection(i2)
a = v1[i1.isin(common)].set_index(KEY)["OddsMvt0"].sort_index()
b = v2[i2.isin(common)].set_index(KEY)["OddsMvt0"].sort_index()
print(f"  gemeinsame Serien: {len(a):,d}")
qa = np.quantile(np.sort(a.to_numpy()), np.linspace(0, 1, 11))
qb = np.quantile(np.sort(b.to_numpy()), np.linspace(0, 1, 11))
print(f"\n  {'Dezil':>6s} {'V1 Grenze':>11s} {'V2 Grenze':>11s} "
      f"{'Diff':>9s}")
for i, (x, y) in enumerate(zip(qa, qb, strict=True)):
    print(f"  {i:>6d} {x:>11.5f} {y:>11.5f} {y - x:>+9.5f}")
da = np.clip(np.searchsorted(qa[1:-1], a.to_numpy(), side="right"), 0, 9)
db = np.clip(np.searchsorted(qb[1:-1], b.to_numpy(), side="right"), 0, 9)
same = (da == db).mean() * 100
print(f"\n  Serien im selben Dezil: {same:.2f} %   "
      f"Wechsler: {(da != db).sum():,d} ({100 - same:.2f} %)")
print(f"  davon um mehr als ein Dezil: "
      f"{(np.abs(da - db) > 1).sum():,d} "
      f"({np.mean(np.abs(da - db) > 1) * 100:.2f} %)")
print(f"  max. Verschiebung: {np.abs(da - db).max()} Dezile")
print(f"\n  OddsMvt0 selbst: identisch in "
      f"{np.mean(np.abs(a.to_numpy() - b.to_numpy()) < 1e-12) * 100:.2f} % "
      f"der Serien, mean|diff| "
      f"{np.abs(a.to_numpy() - b.to_numpy()).mean():.5f}")
