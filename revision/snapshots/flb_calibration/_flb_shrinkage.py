#!/usr/bin/env python3
"""Schrumpft der Favorite-Longshot-Bias ueber das Fenster? (R1-viii, Teil 2)

`_flb_calibration.py` zeigt die Kalibrierungssteigung fuer Opening und
Closing im Aggregat. Hier wird dieselbe Frage segmentweise gestellt: auf
DENSELBEN Kontrakten, aufgeteilt nach dem Opening-Preis, wird der Bias am
Opening gegen den Bias am Closing getestet. Die Paarung ist damit exakt --
jeder Kontrakt geht in beide Spalten ein -- und der Test laeuft ueber die
Differenz je Kontrakt, cluster-robust auf Matchup.

Zusaetzlich getrennt fuer Favoriten und Longshots, weil Teil 3 (Lernraten)
genau diese Trennung verwendet.

Rein diagnostisch.
"""

import numpy as np
import pandas as pd
from scipy import stats

OUT = "revision/snapshots/flb_calibration"
FRAME = "data/interim/pfd_flb_frame.parquet"

pd.set_option("display.width", 220)


def block(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78, flush=True)


def cr1(x, y, codes):
    xtxi = np.linalg.inv(x.T @ x)
    b = xtxi @ (x.T @ y)
    u = y - x @ b
    n, k = x.shape
    g = codes.max() + 1
    s = np.zeros((g, k))
    np.add.at(s, codes, x * u[:, None])
    cf = (g / (g - 1)) * ((n - 1) / (n - k))
    return b, np.sqrt(np.diag(cf * (xtxi @ (s.T @ s) @ xtxi)))


def mean_cr(v, codes):
    """Mittelwert mit cluster-robustem SE."""
    b, se = cr1(np.ones((len(v), 1)), np.asarray(v, float), codes)
    return b[0], se[0]


d = pd.read_parquet(FRAME).reset_index(drop=True)
print(f"{len(d):,d} Kontrakte, {d['Matchup'].nunique():,d} Matchups")

d["dez"] = pd.qcut(d["OpnOdds"], 10, labels=False, duplicates="drop")
d["bias_opn"] = d["Match"] - d["OpnOdds"]
d["bias_cls"] = d["Match"] - d["ClsOdds"]

# --------------------------------------- 1) Bias je Opening-Dezil
block("1) BIAS AM OPENING GEGEN BIAS AM CLOSING, JE OPENING-DEZIL")
print("  Dieselben Kontrakte in beiden Spalten. |Bias| kleiner heisst "
      "besser kalibriert.\n")
print("  'Bias' ist der Gruppenmittelwert = die Kalibrierungsverzerrung;\n"
      "  'd Bias' testet deren Veraenderung, 'd |Bias|' die Treffgenauigkeit\n"
      "  des einzelnen Kontrakts. Das sind zwei verschiedene Groessen.\n")
print(f"  {'Dezil':>5s} {'n':>7s} {'p_opn':>7s} {'Bias opn':>9s} "
      f"{'Bias cls':>9s} {'d Bias':>9s} {'t':>6s} {'d |Bias|':>9s} {'t':>6s}")
rows = []
for k in range(10):
    m = d["dez"] == k
    s = d[m]
    cc = pd.factorize(s["Matchup"], sort=False)[0]
    bo, seo = mean_cr(s["bias_opn"], cc)
    bc, sec = mean_cr(s["bias_cls"], cc)
    # Veraendert sich die Kalibrierungsverzerrung der Gruppe?
    bg, seg = mean_cr(s["bias_cls"] - s["bias_opn"], cc)
    # Wird der einzelne Kontrakt treffsicherer?
    bd, sed = mean_cr(s["bias_cls"].abs() - s["bias_opn"].abs(), cc)
    print(f"  {k + 1:>5d} {int(m.sum()):>7,d} {s['OpnOdds'].mean():>7.4f} "
          f"{bo:>+9.4f} {bc:>+9.4f} {bg:>+9.4f} {bg / seg:>6.2f} "
          f"{bd:>+9.4f} {bd / sed:>6.2f}")
    rows.append({"dezil": k + 1, "n": int(m.sum()),
                 "p_opening": s["OpnOdds"].mean(), "bias_opening": bo,
                 "se_bias_opening": seo, "bias_closing": bc,
                 "se_bias_closing": sec, "delta_bias": bg,
                 "se_delta_bias": seg, "t_delta_bias": bg / seg,
                 "delta_abs_bias": bd, "se_delta": sed, "t_delta": bd / sed})
