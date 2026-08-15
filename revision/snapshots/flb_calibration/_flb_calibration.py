#!/usr/bin/env python3
"""Favorite-Longshot-Bias direkt in Opening- und Closing-Preisen (R1-viii).

Referee 1, Kommentar 8: die Favoriten/Longshot-Befunde des Papers stuetzen
sich bisher nur auf die Lernraten. Gefordert ist der direkte Nachweis, ob
Opening- und Closing-Preise selbst einen Favorite-Longshot-Bias zeigen und
ob er ueber das Wettfenster schrumpft.

Kalibrierungsregression auf Kontraktebene:

    Match = a + lambda * p + (Kovariaten) + u,   p = OpnOdds bzw. ClsOdds

Effizienz heisst a = 0 und lambda = 1. lambda > 1 bedeutet Unterdispersion:
Longshots gewinnen seltener als ihr Preis behauptet, Favoriten haeufiger --
genau der Favorite-Longshot-Bias.

Der Vergleich Opening gegen Closing laeuft zusaetzlich als EINE gestapelte
Regression mit Interaktion, damit die Differenz der Steigungen einen
Standardfehler bekommt, der die Paarung der beiden Preise desselben
Kontrakts beruecksichtigt.

Inferenz durchgehend CR1 auf Matchup, wie bei Eq. 3 (R1-ii).

Rein diagnostisch, kein Eingriff in die Produktions-Pipeline.
"""

import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
from omegaconf import OmegaConf
from scipy import stats

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

OUT = "revision/snapshots/flb_calibration"
FRAME = "data/interim/pfd_flb_frame.parquet"
COMPETS = ["Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
           "Compet_WTA"]

pd.set_option("display.width", 220)


def block(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78, flush=True)


def build():
    """df_oc wie in `bookmaker_accuracy.py`: eine Zeile je GroupId."""
    cfg = OmegaConf.create({"estimation": {
        "spec": "BmHome", "normalize": True, "compets": None,
        "bm_quantile": 0.25, "ts_dur": [12, 72], "period": None,
        "resample_freq": "1min", "pctl": 2}})
    raw = pd.read_hdf("data/processed/shaped_data.h5", "df")
    for c in ("Date", "Update"):
        raw[c] = pd.to_datetime(raw[c])
    df, *_ = filter_and_shape_data(raw.copy(), cfg)
    d = df.groupby("GroupId", as_index=False).first()
    d["DltOpnCls"] = d["ClsOdds"] - d["OpnOdds"]
    d["RtrnOpnCls"] = d["ClsOdds"] / d["OpnOdds"] - 1
    keep = ["GroupId", "Matchup", "Bookies", "Match", "IsFav", "OpnOdds",
            "ClsOdds", "DltOpnCls", "RtrnOpnCls", "TsDur"] + COMPETS
    d = d[keep].reset_index(drop=True)
    d.to_parquet(FRAME)
    return d


def cr1(X, y, codes):
    """OLS mit CR1-Sandwich; gibt beta, SE iid und SE Cluster zurueck."""
    XtXi = np.linalg.inv(X.T @ X)
    b = XtXi @ (X.T @ y)
    u = y - X @ b
    n, k = X.shape
    se_iid = np.sqrt(np.diag((u @ u) / (n - k) * XtXi))
    g = codes.max() + 1
    s = np.zeros((g, k))
    np.add.at(s, codes, X * u[:, None])
    cf = (g / (g - 1)) * ((n - 1) / (n - k))
    se_cl = np.sqrt(np.diag(cf * (XtXi @ (s.T @ s) @ XtXi)))
    return b, se_iid, se_cl, g


def test(b, se, h0):
    t = (b - h0) / se
    return t, 2 * (1 - stats.norm.cdf(abs(t)))


try:
    d_all = pd.read_parquet(FRAME)
    print(f"Frame aus Cache: {len(d_all):,d} Kontrakte")
except (FileNotFoundError, OSError):
    d_all = build()
    print(f"Frame neu gebaut: {len(d_all):,d} Kontrakte")

d = d_all.reset_index(drop=True)
print(f"  Matchups {d['Matchup'].nunique():,d}   "
      f"Bookmaker {d['Bookies'].nunique()}   "
      f"Favoriten {int(d['IsFav'].sum()):,d}")
print(f"  OpnOdds  Mittel {d['OpnOdds'].mean():.4f}  Spanne "
      f"{d['OpnOdds'].min():.4f}-{d['OpnOdds'].max():.4f}")
print(f"  ClsOdds  Mittel {d['ClsOdds'].mean():.4f}  Spanne "
      f"{d['ClsOdds'].min():.4f}-{d['ClsOdds'].max():.4f}")
