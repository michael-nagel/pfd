#!/usr/bin/env python3
"""Posting Time und Opening-RMSE (R2-M7 Teil 2, zugleich R3-2).

Referee R2-M7/R3-2: Bookmaker, die ihre Eroeffnungsquote spaeter stellen,
koennen die Preise der Konkurrenz bereits beobachtet haben. Ihr Opening-RMSE
waere dann nicht besser kalibriert, sondern nur spaeter gemessen. Pinnacles
auffaellig hoher Opening-RMSE waere ein Artefakt frueher Marktteilnahme.

Direkter Test: Korrelation zwischen dem medianen Posting-Zeitpunkt (Stunden
vor Anpfiff) und dem Opening-RMSE ueber die 24 Bookmaker der
Schaetzstichprobe. Vorzeichen der Referee-Hypothese: POSITIV -- wer frueher
postet (viele Stunden vor Anpfiff), hat den hoeheren RMSE.

Zusaetzlich, weil die 24-Punkte-Korrelation ueber verschiedene Match-Portfolios
mittelt: dieselbe Frage innerhalb desselben Matchups, auf Kontraktebene mit
Matchup-Fixed-Effects. Dort ist die Match-Zusammensetzung per Konstruktion
konstant.

Frame stammt aus `_rmse_baselines.py`; dort liegt auch die Definition.
Rein diagnostisch, kein Eingriff in die Produktions-Pipeline.
"""

import numpy as np
import pandas as pd
from scipy import stats

OUT = "revision/snapshots/rmse_baselines"
FRAME = ("/mnt/c/Users/micha/AppData/Local/Temp/claude/"
         "C--Users-micha-OneDrive-Michi-pfd/"
         "faf3f6fb-65b6-4ea7-a5e5-08b35a6557d8/scratchpad/"
         "pfd_rmse_frame.parquet")

pd.set_option("display.width", 220)


def block(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78, flush=True)


d = pd.read_parquet(FRAME)
d["e2_opn"] = (d["Match"] - d["OpnOdds"]) ** 2
print(f"Serien {len(d):,d}   Matchups {d['Matchup'].nunique():,d}   "
      f"Bookmaker {d['Bookies'].nunique()}")

# Kontrolle gegen shaped_data: dort sind es 33 Bookmaker. Die Restriktion auf
# 24 kommt aus dem bm_quantile-Filter in filter_and_shape_data.
raw_bm = pd.read_hdf("data/processed/shaped_data.h5", "df")["Bookies"].nunique()
print(f"  (shaped_data enthaelt {raw_bm} Bookmaker; der bm_quantile-Filter "
      f"reduziert auf {d['Bookies'].nunique()})")

# ------------------------------------------------- 1) Posting-Zeitpunkt
block("1) MEDIANER OPENING-ZEITPUNKT JE BOOKMAKER (Stunden vor Anpfiff)")
print("  OpnHrs = Anpfiff minus erster beobachteter Zeitstempel der Serie.")
print("  Gross = frueh im Markt.  Der ts_dur-Filter [12, 72] h begrenzt die")
print("  Serienlaenge, nicht die Lage des Fensters.\n")

bm = d.groupby("Bookies").agg(
    n_series=("GroupId", "size"),
    n_obs=("NObs", "sum"),
    opn_hrs_med=("OpnHrs", "median"),
    opn_hrs_mean=("OpnHrs", "mean"),
    opn_hrs_q25=("OpnHrs", lambda s: s.quantile(0.25)),
    opn_hrs_q75=("OpnHrs", lambda s: s.quantile(0.75)),
    cls_hrs_med=("ClsHrs", "median"),
    ts_dur_med=("TsDurH", "median"),
    margin_opn_med=("MarginOpn", "median"),
)
# Figure-1-Groesse: Panel-gewichtet wie bookmaker_accuracy.py:62
wsum = (d.assign(we2=d["NObs"] * d["e2_opn"])
        .groupby("Bookies")[["NObs", "we2"]].sum())
bm["rmse_panel"] = np.sqrt(wsum["we2"] / wsum["NObs"])
# Serienebene, ungewichtet -- jede Serie zaehlt gleich viel
bm["rmse_series"] = d.groupby("Bookies")["e2_opn"].mean().pow(0.5)
bm = bm.sort_values("opn_hrs_med", ascending=False)

print(bm[["n_series", "opn_hrs_med", "opn_hrs_q25", "opn_hrs_q75",
          "ts_dur_med", "margin_opn_med", "rmse_panel",
          "rmse_series"]].round(4).to_string())
bm.reset_index().to_csv(f"{OUT}/posting_time_by_bookie.csv", index=False)

