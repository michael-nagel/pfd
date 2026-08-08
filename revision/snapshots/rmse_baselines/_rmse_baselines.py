#!/usr/bin/env python3
"""RMSE-Einordnung: Baselines und Murphy-Zerlegung (R2-M7, Teil 1).

Referee R2-M7: der berichtete RMSE von ~0,45 steht ohne Bezugspunkt im Text.
Ein Leser kann nicht einordnen, ob 0,45 gut oder schlecht ist. Dieses Skript
liefert die drei Bezugspunkte, gegen die sich ein Wahrscheinlichkeitsforecast
messen lassen muss:

  1) die uninformierte Prognose (immer 0,5)  -> Brier 0,25, RMSE 0,5
  2) die Perfekt-Kalibriert-Grenze E[p(1-p)] unter der BEOBACHTETEN
     Preisverteilung -- was ein fehlerfreier Prognostiker bei DIESER
     Match-Ausgeglichenheit noch erreichen koennte
  3) die Murphy-Zerlegung Brier = REL - RES + UNC, die Kalibrierung
     (Reliability) von Trennschaerfe (Resolution) trennt

Zu (2) gilt exakt und ohne jede Binnung, weil y binaer ist:

    (y - p)^2 - p(1-p) = (y - p)(1 - 2p)

Der Abstand des beobachteten Brier-Scores zur Grenze ist also der Mittelwert
von z = (y-p)(1-2p) und damit ein normaler, cluster-robust testbarer
Mittelwert. Unterdisperse Preise (E[y|p] weiter von 0,5 entfernt als p, also
eta_1 > 1 aus R2-C1) erzeugen z < 0: der beobachtete Brier liegt dann UNTER
der Grenze. Das wird hier geprueft, nicht angenommen.

Rein diagnostisch, kein Eingriff in die Produktions-Pipeline.
"""

import sys

import numpy as np
import pandas as pd
from omegaconf import OmegaConf
from scipy import stats

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

OUT = "revision/snapshots/rmse_baselines"
# Cache ausserhalb des Repos; /tmp ueberlebt einen WSL-Neustart nicht.
FRAME = ("/mnt/c/Users/micha/AppData/Local/Temp/claude/"
         "C--Users-micha-OneDrive-Michi-pfd/"
         "faf3f6fb-65b6-4ea7-a5e5-08b35a6557d8/scratchpad/"
         "pfd_rmse_frame.parquet")

pd.set_option("display.width", 220)


def block(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78, flush=True)


def build():
    """Eine Zeile je GroupId, mit Zeitstempeln und Marge fuer Teil 2.

    Quelle ist `df_desc` aus `filter_and_shape_data`: dieselbe Selektion wie
    die Produktions-Cross-Sections, aber noch mit `Date` (Anpfiff), `Update`
    (Zeitstempel der Quote), `Margin` und unstandardisiertem `TsDur`.
    """
    cfg = OmegaConf.create({"estimation": {
        "spec": "BmHome", "normalize": True, "compets": None,
        "bm_quantile": 0.25, "ts_dur": [12, 72], "period": None,
        "resample_freq": "1min", "pctl": 2}})
    raw = pd.read_hdf("data/processed/shaped_data.h5", "df")
    for c in ("Date", "Update"):
        raw[c] = pd.to_datetime(raw[c])
    _, desc, bookies, *_ = filter_and_shape_data(raw.copy(), cfg)
    desc = desc.sort_values(["GroupId", "Update"])

    g = desc.groupby("GroupId", sort=False)
    d = pd.DataFrame({
        "Matchup": g["Matchup"].first(),
        "Bookies": g["Bookies"].first(),
        "Match": g["Match"].first(),
        "OpnOdds": g["OpnOdds"].first(),
        "ClsOdds": g["ClsOdds"].first(),
        "NObs": g.size(),
        "TsDurH": g["TsDur"].first(),
        # Anpfiff minus erster/letzter Zeitstempel, in Stunden VOR Anpfiff
        "OpnHrs": ((g["Date"].first() - g["Update"].first())
                   / np.timedelta64(1, "h")),
        "ClsHrs": ((g["Date"].first() - g["Update"].last())
                   / np.timedelta64(1, "h")),
        "MarginOpn": g["Margin"].first(),
        "MarginCls": g["Margin"].last(),
        "MarginMed": g["Margin"].median(),
    }).reset_index()
    d["RtrnOpnCls"] = d["ClsOdds"] / d["OpnOdds"] - 1
    d.to_parquet(FRAME)
    print(f"Bookmaker der Schaetzstichprobe: {len(bookies)}")
    return d


