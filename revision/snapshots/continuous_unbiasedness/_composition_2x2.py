#!/usr/bin/env python3
"""Imputation vs. composition: the full 2x2 of the beta_1 level.

Two binary axes, four cells:

                            | alle Serien | nur vollständig beobachtete
  Baseline / imputiert      |      A      |      B   <- diese Datei
  kontinuierlich / echt     |      C      |      D

  A  Perzentil-Methode auf dem imputierten Wide-Frame (= C_normalized)
  B  dieselbe Methode, auf die 24.568 vollständig beobachteten Serien
     restringiert  -- die bislang fehlende Zelle
  C  varying-coefficient-GAM auf echten Beobachtungen (beta1_delay_full.csv)
  D  dasselbe GAM, nur vollständig beobachtete (beta1_fully_observed.csv)

Kompositionseffekt   = A-B (Baseline-Zeile)      und C-D (kontinuierliche Zeile)
Methoden-/Imput.-eff = A-C (alle Serien)         und B-D (vollständig beob.)

Zelle B nutzt den Produktionsschätzer wörtlich: dieselbe Restriktion
(NumOddsMvt<20), dieselbe Differenzierung gegen OddsMvt0, dasselbe
Endog = Match - OddsMvt0 und 50 x fit_mixed_lm auf demselben imputierten
Wide-Frame -- es unterscheidet sich ausschließlich die Zeilenmenge.

Rein diagnostisch, kein Eingriff in die Produktions-Pipeline.
"""

import sys
import warnings
from collections import defaultdict
from functools import partial
from multiprocessing import Pool

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import norm

sys.path.insert(0, "src")
from pfd.utils import fit_mixed_lm  # noqa: E402

OUT = "revision/snapshots/continuous_unbiasedness"
ED = f"{OUT}/entry_delay"
BASE = "revision/snapshots/C_normalized"
COLS = [f"OddsMvt{i}" for i in range(51)]
PCTL = 2
# gemeinsamer Träger: die Baseline-Perzentile, die im GAM-Gitter (1..99) liegen
COMMON = np.arange(2, 99, 2, dtype=float)
FE = ("Endog ~ 1 + Exog + TsDur + Compet_Challenger_Men + Compet_ITF_Men + "
      "Compet_Misc + Compet_WTA")

pd.set_option("display.width", 220)


def prepare(df):
    """Produktionsvorbereitung der Unbiasedness-Regressionen."""
    d = df.loc[df["NumOddsMvt"] < 20, :].copy()
    d[COLS[1:]] = d[COLS[1:]].subtract(d["OddsMvt0"], axis=0)
    d["Endog"] = d["Match"] - d["OddsMvt0"]
    return d


def run(df, label):
    """50 x fit_mixed_lm wie estimate_unbiasedness_regressions."""
    d = prepare(df)
    with Pool() as pool:
        res = pool.map(partial(fit_mixed_lm, d), COLS[1:])

    o = defaultdict(list)
    for e in res:
        for k in ("beta_1", "std_beta_1", "beta_0", "std_beta_0", "rmse"):
            o[k].append(e[k])
    o = pd.DataFrame(o)
    o.insert(0, "pctl", (1 + o.index) * PCTL)

    sig = ((o["beta_1"] + norm.ppf(0.975) * o["std_beta_1"] > 1)
           & (o["beta_1"] - norm.ppf(0.975) * o["std_beta_1"] < 1))
    print(f"  {label:<34s} Serien={len(d):>7,d}  mean beta_1="
          f"{o['beta_1'].mean():.4f}  Rand {o['beta_1'].iloc[0]:.3f} -> "
          f"{o['beta_1'].iloc[-1]:.3f}  n_signif={int(sig.sum())}", flush=True)
    return o


def on_common(pctl, beta):
    return np.interp(COMMON, np.asarray(pctl, float), np.asarray(beta, float))


# ------------------------------------------------------------------- Daten
w = pd.read_hdf(f"{BASE}/wide_imputed.h5").reset_index(drop=True)

# Kandidaten aus dem Fehlmuster VOR der Imputation ableiten -- identisch zum
# Masking-Test (Nachtrag 2), aber ohne Zwischen-Cache.
r = pd.read_hdf("data/interim/data_resampled.h5")
r["t"] = r.groupby("GroupId").cumcount()
pre = r.pivot(index="GroupId", columns="t", values="OddsMvt")
pre.columns = COLS
pre = pre.join(r.groupby("GroupId").agg(Matchup=("Matchup", "first"),
                                        Bookies=("Bookies", "first")))