print(f"\n  Spanne der Mediane: {bm['opn_hrs_med'].min():.2f} h bis "
      f"{bm['opn_hrs_med'].max():.2f} h vor Anpfiff   "
      f"(Faktor {bm['opn_hrs_med'].max() / bm['opn_hrs_med'].min():.2f})")
print(f"  Median ueber die Bookmaker: {bm['opn_hrs_med'].median():.2f} h")
for nm in ("Pinnacle", "BetInAsia", "10Bet", "Vulkan Bet", "GGBET"):
    r = bm.loc[nm]
    print(f"    {nm:<12s} Opening {r['opn_hrs_med']:6.2f} h vor Anpfiff   "
          f"RMSE {r['rmse_panel']:.4f}   Rang Zeit "
          f"{int(bm['opn_hrs_med'].rank(ascending=False)[nm]):>2d} / "
          f"Rang RMSE {int(bm['rmse_panel'].rank()[nm]):>2d}")

# --------------------------------------------------- 2) Korrelationen
block("2) KORRELATION POSTING-ZEITPUNKT GEGEN OPENING-RMSE (n = 24)")
print("  Referee-Hypothese: spaetere Bookmaker sehen besser aus.")
print("  OpnHrs misst FRUEHE Marktteilnahme -> die Hypothese sagt r > 0.\n")

pub = pd.read_csv("revision/snapshots/A_baseline/rmse_by_bookie.csv",
                  index_col="bookie")["rmse"]
bm["rmse_publiziert"] = pub

rows = []
for ylab, yv in (("rmse_panel (Figure 1)", bm["rmse_panel"]),
                 ("rmse_series (Serienebene)", bm["rmse_series"]),
                 ("rmse_publiziert (roh, A_baseline)", bm["rmse_publiziert"])):
    for xlab, xv in (("opn_hrs_med", bm["opn_hrs_med"]),
                     ("opn_hrs_mean", bm["opn_hrs_mean"])):
        rp, pp = stats.pearsonr(xv, yv)
        rs, ps = stats.spearmanr(xv, yv)
        rows.append({"y": ylab, "x": xlab, "pearson": rp, "p_pearson": pp,
                     "spearman": rs, "p_spearman": ps, "n": len(bm)})
        print(f"  {ylab:<36s} vs {xlab:<13s}  "
              f"Pearson {rp:+.4f} (p {pp:.4f})   "
              f"Spearman {rs:+.4f} (p {ps:.4f})")

# Kontrollgroessen, die dieselbe Achse belegen koennten
print()
for xlab, xv in (("margin_opn_med", bm["margin_opn_med"]),
                 ("ts_dur_med", bm["ts_dur_med"]),
                 ("n_series", bm["n_series"])):
    rp, pp = stats.pearsonr(xv, bm["rmse_panel"])
    rs, ps = stats.spearmanr(xv, bm["rmse_panel"])
    rows.append({"y": "rmse_panel (Figure 1)", "x": xlab, "pearson": rp,
                 "p_pearson": pp, "spearman": rs, "p_spearman": ps,
                 "n": len(bm)})
    print(f"  {'rmse_panel (Figure 1)':<36s} vs {xlab:<13s}  "
          f"Pearson {rp:+.4f} (p {pp:.4f})   "
          f"Spearman {rs:+.4f} (p {ps:.4f})")
rp, pp = stats.pearsonr(bm["margin_opn_med"], bm["rmse_publiziert"])
rs, _ = stats.spearmanr(bm["margin_opn_med"], bm["rmse_publiziert"])
print(f"\n  Gegenprobe zum Eintrag im revision_log (Marge gegen ROHEN RMSE, "
      f"-0,34): Pearson {rp:+.4f}, Spearman {rs:+.4f}")
rp2, _ = stats.pearsonr(bm["margin_opn_med"], bm["opn_hrs_med"])
rs2, _ = stats.spearmanr(bm["margin_opn_med"], bm["opn_hrs_med"])
print(f"  Marge gegen Posting-Zeitpunkt: Pearson {rp2:+.4f}, "
      f"Spearman {rs2:+.4f}")
pd.DataFrame(rows).to_csv(f"{OUT}/correlations.csv", index=False)