try:
    d_all = pd.read_parquet(FRAME)
    print(f"Frame aus Cache: {len(d_all):,d} Serien")
except (FileNotFoundError, OSError):
    d_all = build()
    print(f"Frame neu gebaut: {len(d_all):,d} Serien")

# Produktions-`df_oc` (bookmaker_accuracy.py:88) verwirft Serien ohne
# Preisbewegung. Das ist die Basis von Tabelle 3/6/7 und wird hier als
# Hauptstichprobe gefuehrt; die ungefilterte Fassung laeuft als Sensitivitaet
# mit, weil der Filter fuer eine Prognosegueteaussage nicht neutral ist.
d = d_all[d_all["RtrnOpnCls"].abs() > 0].reset_index(drop=True)
print(f"  df_oc (Produktion, |RtrnOpnCls| > 0): {len(d):,d} Serien")
print(f"  ohne Filter:                          {len(d_all):,d} Serien "
      f"(+{len(d_all) - len(d):,d})")
print(f"  Matchups {d['Matchup'].nunique():,d}   "
      f"Bookmaker {d['Bookies'].nunique()}")


def cl_se(z, codes, n_g):
    """Cluster-robuste SE des Mittelwerts von z, geclustert auf Matchup."""
    s = np.zeros(n_g)
    np.add.at(s, codes, z - z.mean())
    return float(np.sqrt((n_g / (n_g - 1)) * (s @ s)) / len(z))


def scores(y, p, codes, n_g, label):
    """Brier, RMSE, BSS und der exakte Abstand zur Kalibrierungsgrenze."""
    brier = float(np.mean((p - y) ** 2))
    limit = float(np.mean(p * (1 - p)))
    z = (y - p) * (1 - 2 * p)          # = (y-p)^2 - p(1-p), exakt
    se_z = cl_se(z, codes, n_g)
    t = z.mean() / se_z
    return {
        "sample": label, "N": len(y), "y_mean": float(y.mean()),
        "p_mean": float(p.mean()), "brier": brier, "rmse": np.sqrt(brier),
        "brier_uninformed": 0.25, "rmse_uninformed": 0.5,
        "bss_vs_uninformed": 1 - brier / 0.25,
        "limit_E_p1mp": limit, "gap": brier - limit,
        "gap_se_cluster": se_z, "gap_t": t,
        "gap_p": 2 * (1 - stats.norm.cdf(abs(t))),
    }


def murphy(y, p, nbin, how):
    """Murphy-Zerlegung Brier = REL - RES + UNC ueber `nbin` Bins.

    Die Zerlegung ist nur exakt, wenn p innerhalb eines Bins konstant ist.
    Der Rest (Brier - (REL - RES + UNC)) wird mitgefuehrt statt versteckt.
    """
    if how == "quantile":
        b = pd.qcut(p, nbin, labels=False, duplicates="drop")
    else:
        b = pd.cut(p, np.linspace(p.min(), p.max(), nbin + 1),
                   labels=False, include_lowest=True)
    t = (pd.DataFrame({"y": y, "p": p, "b": b}).groupby("b")
         .agg(n=("y", "size"), ybar=("y", "mean"), pbar=("p", "mean")))
    n, N, ybar = t["n"].to_numpy(float), float(len(y)), y.mean()
    rel = float((n * (t["pbar"] - t["ybar"]) ** 2).sum() / N)
    res = float((n * (t["ybar"] - ybar) ** 2).sum() / N)
    unc = float(ybar * (1 - ybar))
    brier = float(np.mean((p - y) ** 2))
    return {"nbin": int(t.shape[0]), "binning": how, "reliability": rel,
            "resolution": res, "uncertainty": unc,
            "rel_minus_res_plus_unc": rel - res + unc, "brier": brier,
            "within_bin_rest": brier - (rel - res + unc),
            "rel_share_of_brier": rel / brier,
            "res_share_of_unc": res / unc}, t