print(f"  Match    Mittel {d['Match'].mean():.4f}")

y = d["Match"].to_numpy(float)
codes = pd.factorize(d["Matchup"], sort=False)[0]

# ----------------------------------------- 1) Kalibrierung je Preis
block("1) KALIBRIERUNG: Match ~ p, EINZELN FUER OPENING UND CLOSING")

specs = [
    ("A  Opening, roh", "OpnOdds", []),
    ("B  Closing, roh", "ClsOdds", []),
    ("C  Opening + Kovariaten", "OpnOdds", ["TsDur"] + COMPETS),
    ("D  Closing + Kovariaten", "ClsOdds", ["TsDur"] + COMPETS),
    ("E  Opening + DltOpnCls + Kov. (= Eq. 3 R2-C1)", "OpnOdds",
     ["DltOpnCls", "TsDur"] + COMPETS),
]

rows = []
print(f"\n  {'Spezifikation':<46s} {'a':>9s} {'lambda':>8s} "
      f"{'SE cl.':>8s} {'t vs 1':>8s} {'p':>9s}")
for lab, price, extra in specs:
    cols = [price] + extra
    x = np.column_stack([np.ones(len(d))]
                        + [d[c].to_numpy(float) for c in cols])
    b, se_iid, se_cl, g = cr1(x, y, codes)
    t1, p1 = test(b[1], se_cl[1], 1.0)
    t0, p0 = test(b[0], se_cl[0], 0.0)
    print(f"  {lab:<46s} {b[0]:>9.5f} {b[1]:>8.4f} {se_cl[1]:>8.5f} "
          f"{t1:>8.2f} {p1:>9.2e}")
    rows.append({"spec": lab, "preis": price, "kovariaten": len(extra),
                 "intercept": b[0], "se_intercept_cluster": se_cl[0],
                 "t_intercept_vs0": t0, "p_intercept_vs0": p0,
                 "lambda": b[1], "se_lambda_iid": se_iid[1],
                 "se_lambda_cluster": se_cl[1], "faktor": se_cl[1] / se_iid[1],
                 "t_lambda_vs1": t1, "p_lambda_vs1": p1, "n": len(d),
                 "n_cluster": g})
pd.DataFrame(rows).to_csv(f"{OUT}/calibration_by_price.csv", index=False)

# --------------------------------- 2) Gestapelt: schrumpft der Bias?
block("2) GESTAPELT: Match ~ (1 + p) * Closing, DIFFERENZ MIT SE")

st = pd.concat([
    d[["Matchup", "Match"]].assign(p=d["OpnOdds"], close=0.0),
    d[["Matchup", "Match"]].assign(p=d["ClsOdds"], close=1.0),
], ignore_index=True)
xs = np.column_stack([np.ones(len(st)), st["p"], st["close"],
                      st["p"] * st["close"]])
ys = st["Match"].to_numpy(float)
cs = pd.factorize(st["Matchup"], sort=False)[0]
b, se_iid, se_cl, g = cr1(xs, ys, cs)
nm = ["(Intercept)", "p", "close", "p:close"]
print(f"  N = {len(st):,d} (je Kontrakt zwei Zeilen), G = {g:,d} Matchups\n")
for i, n_ in enumerate(nm):
    print(f"  {n_:<14s} {b[i]:>10.5f}   SE cl. {se_cl[i]:.5f}   "
          f"t = {b[i] / se_cl[i]:>7.2f}")
t_int, p_int = test(b[3], se_cl[3], 0.0)
print(f"\n  lambda(Opening) = {b[1]:.4f}")
print(f"  lambda(Closing) = {b[1] + b[3]:.4f}")
print(f"  Differenz       = {b[3]:+.4f}   SE {se_cl[3]:.5f}   "
      f"t = {t_int:+.2f}   p = {p_int:.3g}")
pd.DataFrame([{"term": n_, "coef": b[i], "se_iid": se_iid[i],
               "se_cluster": se_cl[i]} for i, n_ in enumerate(nm)]
             + [{"term": "lambda_opening", "coef": b[1],
                 "se_cluster": se_cl[1]},
                {"term": "lambda_closing", "coef": b[1] + b[3],
                 "se_cluster": np.nan},
                {"term": "differenz", "coef": b[3], "se_cluster": se_cl[3],
                 "t": t_int, "p": p_int}]).to_csv(
    f"{OUT}/calibration_stacked.csv", index=False)