meta = w.drop(columns=COLS)
p = meta.merge(pre.reset_index().drop(columns="GroupId"),
               on=["Matchup", "Bookies"], how="inner")
assert len(p) == len(w), f"join {len(p)} != {len(w)}"

cand = (~p[COLS].isna().any(axis=1)) & (p["NumOddsMvt"] < 20)
print(f"wide_imputed: {len(w):,d} Serien; NumOddsMvt<20: "
      f"{(w['NumOddsMvt'] < 20).sum():,d}")
print(f"vollständig beobachtet (kein NaN vor der Imputation): "
      f"{int(cand.sum()):,d}")
print(f"Kontrolle NaN-Anteil vor Imputation: alle "
      f"{p[COLS].isna().values.mean() * 100:.2f}%, nur diese "
      f"{p.loc[cand, COLS].isna().values.mean() * 100:.2f}%")

# p muss zeilengleich zu w sein, damit die Maske positionsweise passt
assert p[["Matchup", "Bookies"]].equals(w[["Matchup", "Bookies"]]), \
    "Zeilenreihenfolge von p und w weicht ab"
hit = cand.to_numpy()

# --------------------------------------------------------------- Schätzung
print("\nBaseline-Perzentil-Methode (Produktionsschätzer):")
A = run(w, "A  alle Serien (Reproduktion)")
B = run(w[hit], "B  nur vollständig beobachtete")

base = pd.read_csv(f"{BASE}/beta1_curve.csv")
dev = np.abs(A["beta_1"].to_numpy() - base["beta_1"].to_numpy()).max()
print(f"\nReproduktionskontrolle A vs. C_normalized/beta1_curve.csv: "
      f"max |dbeta_1| = {dev:.3e}")
assert dev < 1e-10, "Zelle A reproduziert die Baseline nicht"

B.to_csv(f"{OUT}/beta1_baseline_fully_observed.csv", index=False)

# ------------------------------------------------------------------- 2x2
C = pd.read_csv(f"{ED}/beta1_delay_full.csv")
D = pd.read_csv(f"{ED}/beta1_fully_observed.csv")
cells = {"A": (A, "Baseline/imputiert, alle Serien", 174392),
         "B": (B, "Baseline/imputiert, nur vollst. beob.", 24568),
         "C": (C, "kontinuierlich/echt, alle Serien", 175266),
         "D": (D, "kontinuierlich/echt, nur vollst. beob.", 24568)}

rows, cm = [], {}
for k, (v, name, n) in cells.items():
    cm[k] = on_common(v["pctl"], v["beta_1"])
    rows.append({"Zelle": f"{k}  {name}", "n_Serien": n,
                 "n_Gitterpunkte": len(v),
                 "beta_1_mean_nativ": v["beta_1"].mean(),
                 "beta_1_mean_common": cm[k].mean(),
                 "beta_1_min": v["beta_1"].min(),
                 "beta_1_max": v["beta_1"].max(),
                 "beta_1_Anfang": v["beta_1"].iloc[0],
                 "beta_1_Ende": v["beta_1"].iloc[-1],
                 "beta_1_bei_50": float(np.interp(50, v["pctl"], v["beta_1"])),
                 "Anteil_ueber_1": float((cm[k] > 1).mean())})
t = pd.DataFrame(rows)
print("\n2x2 (Mittel auf gemeinsamem Träger: Perzentile 2,4,...,98)\n")
print(t.to_string(index=False, float_format=lambda v: f"{v:,.4f}"))

a, b, c, d = (cm[k].mean() for k in "ABCD")
comp_base, comp_cont = a - b, c - d
meth_all, meth_fo = a - c, b - d
inter = comp_base - comp_cont

print("\n" + "=" * 74)
print("ZERLEGUNG (mittleres beta_1 auf gemeinsamem Träger)")
print("=" * 74)
grid = [("", "alle Serien", "vollst. beob.", "Komposition"),
        ("Baseline/imputiert", f"{a:.3f}", f"{b:.3f}", f"{comp_base:+.3f}"),
        ("kontinuierlich/echt", f"{c:.3f}", f"{d:.3f}", f"{comp_cont:+.3f}"),
        ("Methode/Imputation", f"{meth_all:+.3f}", f"{meth_fo:+.3f}",
         f"{inter:+.3f} (Inter.)")]