codes, uniq = pd.factorize(d["Matchup"], sort=False)
n_g = len(uniq)
y = d["Match"].to_numpy(float)
p_opn = d["OpnOdds"].to_numpy(float)
p_cls = d["ClsOdds"].to_numpy(float)

# ------------------------------------------- 1) Baselines Opening/Closing
block("1) BRIER, RMSE UND DIE DREI BEZUGSPUNKTE (df_oc)")
rows = [scores(y, p_opn, codes, n_g, "Opening"),
        scores(y, p_cls, codes, n_g, "Closing")]

codes_a, uniq_a = pd.factorize(d_all["Matchup"], sort=False)
y_a = d_all["Match"].to_numpy(float)
rows += [scores(y_a, d_all["OpnOdds"].to_numpy(float), codes_a, len(uniq_a),
                "Opening (ohne |Rtrn|>0-Filter)"),
         scores(y_a, d_all["ClsOdds"].to_numpy(float), codes_a, len(uniq_a),
                "Closing (ohne |Rtrn|>0-Filter)")]

for r in rows:
    print(f"\n  {r['sample']}   N = {r['N']:,d}")
    print(f"    Mittelwert Ausgang y   {r['y_mean']:.5f}")
    print(f"    Mittelwert Preis  p    {r['p_mean']:.5f}   "
          f"Kalibrierung im Grossen: p - y = "
          f"{r['p_mean'] - r['y_mean']:+.5f}")
    print(f"    Brier                  {r['brier']:.5f}")
    print(f"    RMSE                   {r['rmse']:.5f}")
    print("    uninformiert (p=0,5)   Brier 0,25000   RMSE 0,50000")
    print(f"    Brier Skill Score      {r['bss_vs_uninformed']:.5f}   "
          f"({r['bss_vs_uninformed'] * 100:.2f} % Verbesserung gegenueber "
          f"dem Muenzwurf)")
    print(f"    Grenze E[p(1-p)]       {r['limit_E_p1mp']:.5f}   "
          f"(entspricht RMSE {np.sqrt(r['limit_E_p1mp']):.5f})")
    print(f"    Abstand Brier - Grenze {r['gap']:+.6f}   "
          f"SE {r['gap_se_cluster']:.6f} (cluster Matchup)   "
          f"t = {r['gap_t']:+.2f}   p = {r['gap_p']:.3g}")
    print(f"      -> beobachteter Brier liegt "
          f"{'UNTER' if r['gap'] < 0 else 'UEBER'} der Grenze")

base = pd.DataFrame(rows)
base.to_csv(f"{OUT}/baselines.csv", index=False)

# Opening gegen Closing, gepaart
block("2) OPENING GEGEN CLOSING (gepaart, gleiche Serien)")
dz = (p_opn - y) ** 2 - (p_cls - y) ** 2
se = cl_se(dz, codes, n_g)
t = dz.mean() / se
print(f"  Brier(Opening) - Brier(Closing) = {dz.mean():+.6f}   SE {se:.6f}   "
      f"t = {t:+.2f}   p = {2 * (1 - stats.norm.cdf(abs(t))):.3g}")