# ------------------------------------------------ 3) Logit-Kalibrierung
block("3) LOGIT-KALIBRIERUNG (Robustheit gegen die Linearitaetsannahme)")
lg = []
for lab, price in (("Opening", "OpnOdds"), ("Closing", "ClsOdds")):
    p = d[price].to_numpy(float)
    x = sm.add_constant(np.log(p / (1 - p)))
    m = sm.Logit(y, x).fit(disp=0, cov_type="cluster",
                           cov_kwds={"groups": codes})
    t1, p1 = test(m.params[1], m.bse[1], 1.0)
    t0, p0 = test(m.params[0], m.bse[0], 0.0)
    print(f"  {lab}: Steigung {m.params[1]:.4f} (SE {m.bse[1]:.4f})  "
          f"gegen 1: t = {t1:+.2f}, p = {p1:.2e}")
    print(f"  {'':7s} Intercept {m.params[0]:+.5f} (SE {m.bse[0]:.5f})  "
          f"gegen 0: t = {t0:+.2f}, p = {p0:.3g}")
    lg.append({"preis": lab, "slope": m.params[1], "se_slope": m.bse[1],
               "t_slope_vs1": t1, "p_slope_vs1": p1,
               "intercept": m.params[0], "se_intercept": m.bse[0],
               "t_intercept_vs0": t0, "p_intercept_vs0": p0})
pd.DataFrame(lg).to_csv(f"{OUT}/logit_calibration.csv", index=False)

# --------------------------------- 4) Deskriptiv: Bias je Preisdezil
block("4) DESKRIPTIV: MITTLERER BIAS JE PREISDEZIL")
print("  Bias = Gewinnrate minus mittlerer Preis. Positiv heisst "
      "unterbewertet.\n")
des = []
for lab, price in (("Opening", "OpnOdds"), ("Closing", "ClsOdds")):
    q = pd.qcut(d[price], 10, labels=False, duplicates="drop")
    print(f"  {lab}")
    print(f"    {'Dezil':>5s} {'n':>8s} {'Preis':>8s} {'Gewinnrate':>11s} "
          f"{'Bias':>9s} {'SE cl.':>8s} {'t':>7s}")
    for k in sorted(q.unique()):
        m = q == k
        diff = (d.loc[m, "Match"] - d.loc[m, price]).to_numpy(float)
        cc = pd.factorize(d.loc[m, "Matchup"], sort=False)[0]
        b1, _, se1, g1 = cr1(np.ones((m.sum(), 1)), diff, cc)
        print(f"    {k + 1:>5d} {m.sum():>8,d} {d.loc[m, price].mean():>8.4f} "
              f"{d.loc[m, 'Match'].mean():>11.4f} {b1[0]:>+9.4f} "
              f"{se1[0]:>8.4f} {b1[0] / se1[0]:>7.2f}")
        des.append({"preis": lab, "dezil": k + 1, "n": int(m.sum()),
                    "preis_mittel": d.loc[m, price].mean(),
                    "gewinnrate": d.loc[m, "Match"].mean(),
                    "bias": b1[0], "se_cluster": se1[0],
                    "t": b1[0] / se1[0], "n_cluster": g1})
    print()
pd.DataFrame(des).to_csv(f"{OUT}/bias_by_decile.csv", index=False)

# ------------------------------------------- 5) Kontrolle: Produktionsfilter
block("5) KONTROLLE: DERSELBE BEFUND AUF DER GEFILTERTEN STICHPROBE")
f = d[d["RtrnOpnCls"].abs() > 0].reset_index(drop=True)
cf_ = pd.factorize(f["Matchup"], sort=False)[0]
yf = f["Match"].to_numpy(float)
print(f"  |RtrnOpnCls| > 0: {len(f):,d} von {len(d):,d} Kontrakten\n")
ctrl = []
for lab, price in (("Opening", "OpnOdds"), ("Closing", "ClsOdds")):
    x = np.column_stack([np.ones(len(f)), f[price].to_numpy(float)])
    b, _, se_cl, _ = cr1(x, yf, cf_)
    t1, p1 = test(b[1], se_cl[1], 1.0)
    print(f"  {lab}: lambda = {b[1]:.4f} (SE {se_cl[1]:.5f})  "
          f"gegen 1: t = {t1:+.2f}, p = {p1:.2e}")
    ctrl.append({"preis": lab, "lambda": b[1], "se_cluster": se_cl[1],
                 "t_vs1": t1, "p_vs1": p1, "n": len(f)})
pd.DataFrame(ctrl).to_csv(f"{OUT}/calibration_filtered.csv", index=False)

print(f"\ngeschrieben nach {OUT}/")