# ------------------------------------------ 3) Partielle Betrachtung
block("2b) DIE GEWICHTUNG IN FIGURE 1 ENTSCHEIDET UEBER DAS VORZEICHEN")
print("  bookmaker_accuracy.py:62 rechnet den RMSE auf dem PANEL. OpnOdds ist")
print("  je Serie konstant, also geht jede Serie mit ihrer Zahl an")
print("  Preisupdates gewichtet ein. Fuer eine Prognosegueteaussage muesste")
print("  jedes Spiel einmal zaehlen.\n")
bm["obs_per_series"] = bm["n_obs"] / bm["n_series"]
bm["rmse_gap"] = bm["rmse_panel"] - bm["rmse_series"]
for xlab, xv in (("obs_per_series", bm["obs_per_series"]),
                 ("opn_hrs_med", bm["opn_hrs_med"])):
    rp, pp = stats.pearsonr(xv, bm["rmse_gap"])
    print(f"  rmse_gap (panel - series) vs {xlab:<15s} Pearson {rp:+.4f} "
          f"(p {pp:.4f})")
rp, pp = stats.pearsonr(bm["obs_per_series"], bm["opn_hrs_med"])
print(f"  obs_per_series            vs opn_hrs_med     Pearson {rp:+.4f} "
      f"(p {pp:.4f})")
print(f"\n  Spanne obs_per_series: {bm['obs_per_series'].min():.2f} bis "
      f"{bm['obs_per_series'].max():.2f} Updates je Serie")
print(f"  Spanne rmse_gap:       {bm['rmse_gap'].min():+.4f} bis "
      f"{bm['rmse_gap'].max():+.4f}")
bm.reset_index().to_csv(f"{OUT}/posting_time_by_bookie.csv", index=False)

block("3) PARTIELL, KONTROLLIERT FUER DIE BOOKMAKER-MARGE")


def partial(x, y, z):
    """r_xy.z plus t-Test mit df = n - 3."""
    rxy = stats.pearsonr(x, y)[0]
    rxz = stats.pearsonr(x, z)[0]
    ryz = stats.pearsonr(y, z)[0]
    r = (rxy - rxz * ryz) / np.sqrt((1 - rxz**2) * (1 - ryz**2))
    dfree = len(x) - 3
    t = r * np.sqrt(dfree / (1 - r**2))
    return r, t, 2 * (1 - stats.t.cdf(abs(t), dfree))


prows = []
for ylab, yv in (("rmse_panel", bm["rmse_panel"]),
                 ("rmse_series", bm["rmse_series"]),
                 ("rmse_publiziert", bm["rmse_publiziert"])):
    x = bm["opn_hrs_med"].to_numpy(float)
    y = yv.to_numpy(float)
    z = bm["margin_opn_med"].to_numpy(float)
    r0 = stats.pearsonr(x, y)[0]
    r, t, p = partial(x, y, z)
    # Rang-Fassung: partielle Spearman-Korrelation ueber die Raenge
    rr, tr, pr = partial(stats.rankdata(x), stats.rankdata(y),
                         stats.rankdata(z))
    print(f"  {ylab:<16s}  roh {r0:+.4f}   partiell (Marge heraus) "
          f"{r:+.4f}  t = {t:+.2f}  p = {p:.4f}   |   "
          f"Rang-partiell {rr:+.4f} (p {pr:.4f})")
    prows.append({"y": ylab, "pearson_raw": r0, "pearson_partial": r,
                  "t": t, "p": p, "spearman_partial": rr, "p_spearman": pr})
pd.DataFrame(prows).to_csv(f"{OUT}/partial_correlations.csv", index=False)

# gemeinsame Regression, damit die Groessenordnung interpretierbar ist
X = np.column_stack([np.ones(len(bm)), bm["opn_hrs_med"],
                     bm["margin_opn_med"]])
y = bm["rmse_panel"].to_numpy(float)
XtXi = np.linalg.inv(X.T @ X)
b = XtXi @ (X.T @ y)
u = y - X @ b
se = np.sqrt(np.diag((u @ u) / (len(y) - 3) * XtXi))
r2 = 1 - (u @ u) / ((y - y.mean()) @ (y - y.mean()))
print(f"\n  RMSE_panel = {b[0]:.5f} + {b[1]:+.6f} * OpnHrs "
      f"{b[2]:+.5f} * Marge      R2 = {r2:.4f}")
for nm, bi, si in zip(["const", "opn_hrs_med", "margin_opn_med"], b, se,
                      strict=True):
    print(f"    {nm:<16s} {bi:>12.6f}  ({si:.6f})   t = {bi / si:>6.2f}")
sd_h = bm["opn_hrs_med"].std()
print(f"  Lesart: eine Standardabweichung frueheres Posting "
      f"({sd_h:.2f} h) verschiebt den RMSE um {b[1] * sd_h:+.5f} -- "
      f"gegen eine beobachtete Spanne von "
      f"{bm['rmse_panel'].max() - bm['rmse_panel'].min():.5f}.")