print(f"  Anteil des Opening-Brier, den das Closing wegnimmt: "
      f"{dz.mean() / rows[0]['brier'] * 100:.2f} %")
print(f"  BSS des Closing gegenueber dem Opening als Referenz: "
      f"{1 - rows[1]['brier'] / rows[0]['brier']:.5f}")
pd.DataFrame([{"delta_brier": dz.mean(), "se_cluster": se, "t": t,
               "p": 2 * (1 - stats.norm.cdf(abs(t))),
               "bss_cls_vs_opn": 1 - rows[1]['brier'] / rows[0]['brier']}]
             ).to_csv(f"{OUT}/opening_vs_closing.csv", index=False)

# ------------------------------------------------- 3) Murphy-Zerlegung
block("3) MURPHY-ZERLEGUNG  Brier = REL - RES + UNC")
print("  UNC = ybar(1-ybar) haengt nur am Sample, nicht am Forecast.")
print("  REL klein = gut kalibriert.  RES gross = trennscharf.\n")
mrows, curves = [], {}
for lab, p in (("Opening", p_opn), ("Closing", p_cls)):
    for how in ("quantile", "equal_width"):
        for nb in (10, 20, 50):
            m, t_ = murphy(y, p, nb, how)
            m["sample"] = lab
            mrows.append(m)
            if how == "quantile" and nb == 20:
                curves[lab] = t_.reset_index()
    print(f"  {lab}")
    for m in [x for x in mrows if x["sample"] == lab]:
        print(f"    {m['binning']:<12s} k={m['nbin']:>3d}   "
              f"REL {m['reliability']:.6f}   RES {m['resolution']:.6f}   "
              f"UNC {m['uncertainty']:.6f}   Summe "
              f"{m['rel_minus_res_plus_unc']:.6f}   Rest "
              f"{m['within_bin_rest']:+.6f}")
mp = pd.DataFrame(mrows)[["sample", "binning", "nbin", "reliability",
                          "resolution", "uncertainty",
                          "rel_minus_res_plus_unc", "brier",
                          "within_bin_rest", "rel_share_of_brier",
                          "res_share_of_unc"]]
mp.to_csv(f"{OUT}/murphy.csv", index=False)

ref = mp[(mp["binning"] == "quantile") & (mp["nbin"] == 20)]
print("\n  Lesart (20 Quantilsbins):")
for _, r in ref.iterrows():
    print(f"    {r['sample']:<8s} REL = {r['reliability']:.5f} "
          f"({r['rel_share_of_brier'] * 100:.2f} % des Brier) -- "
          f"Fehlkalibrierung ist klein, aber vorhanden;   "
          f"RES = {r['resolution']:.5f} "
          f"({r['res_share_of_unc'] * 100:.2f} % der Unsicherheit aufgeloest)")

# Kalibrierungskurve und -steigung: Bruecke zum Favorite-Longshot-Befund
block("4) KALIBRIERUNGSKURVE UND -STEIGUNG (Bruecke zu eta_1 = 1,125)")
crows = []
for lab, p in (("Opening", p_opn), ("Closing", p_cls)):
    c = curves[lab]
    w = c["n"].to_numpy(float)
    X = np.column_stack([np.ones(len(c)), c["pbar"].to_numpy(float)])
    b = np.linalg.solve(X.T @ (X * w[:, None]), (X * w[:, None]).T
                        @ c["ybar"].to_numpy(float))
    # dieselbe Groesse auf Kontraktebene, ohne Binnung
    Xi = np.column_stack([np.ones(len(y)), p])
    bi = np.linalg.solve(Xi.T @ Xi, Xi.T @ y)
    print(f"  {lab}:  Bin-Kalibrierung ybar = {b[0]:+.4f} + {b[1]:.4f} * pbar"
          f"   |   Kontraktebene y = {bi[0]:+.4f} + {bi[1]:.4f} * p")
    crows.append({"sample": lab, "bin_intercept": b[0], "bin_slope": b[1],
                  "contract_intercept": bi[0], "contract_slope": bi[1]})
    c.assign(sample=lab).to_csv(
        f"{OUT}/calibration_{lab.lower()}.csv", index=False)
