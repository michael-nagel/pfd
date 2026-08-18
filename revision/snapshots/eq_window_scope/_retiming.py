#!/usr/bin/env python3
"""Wie stark verschieben sich die GMM-Stuetzstellen in absoluter Zeit?

Nutzt den bereits gerechneten window_scope_per_series.csv. Stuetzstelle k
liegt matchweit bei m_start + k/50 * m_win, serieneigen bei
own_start + k/50 * own_win. Beide Achsen sind linear in der Zeit, weil das
1-min-Raster gleichabstaendig ist.
"""

import numpy as np
import pandas as pd

OUT = "revision/snapshots/eq_window_scope"
d = pd.read_csv(f"{OUT}/window_scope_per_series.csv")
print(f"Serien: {len(d):,d}")

# Stuetzstellen relativ zum Matchup-Start, in Stunden
for k in (46, 41, 36, 26, 0):
    pos = k / 50
    t_match = pos * d["m_win_h"]
    t_own = d["delay_h"] + pos * d["own_win_h"]
    shift = t_own - t_match
    # Abstand zum Fensterende (Kickoff-nah) ist die inhaltlich relevante Groesse
    end_match = d["m_win_h"] - t_match
    end_own = d["m_win_h"] - t_own
    print(f"\nOddsMvt{k}  ({pos * 100:.0f} % des jeweiligen Fensters)")
    print(f"  Verschiebung (serieneigen - matchweit), Stunden:")
    print(f"    Median {shift.median():+.2f}   Mittel {shift.mean():+.2f}   "
          f"p90 {shift.quantile(.9):+.2f}   p99 {shift.quantile(.99):+.2f}")
    print(f"  Abstand zum Matchup-Ende (Stunden vor Fensterschluss):")
    print(f"    matchweit   Median {end_match.median():.2f}")
    print(f"    serieneigen Median {end_own.median():.2f}")

print("\n" + "=" * 70)
print("KORRELATION DER VERSCHIEBUNG MIT DER VERSPAETUNG")
print("=" * 70)
pos = 46 / 50
shift46 = (d["delay_h"] + pos * d["own_win_h"]) - pos * d["m_win_h"]
print(f"  corr(Verschiebung OddsMvt46, Verspaetung) = "
      f"{np.corrcoef(shift46, d['delay_h'])[0, 1]:.4f}")
q = pd.qcut(d["delay_h"].rank(method="first"), 4,
            labels=["Q1 frueh", "Q2", "Q3", "Q4 spaet"])
print("\n  nach Verspaetungsquartil:")
print("    " + pd.DataFrame({
    "Verspaetung_h_Median": d.groupby(q, observed=True)["delay_h"].median(),
    "eig_Fenster_h_Median": d.groupby(q, observed=True)["own_win_h"].median(),
    "Match_Fenster_h_Median": d.groupby(q, observed=True)["m_win_h"].median(),
    "Verschiebung46_h_Median": shift46.groupby(q, observed=True).median(),
    "imputierte_Zellen_Mittel": d.groupby(q, observed=True)["n_imputed"].mean(),
}).round(3).to_string().replace("\n", "\n    "))