pd.DataFrame(rows).to_csv(f"{OUT}/shrinkage_by_decile.csv", index=False)

# ------------------------------------ 2) Steigung je Gruppe
block("2) KALIBRIERUNGSSTEIGUNG JE GRUPPE, OPENING GEGEN CLOSING")
print("  Gestapelt mit Interaktion; die Differenz bekommt einen SE, der die\n"
      "  Paarung der beiden Preise desselben Kontrakts traegt.\n")
res = []
for lab, sub in (("alle", d), ("Favoriten", d[d["IsFav"] == 1]),
                 ("Longshots", d[d["IsFav"] == 0])):
    st = pd.concat([
        sub[["Matchup", "Match"]].assign(p=sub["OpnOdds"], cl=0.0),
        sub[["Matchup", "Match"]].assign(p=sub["ClsOdds"], cl=1.0),
    ], ignore_index=True)
    x = np.column_stack([np.ones(len(st)), st["p"], st["cl"],
                         st["p"] * st["cl"]])
    cc = pd.factorize(st["Matchup"], sort=False)[0]
    b, se = cr1(x, st["Match"].to_numpy(float), cc)
    t = b[3] / se[3]
    p = 2 * (1 - stats.norm.cdf(abs(t)))
    print(f"  {lab:<10s} n = {len(sub):>7,d}   lambda_opn = {b[1]:.4f}   "
          f"lambda_cls = {b[1] + b[3]:.4f}   Differenz {b[3]:+.4f} "
          f"(SE {se[3]:.4f}, t = {t:+.2f}, p = {p:.3f})")
    res.append({"gruppe": lab, "n": len(sub), "lambda_opening": b[1],
                "se_lambda_opening": se[1], "lambda_closing": b[1] + b[3],
                "differenz": b[3], "se_differenz": se[3], "t": t, "p": p})
pd.DataFrame(res).to_csv(f"{OUT}/shrinkage_by_group.csv", index=False)

# ------------------------------------ 3) Gesamtmass: mittlerer |Bias|
block("3) MITTLERER ABSOLUTER BIAS, OPENING GEGEN CLOSING")
cc = pd.factorize(d["Matchup"], sort=False)[0]
bo, seo = mean_cr(d["bias_opn"].abs(), cc)
bc, sec = mean_cr(d["bias_cls"].abs(), cc)
bd, sed = mean_cr(d["bias_cls"].abs() - d["bias_opn"].abs(), cc)
print(f"  |Bias| Opening {bo:.5f} (SE {seo:.5f})")
print(f"  |Bias| Closing {bc:.5f} (SE {sec:.5f})")
print(f"  Differenz      {bd:+.5f} (SE {sed:.5f})   t = {bd / sed:+.2f}")
print("\n  Zum Vergleich, der Brier-Score derselben Kontrakte:")
for lab, c in (("Opening", "OpnOdds"), ("Closing", "ClsOdds")):
    br = ((d["Match"] - d[c]) ** 2)
    b1, s1 = mean_cr(br, cc)
    print(f"    {lab}: {b1:.5f} (SE {s1:.5f})")
bb, sbb = mean_cr((d["Match"] - d["ClsOdds"]) ** 2
                  - (d["Match"] - d["OpnOdds"]) ** 2, cc)
print(f"    Differenz: {bb:+.5f} (SE {sbb:.5f})   t = {bb / sbb:+.2f}")

print(f"\ngeschrieben nach {OUT}/")