pd.DataFrame(crows).to_csv(f"{OUT}/calibration_slopes.csv", index=False)
print("\n  Steigung > 1 = unterdisperse Preise: die tatsaechliche Gewinnrate")
print("  ist extremer als der Preis. Deckt sich mit eta_1 = 1,125 aus")
print("  revision/snapshots/eq3_contract_level/ladder.csv (S2-S4) und")
print("  erklaert das Vorzeichen des Abstands zur Grenze in Abschnitt 1.")

# --------------------------------------- 5) Stimmt "around 0.45" noch?
block("5) PRUEFUNG DES PAPERTEXTES: 'RMSE values clustering around 0.45'")
# Figure 1 rechnet auf dem Panel (bookmaker_accuracy.py:62), nicht auf df_oc:
# jede Serie geht mit ihrer Beobachtungszahl gewichtet ein.
w = d_all["NObs"].to_numpy(float)
e2 = (d_all["Match"] - d_all["OpnOdds"]).to_numpy(float) ** 2
fig = (pd.DataFrame({"bookie": d_all["Bookies"], "w": w, "we2": w * e2})
       .groupby("bookie").sum())
fig["rmse_panel"] = np.sqrt(fig["we2"] / fig["w"])
oc = (d.assign(e2=(d["Match"] - d["OpnOdds"]) ** 2)
      .groupby("Bookies")["e2"].mean().pow(0.5).rename("rmse_df_oc"))
cmp_ = fig[["rmse_panel"]].join(oc)

pub = pd.read_csv("revision/snapshots/A_baseline/rmse_by_bookie.csv",
                  index_col="bookie")["rmse"].rename("rmse_publiziert")
cmp_ = cmp_.join(pub)
cmp_["delta_zu_publiziert"] = cmp_["rmse_panel"] - cmp_["rmse_publiziert"]
cmp_ = cmp_.sort_values("rmse_panel")
print(cmp_.round(5).to_string())
cmp_.reset_index().to_csv(f"{OUT}/rmse_by_bookie_check.csv", index=False)

pn = cmp_["rmse_panel"]
print(f"\n  Figure-1-Groesse (Panel, gewichtet):  Spanne {pn.min():.4f} - "
      f"{pn.max():.4f}   Median {pn.median():.4f}   Mittel {pn.mean():.4f}")
print(f"  df_oc-Ebene (ungewichtet):            Spanne "
      f"{cmp_['rmse_df_oc'].min():.4f} - {cmp_['rmse_df_oc'].max():.4f}   "
      f"Median {cmp_['rmse_df_oc'].median():.4f}")
print(f"  max |Delta| gegen publiziert:         "
      f"{cmp_['delta_zu_publiziert'].abs().max():.5f}")
print(f"  Bookmaker unter 0,455:                "
      f"{(pn < 0.455).sum()} von {len(pn)}")
print(f"  Bookmaker in [0,455; 0,465):          "
      f"{((pn >= 0.455) & (pn < 0.465)).sum()}")
print(f"  Bookmaker ab 0,465:                   {(pn >= 0.465).sum()}")
print(f"  gepoolter Opening-RMSE (df_oc):       {rows[0]['rmse']:.4f}")
print("\n  -> 'clustering around 0.45' rundet nach unten ab. Die Masse liegt")
print("     zwischen 0,45 und 0,47, der gepoolte Wert bei "
      f"{rows[0]['rmse']:.3f}. Praeziser: 'between 0.45 and 0.47'.")

print(f"\ngeschrieben: {OUT}/baselines.csv, opening_vs_closing.csv, "
      f"murphy.csv, calibration_*.csv, calibration_slopes.csv, "
      f"rmse_by_bookie_check.csv")