pd.DataFrame({"term": ["const", "opn_hrs_med", "margin_opn_med"],
              "coef": b, "se": se, "t": b / se,
              "r2": r2}).to_csv(f"{OUT}/joint_regression.csv", index=False)

# ------------------------ 4) Dieselbe Frage innerhalb desselben Matchups
block("4) ZUSATZ: INNERHALB DESSELBEN MATCHUPS (Kontraktebene, FE)")
print("  Die 24-Punkte-Korrelation vergleicht Bookmaker mit verschiedenen")
print("  Match-Portfolios. Mit Matchup-FE faellt diese Zusammensetzung heraus:")
print("  verglichen werden nur Bookmaker, die DASSELBE Spiel quotieren.\n")

m = d[d.groupby("Matchup")["GroupId"].transform("size") > 1].copy()
print(f"  Matchups mit mindestens zwei Bookmakern: "
      f"{m['Matchup'].nunique():,d}   Kontrakte {len(m):,d}")

codes, uniq = pd.factorize(m["Matchup"], sort=False)
n_g = len(uniq)


def fe_fit(dm, extra_cols, label):
    """Matchup absorbiert per Demeaning; SEs cluster-robust auf Matchup."""
    cols = ["OpnHrs"] + extra_cols
    Xr = dm[cols].to_numpy(float)
    yr = dm["e2_opn"].to_numpy(float)
    def dmn(a):
        return a - (pd.DataFrame(a).groupby(codes)
                    .transform("mean").to_numpy())

    Xd, yd = dmn(Xr), dmn(yr.reshape(-1, 1)).ravel()
    XtXi = np.linalg.inv(Xd.T @ Xd)
    b = XtXi @ (Xd.T @ yd)
    u = yd - Xd @ b
    S = np.zeros((n_g, Xd.shape[1]))
    np.add.at(S, codes, Xd * u[:, None])
    N, K = len(yd), Xd.shape[1] + n_g
    V = (n_g / (n_g - 1)) * ((N - 1) / (N - K)) * (XtXi @ (S.T @ S) @ XtXi)
    se = np.sqrt(np.diag(V))
    print(f"  {label}")
    print(f"    OpnHrs  {b[0]:+.3e}  (SE {se[0]:.3e})   t = {b[0] / se[0]:+.2f}"
          f"   p = {2 * (1 - stats.norm.cdf(abs(b[0] / se[0]))):.4f}")
    return {"spec": label, "coef_opn_hrs": b[0], "se_cluster": se[0],
            "t": b[0] / se[0],
            "p": 2 * (1 - stats.norm.cdf(abs(b[0] / se[0])))}


frows = [fe_fit(m, [], "Matchup-FE")]
bk = sorted(m["Bookies"].unique())
for b_ in bk[1:]:
    m[f"B_{b_}"] = (m["Bookies"] == b_).astype(float)
frows.append(fe_fit(m, [f"B_{b_}" for b_ in bk[1:]],
                    "Matchup-FE + Bookmaker-FE"))
pd.DataFrame(frows).to_csv(f"{OUT}/within_matchup_fe.csv", index=False)

sd_within = (m["OpnHrs"] - m.groupby("Matchup")["OpnHrs"]
             .transform("mean")).std()
print(f"\n  Streuung von OpnHrs innerhalb eines Matchups: sd "
      f"{sd_within:.3f} h")
print(f"  Effekt einer Stunde frueheren Postings auf den quadrierten Fehler: "
      f"{frows[0]['coef_opn_hrs']:+.3e}")
span = bm["opn_hrs_med"].max() - bm["opn_hrs_med"].min()
d_brier = frows[0]["coef_opn_hrs"] * span
# Umrechnung Brier -> RMSE ueber die Ableitung d sqrt(B) = dB / (2 sqrt(B))
d_rmse = d_brier / (2 * bm["rmse_panel"].mean())
print(f"  Hochgerechnet auf die Spanne der Bookmaker-Mediane "
      f"({span:.2f} h): {d_brier:+.5f} im Brier, das sind "
      f"{d_rmse:+.5f} im RMSE.")
print(f"  Beobachtete Spanne ueber die Bookmaker: panel "
      f"{bm['rmse_panel'].max() - bm['rmse_panel'].min():.5f}, Serienebene "
      f"{bm['rmse_series'].max() - bm['rmse_series'].min():.5f}")

print(f"\ngeschrieben: {OUT}/posting_time_by_bookie.csv, correlations.csv, "
      f"partial_correlations.csv, joint_regression.csv, "
      f"within_matchup_fe.csv")