print()
for r in grid:
    print(f"  {r[0]:<20s} {r[1]:>12s} {r[2]:>14s} {r[3]:>16s}")
print()
print(f"  Gesamtlücke A - C                  : {meth_all:+.3f}")
print(f"  Methode OHNE Imputation (B - D)    : {meth_fo:+.3f}"
      f"   ({meth_fo / meth_all * 100:5.1f} % der Lücke)")
print(f"  Interaktion (A-C) - (B-D)          : {inter:+.3f}"
      f"   ({inter / meth_all * 100:5.1f} % der Lücke)")
print(f"  Komposition echt (C - D)           : {comp_cont:+.3f}")
print(f"  Komposition imputiert (A - B)      : {comp_base:+.3f}"
      f"   ({comp_base / comp_cont * 100:5.1f} % davon erhalten)")

mt = pd.read_csv(f"{OUT}/masking_beta1_true.csv")
mi = pd.read_csv(f"{OUT}/masking_beta1_imputed.csv")
mtc, mic = (on_common(x["pctl"], x["beta_1"]).mean() for x in (mt, mi))
print(f"\n  Kontext Masking-Test, dieselben 24.568 Serien (within-sample):"
      f"\n    echt {mtc:.3f} -> imputiert {mic:.3f}  ({mic - mtc:+.3f})")

t.to_csv(f"{OUT}/compare_2x2_composition.csv", index=False)
pd.DataFrame({"pctl": COMMON, **{k: cm[k] for k in "ABCD"}}).to_csv(
    f"{OUT}/beta1_2x2_composition_curves.csv", index=False)

# ------------------------------------- Konvergenzzensus / Schätzerrobustheit
# Die restringierte Stichprobe (24 Bookmaker) treibt die RE-Varianz an den
# Rand. Prüfen, ob das Niveau von Zelle B daran hängt.
print("\n" + "=" * 74)
print("KONVERGENZ / SCHÄTZERROBUSTHEIT von Zelle B")
print("=" * 74)
db = prepare(w[hit])
rows = []
for i, col in enumerate(COLS[1:]):
    db["Exog"] = db[col]
    with warnings.catch_warnings(record=True) as wl:
        warnings.simplefilter("always")
        m = smf.mixedlm(FE, data=db, groups="Bookies",
                        re_formula="1 + Exog").fit(reml=False, method="lbfgs")
    msgs = {str(x.message)[:40] for x in wl}
    ols = smf.ols(FE, data=db).fit()
    rows.append({"pctl": (i + 1) * PCTL, "beta_1_re": m.fe_params["Exog"],
                 "se_re": m.bse_fe["Exog"], "beta_1_ols": ols.params["Exog"],
                 "se_ols": ols.bse["Exog"],
                 "singular": any("singular" in x for x in msgs),
                 "boundary": any("boundary" in x for x in msgs)})
cv = pd.DataFrame(rows)
print(f"  Bookmaker in Zelle B      : {db['Bookies'].nunique()}")
print(f"  Fits mit 'RE singular'    : {int(cv['singular'].sum())} von 50")
print(f"  Fits mit 'MLE at boundary': {int(cv['boundary'].sum())} von 50")
print(f"  mean beta_1  mit RE       : {cv['beta_1_re'].mean():.4f}")
print(f"  mean beta_1  OLS ohne RE  : {cv['beta_1_ols'].mean():.4f}")
print(f"  max |RE - OLS|            : "
      f"{(cv['beta_1_re'] - cv['beta_1_ols']).abs().max():.4f}")
print(f"  corr(RE, OLS)             : "
      f"{np.corrcoef(cv['beta_1_re'], cv['beta_1_ols'])[0, 1]:.5f}")
cv.to_csv(f"{OUT}/beta1_baseline_fully_observed_convergence.csv", index=False)
print(f"\ngeschrieben: {OUT}/beta1_baseline_fully_observed.csv, "
      f"compare_2x2_composition.csv, beta1_2x2_composition_curves.csv, "
      f"beta1_baseline_fully_observed_convergence.csv")
