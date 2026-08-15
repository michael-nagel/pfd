#!/usr/bin/env python3
"""Ist gamma nach dem Exponenten-Fix invariant gegen den Stuetzstellenabstand?

Biais et al. (1999), Gl. (13): die Momentbedingung ist invariant gegen eine
Skalierung der Zeitachse. Praktisch heisst das, dass der gewaehlte Abstand
der Stuetzstellen (`incr`) gamma nicht veraendern darf. Mit der alten,
fest an `n_per` gekoppelten Formel galt das nicht (0,0051 / 0,0016 / 0,0293
bei incr = 1 / 2 / 5). Hier wird dieselbe Reihe mit dem korrigierten
Exponenten gerechnet.

Geschaetzt wird wie in der Produktion: je Bookmaker, CUE, Startwert 0,01
(`gmm_estimation.py` verwirft die uebrigen neun Startwerte), danach der
Mittelwert ueber die 24 Bookmaker -- also exakt `avg_gamma_gmm`.

Rein diagnostisch.
"""

import sys
from functools import partial
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from pfd.helpers import fit_gmm_mod  # noqa: E402

OUT = "revision/snapshots/E_gmm_exponent_fix"
WIDE = "revision/snapshots/C_normalized/wide_imputed.h5"
INCRS = [1, 2, 3, 4, 5, 6, 8, 10]
START = [np.array([0.01])]

pd.set_option("display.width", 220)

if __name__ == "__main__":
    d = pd.read_hdf(WIDE, "wide")
    cols = [c for c in d.columns if c.startswith("OddsMvt")
            and c[7:].isdigit()]
    n_per = max(int(c[7:]) for c in cols) + 1
    bookies = sorted(d["Bookies"].unique())
    print(f"{len(d):,d} Serien, n_per = {n_per}, "
          f"{len(bookies)} Bookmaker\n")

    rows = []
    for incr in INCRS:
        # Stuetzstellen und Zerfallsfaktoren wie in _create_gmm_data /
        # _GenMethMom.momcond
        sup = [n_per - i * incr for i in (1, 2, 3, 4, 5)]
        tau = [n_per - i * incr + 1 for i in (1, 2, 3)]
        f1, f2 = tau[1] / tau[0], tau[2] / tau[1]
        with Pool() as pool:
            res = pool.map(
                partial(fit_gmm_mod, d, n_per, incr, START, "cue"), bookies)
        g = np.array([r[0]["gamma"] for r in res])
        se = np.array([r[0]["std_gamma"] for r in res])
        t = g / se
        rows.append({"incr": incr, "stuetzstellen": str(sup),
                     "faktor_1": f1, "faktor_2": f2,
                     "gamma_mittel": g.mean(), "gamma_min": g.min(),
                     "gamma_max": g.max(), "se_mittel": se.mean(),
                     "n_negativ": int((g < 0).sum()),
                     "n_signifikant": int((np.abs(t) > 1.96).sum())})
        print(f"  incr = {incr:>2d}  Stuetzstellen {str(sup):<24s} "
              f"Faktoren {f1:.4f}/{f2:.4f}   gamma {g.mean():.5f}   "
              f"SE {se.mean():.5f}   neg {int((g < 0).sum()):>2d}/24   "
              f"sig {int((np.abs(t) > 1.96).sum()):>2d}/24", flush=True)

    r = pd.DataFrame(rows)
    r.to_csv(f"{OUT}/incr_invariance.csv", index=False)

    print("\ngamma-Mittel ueber die Abstaende:")
    print("  " + r[["incr", "gamma_mittel"]].to_string(
        index=False, float_format=lambda v: f"{v:.5f}").replace(
        "\n", "\n  "))
    sub = r[r["incr"] >= 3]["gamma_mittel"]
    print(f"\n  Spanne ueber alle Abstaende:      "
          f"{r['gamma_mittel'].min():.5f} bis {r['gamma_mittel'].max():.5f}")
    print(f"  Spanne ab incr = 3:               "
          f"{sub.min():.5f} bis {sub.max():.5f}  "
          f"(Variationskoeffizient {sub.std() / sub.mean():.3f})")
    print(f"\ngeschrieben: {OUT}/incr_invariance.csv")
