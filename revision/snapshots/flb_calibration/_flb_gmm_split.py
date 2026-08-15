#!/usr/bin/env python3
"""Lernraten je Favorit/Longshot per GMM statt Bayes (R1-viii, Teil 3).

Die publizierten Favoriten/Longshot-Lernraten stammen aus dem Bayes-Block
(`gamma_fav`, `gamma_udd`) und sind seit der Korrektur des Zerfallsexponenten
veraltet. Der GMM-Pfad traegt die Korrektur bereits. `fit_gmm_mod` schneidet
die Stichprobe ueber die Spalte `Bookies` zu -- es reicht daher, diese Spalte
mit dem Gruppenlabel zu ueberschreiben, um dieselbe Schaetzung je Gruppe zu
fahren. An der Produktions-Pipeline aendert das nichts.

Zusaetzlich: aendert die Normalisierung die Gruppenzuordnung?
`IsFav` wird in `filter_and_shape.py:74-88` aus den ROHEN Quoten beider
Seiten gebildet und kann sich deshalb nicht aendern; der Dezil-Split laeuft
dagegen ueber `OddsMvt0`, und die Normalisierung ist keine monotone
Transformation davon (sie haengt auch von der Marge ab). Beides wird hier
am tatsaechlichen Datenstand geprueft, roh gegen normalisiert.

Rein diagnostisch.
"""

import sys
import time

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "src")
from pfd.helpers import fit_gmm_mod  # noqa: E402

OUT = "revision/snapshots/flb_calibration"
NORM = "revision/snapshots/C_normalized/wide_imputed.h5"
RAW = "revision/snapshots/C1_refactor/wide_imputed.h5"
INCR = 5
STARTS = [np.array([0.01]), np.array([0.05]), np.array([0.2]),
          np.array([0.5])]

pd.set_option("display.width", 220)


def block(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78, flush=True)


def load(path):
    d = pd.read_hdf(path, "wide")
    cols = [c for c in d.columns if c.startswith("OddsMvt")
            and c[7:].isdigit()]
    n_per = max(int(c[7:]) for c in cols) + 1
    return d, n_per


block("0) DATENSTAND")
dn, n_per = load(NORM)
print(f"  normalisiert: {len(dn):,d} Serien, n_per = {n_per}, "
      f"Bookmaker {dn['Bookies'].nunique()}")
print(f"  OddsMvt0  Median {dn['OddsMvt0'].median():.4f}   "
      f"IsFav-Anteil {dn['IsFav'].mean():.4f}")
dr, n_per_r = load(RAW)
print(f"  roh:          {len(dr):,d} Serien, n_per = {n_per_r}")
print(f"  OddsMvt0  Median {dr['OddsMvt0'].median():.4f}   "
      f"IsFav-Anteil {dr['IsFav'].mean():.4f}")

# ------------------------------- 1) Aendert die Normalisierung die Gruppen?
block("1) GRUPPENZUORDNUNG: ROH GEGEN NORMALISIERT")

key = ["Matchup", "Bookies"] if "Matchup" in dn.columns else ["GroupId"]
print(f"  Verknuepfung ueber {key}")
a = dn[key + ["IsFav", "OddsMvt0"]].rename(
    columns={"IsFav": "IsFav_norm", "OddsMvt0": "p0_norm"})
b = dr[key + ["IsFav", "OddsMvt0"]].rename(
    columns={"IsFav": "IsFav_raw", "OddsMvt0": "p0_raw"})
m = a.merge(b, on=key, how="inner")
print(f"  gemeinsame Serien: {len(m):,d} von {len(dn):,d} / {len(dr):,d}")

n_diff = int((m["IsFav_norm"] != m["IsFav_raw"]).sum())
print(f"\n  IsFav: abweichende Zuordnungen {n_diff} von {len(m):,d}")

for c, lab in (("p0_norm", "normalisiert"), ("p0_raw", "roh")):
    m[f"dez_{c}"] = pd.qcut(m[c], 10, labels=False, duplicates="drop")
same = int((m["dez_p0_norm"] == m["dez_p0_raw"]).sum())
rho = stats.spearmanr(m["p0_norm"], m["p0_raw"]).statistic
shift = (m["dez_p0_norm"] - m["dez_p0_raw"]).abs()
print(f"\n  Dezil-Split ueber OddsMvt0:")
print(f"    identisches Dezil : {same:,d} von {len(m):,d} "
      f"({same / len(m) * 100:.2f} %)")
print(f"    Spearman roh/norm : {rho:.6f}")
print(f"    Verschiebung um 1 : {int((shift == 1).sum()):,d}   "
      f"um 2 oder mehr: {int((shift >= 2).sum()):,d}")
print(f"    groesste Verschiebung: {int(shift.max())} Dezile")
print("\n  Dezil-Wechsel je Ausgangsdezil (roh -> normalisiert):")
ct = pd.crosstab(m["dez_p0_raw"] + 1, m["dez_p0_norm"] + 1)
print("    " + ct.to_string().replace("\n", "\n    "))
pd.DataFrame([{"isfav_abweichungen": n_diff, "n": len(m),
               "dezil_identisch": same, "spearman": rho,
               "shift_1": int((shift == 1).sum()),
               "shift_ge2": int((shift >= 2).sum()),
               "shift_max": int(shift.max())}]).to_csv(
    f"{OUT}/split_invariance.csv", index=False)
ct.to_csv(f"{OUT}/split_decile_crosstab.csv")

# --------------------------------------------- 2) GMM je Gruppe
block("2) GMM JE GRUPPE (normalisierte Basis, korrigierter Exponent)")

d = dn.copy()
d["Gruppe"] = np.where(d["IsFav"] == 1, "Favoriten", "Longshots")
split = np.quantile(np.sort(d["OddsMvt0"]), np.linspace(0, 1, 11))
d["Dezil"] = pd.cut(d["OddsMvt0"], bins=split, labels=False,
                    include_lowest=True) + 1

groups = ["Gesamt", "Favoriten", "Longshots"] + [f"D{i}" for i in range(1, 11)]
res = []
for g in groups:
    if g == "Gesamt":
        sub = d
    elif g.startswith("D"):
        sub = d[d["Dezil"] == int(g[1:])]
    else:
        sub = d[d["Gruppe"] == g]
    sub = sub.copy()
    sub["Bookies"] = g
    t0 = time.time()
    out = fit_gmm_mod(sub, n_per, INCR, STARTS, "cue", g)
    secs = time.time() - t0
    gam = [o["gamma"] for o in out]
    best = out[int(np.argmin([abs(x - np.median(gam)) for x in gam]))]
    print(f"  {g:<10s} n = {len(sub):>7,d}   gamma = {best['gamma']:.5f}   "
          f"SE {best['std_gamma']:.5f}   J = {best['J_stat']:6.2f} "
          f"(p = {best['p_value']:.3f})   Spanne ueber Startwerte "
          f"{max(gam) - min(gam):.2e}   {secs:.0f} s")
    res.append({"gruppe": g, "n": len(sub), "gamma": best["gamma"],
                "se_gamma": best["std_gamma"], "j_stat": best["J_stat"],
                "p_value": best["p_value"],
                "spanne_startwerte": max(gam) - min(gam),
                "p0_mittel": sub["OddsMvt0"].mean(), "sekunden": secs})
r = pd.DataFrame(res)
r.to_csv(f"{OUT}/gmm_by_group.csv", index=False)

block("3) FAVORITEN GEGEN LONGSHOTS")
f = r[r["gruppe"] == "Favoriten"].iloc[0]
u = r[r["gruppe"] == "Longshots"].iloc[0]
diff = f["gamma"] - u["gamma"]
se = np.sqrt(f["se_gamma"] ** 2 + u["se_gamma"] ** 2)
print(f"  gamma Favoriten {f['gamma']:.5f} (SE {f['se_gamma']:.5f})")
print(f"  gamma Longshots {u['gamma']:.5f} (SE {u['se_gamma']:.5f})")
print(f"  Differenz {diff:+.5f}   SE (unabhaengig) {se:.5f}   "
      f"t = {diff / se:+.2f}")
print("\n  Dezile (aufsteigender Opening-Preis):")
print("    " + r[r["gruppe"].str.startswith("D")][
    ["gruppe", "n", "p0_mittel", "gamma", "se_gamma"]].to_string(
    index=False, float_format=lambda v: f"{v:.5f}").replace("\n", "\n    "))

print(f"\ngeschrieben nach {OUT}/")
