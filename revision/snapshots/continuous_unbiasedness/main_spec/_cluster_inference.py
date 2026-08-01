#!/usr/bin/env python3
"""Match-Clusterung ohne Match-Random-Intercept: robuste Inferenz + Absorption.

Hintergrund: die Hauptspezifikation mit `(1 | Matchup)` ist im Niveau stabil,
in der Kovarianzstruktur aber entartet (Bookmaker-Intercept sd 0,00017,
Residual-sd 0,015, beta_1-SE über das ganze Gitter konstant 0,155). Grund ist
strukturell: `Endog = Match - p_ref` ist innerhalb einer Serie konstant, der
Match-Intercept absorbiert daher fast die gesamte Varianz der abhängigen
Variablen. R2/R1-ii verlangt, die Abhängigkeit der Serien innerhalb eines
Matchups zu berücksichtigen -- das geht auch über cluster-robuste Inferenz
auf M_c, ohne den Punktschätzer zu verändern.

  1) analytischer Cluster-Sandwich (CR1) für beta_1, geclustert auf Matchup,
     gegen die modellbasierten SEs von M_c (lme4). Der Bootstrap über
     Match-Resampling wäre mit 58 s je Fit und B = 300 rund 4,8 h sequentiell
     bzw. ~2,4 h mit zwei Prozessen (mehr passt nicht in 11,4 GB) -- der
     Sandwich kostet Sekunden und ist für lineare Modelle die
     Standardantwort. Ein kleiner Bootstrap validiert ihn separat.
  2) ANOVA-Zerlegung: welcher Anteil der Varianz von Endog liegt auf
     Matchup-Ebene
  3) wie viel Streuung bleibt für die Within-Match-Identifikation: sd von
     p_ref innerhalb eines Matchups gegen sd insgesamt

Rein diagnostisch, nichts an der Produktions-Pipeline.
"""

import sys
import tempfile
import time

import numpy as np
import pandas as pd
import rpy2.robjects as ro
from omegaconf import OmegaConf
from rpy2.robjects import numpy2ri, pandas2ri
from rpy2.robjects.conversion import localconverter

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

OUT = "revision/snapshots/continuous_unbiasedness/main_spec"
FRAME = f"{tempfile.gettempdir()}/pfd_mainspec_frame2.parquet"
COVS = ["TsDur", "Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
        "Compet_WTA"]
K = 6
NGRID = 100
MARKS = [24.0, 12.0, 6.0, 3.0, 1.0, 0.25]

pd.set_option("display.width", 220)
ro.r("library(mgcv); library(lme4)")


def build():
    """Wie `_lme4_main.py`, zusätzlich PRef und Match (für Teil 2 und 3)."""
    cfg = OmegaConf.create({"estimation": {
        "spec": "BmHome", "normalize": True, "compets": None,
        "bm_quantile": 0.25, "ts_dur": [12, 72], "period": None,
        "resample_freq": "1min", "pctl": 2}})

    raw = pd.read_hdf("data/processed/shaped_data.h5", "df")
    for c in ("Date", "Update"):
        raw[c] = pd.to_datetime(raw[c])
    kick = raw.groupby("Matchup")["Date"].first()
    d, *_ = filter_and_shape_data(raw.copy(), cfg)

    d["Kick"] = d["Matchup"].map(kick)
    d["HoursToKick"] = (d["Kick"] - d["Update"]).dt.total_seconds() / 3600.0
    d = d[d["HoursToKick"] > 0]
    d = d[d.groupby("GroupId")["OddsMvt"].transform("std") > 0]
    d = d[d["NumOddsMvt"] < 20]

    d = d.sort_values(["GroupId", "Update"])
    d["PRef"] = d.groupby("GroupId", sort=False)["OddsMvt"].transform("first")
    d["Endog"] = d["Match"] - d["PRef"]
    d["Exog"] = d["OddsMvt"] - d["PRef"]
    d["ObsIdx"] = d.groupby("GroupId").cumcount()
    d = d[d["ObsIdx"] > 0]

    d["X"] = np.log(d["HoursToKick"])
    keep = ["GroupId", "Matchup", "Bookies", "X", "HoursToKick", "Endog",
            "Exog", "PRef", "Match", "NumOddsMvt"] + COVS
    d = d[keep].reset_index(drop=True)
    d.to_parquet(FRAME)
    return d


def block(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78, flush=True)


try:
    df = pd.read_parquet(FRAME)
    print(f"Frame aus Cache: {len(df):,d} Zeilen")
except (FileNotFoundError, OSError):
    df = build()
    print(f"Frame neu gebaut: {len(df):,d} Zeilen")

df["Bookies"] = df["Bookies"].astype(str)
G = df["Matchup"].nunique()
print(f"  {df['GroupId'].nunique():,d} Serien, {G:,d} Matchups, "
      f"{df['Bookies'].nunique()} Bookmaker", flush=True)

# ------------------------------------------------ 2) ANOVA-Zerlegung Endog
block("2) ANOVA: WIEVIEL DER VARIANZ VON Endog LIEGT AUF MATCHUP-EBENE?")

# Endog ist innerhalb einer Serie konstant -> die Zerlegung ist auf
# Serienebene die inhaltlich richtige; auf Beobachtungsebene gewichtet sie
# lange Serien stärker. Beides wird berichtet.
ser = df.groupby("GroupId").agg(Matchup=("Matchup", "first"),
                                Endog=("Endog", "first"),
                                PRef=("PRef", "first"),
                                Match=("Match", "first"))
rows = []
for lab, d, col in (("Serienebene", ser, "Endog"),
                    ("Beobachtungsebene", df, "Endog")):
    grand = d[col].var(ddof=0)
    btw = d.groupby("Matchup")[col].transform("mean").var(ddof=0)
    rows.append({"Ebene": lab, "n": len(d), "var_gesamt": grand,
                 "var_between": btw, "var_within": grand - btw,
                 "Anteil_between": btw / grand})
an = pd.DataFrame(rows)
print(an.to_string(index=False, float_format=lambda v: f"{v:,.6f}"))
print(f"\n  Anteil der Endog-Varianz auf Matchup-Ebene: "
      f"{an['Anteil_between'].iloc[0] * 100:.2f} % (Serienebene), "
      f"{an['Anteil_between'].iloc[1] * 100:.2f} % (Beobachtungsebene)")
print(f"  Modellbasiert (Hauptspezifikation): "
      f"{0.193652 / (0.193652 + 0.000226) * 100:.2f} % "
      f"(= var_Matchup / (var_Matchup + var_Resid))")
an.to_csv(f"{OUT}/absorption_anova.csv", index=False)

# --------------------------------------- 3) Wieviel Streuung bleibt within
block("3) STREUUNG VON p_ref: INNERHALB EINES MATCHUPS GEGEN INSGESAMT")

n_bm = ser.groupby("Matchup").size()
within_sd = ser.groupby("Matchup")["PRef"].std(ddof=1)
tot_sd = ser["PRef"].std(ddof=1)
# gepoolte Within-sd: sqrt( sum (n_g-1) s_g^2 / sum (n_g-1) )
ok = n_bm[n_bm > 1].index
w = (n_bm.loc[ok] - 1)
pooled = float(np.sqrt((w * within_sd.loc[ok] ** 2).sum() / w.sum()))
btw_sd = float(ser.groupby("Matchup")["PRef"].mean().std(ddof=1))

print(f"  p_ref insgesamt          sd {tot_sd:.5f}   "
      f"(n = {len(ser):,d} Serien)")
print(f"  zwischen Matchups        sd {btw_sd:.5f}")
print(f"  innerhalb eines Matchups sd {pooled:.5f} (gepoolt über "
      f"{len(ok):,d} Matchups mit >= 2 Bookmakern)")
print(f"  Median der Within-sd        {within_sd.loc[ok].median():.5f}")
print(f"\n  Within-Anteil an der Gesamtstreuung: "
      f"{pooled / tot_sd * 100:.1f} %   (Varianzanteil "
      f"{(pooled / tot_sd) ** 2 * 100:.1f} %)")
print(f"  Bookmaker je Matchup: Median {int(n_bm.median())}, "
      f"Mittel {n_bm.mean():.1f}, Spanne {n_bm.min()}-{n_bm.max()}")
pd.DataFrame([{"sd_total": tot_sd, "sd_between": btw_sd,
               "sd_within_pooled": pooled,
               "sd_within_median": float(within_sd.loc[ok].median()),
               "n_matchups_ge2": len(ok), "bm_per_matchup_median":
               float(n_bm.median()), "share_within":
               pooled / tot_sd}]).to_csv(
    f"{OUT}/pref_within_between.csv", index=False)

# ------------------------------------------ 1) Cluster-robuste Inferenz
block("1) CLUSTER-ROBUSTE INFERENZ FÜR beta_1 (Cluster = Matchup)")

h_lo, h_hi = df["HoursToKick"].quantile([0.01, 0.99])
HRS = np.exp(np.linspace(np.log(h_hi), np.log(h_lo), NGRID))

with localconverter(ro.default_converter + pandas2ri.converter):
    ro.globalenv["d0"] = df[["Endog", "Exog", "X", "Bookies"] + COVS]
ro.globalenv["kk"] = K
ro.r("""
sm <- smoothCon(s(X, k = kk, bs = "cr"), data = d0, absorb.cons = TRUE)[[1]]
B  <- PredictMat(sm, d0)
""")
with localconverter(ro.default_converter + numpy2ri.converter):
    Bm = np.asarray(ro.globalenv["B"], float)
    ro.globalenv["hrs"] = HRS
ro.r('Bg <- PredictMat(sm, data.frame(X = log(hrs)))')
with localconverter(ro.default_converter + numpy2ri.converter):
    Bg = np.asarray(ro.globalenv["Bg"], float)
nb = Bm.shape[1]
print(f"  Basisspalten {nb} (k = {K}, cr)")

ex = df["Exog"].to_numpy()
Xd = np.column_stack([np.ones(len(df)), Bm, ex, Bm * ex[:, None],
                      df[COVS].to_numpy()])
y = df["Endog"].to_numpy()
names = (["(Intercept)"] + [f"b{j}" for j in range(1, nb + 1)] + ["Exog"]
         + [f"eb{j}" for j in range(1, nb + 1)] + COVS)
N, Kp = Xd.shape
print(f"  Designmatrix {N:,d} x {Kp}")

XtX = Xd.T @ Xd
XtXi = np.linalg.inv(XtX)
beta = XtXi @ (Xd.T @ y)
u = y - Xd @ beta

# Cluster-Scores: pro Matchup s_g = X_g' u_g, dann meat = sum_g s_g s_g'
codes = pd.factorize(df["Matchup"], sort=False)[0]
S = np.zeros((G, Kp))
np.add.at(S, codes, Xd * u[:, None])
meat = S.T @ S
cf = (G / (G - 1)) * ((N - 1) / (N - Kp))          # CR1
V_cr = cf * (XtXi @ meat @ XtXi)
V_ols = (u @ u) / (N - Kp) * XtXi

# beta_1(x) = coef(Exog) + sum_j coef(eb_j) * B_j(x)
C = np.zeros((len(HRS), Kp))
C[:, names.index("Exog")] = 1.0
for j in range(nb):
    C[:, names.index(f"eb{j + 1}")] = Bg[:, j]
b1 = C @ beta
se_cr = np.sqrt(np.einsum("ij,jk,ik->i", C, V_cr, C))
se_ols = np.sqrt(np.einsum("ij,jk,ik->i", C, V_ols, C))

# Modellbasierte SEs von M_c (lme4) auf demselben Gitter
print("\n  M_c (lme4, ohne Matchup) für den Vergleich der SEs ...", flush=True)
fe = (" + ".join(f"b{j}" for j in range(1, nb + 1)) + " + Exog + "
      + " + ".join(f"eb{j}" for j in range(1, nb + 1)) + " + "
      + " + ".join(COVS))
ro.globalenv["fml"] = f"Endog ~ {fe} + (1 + Exog | Bookies)"
ro.r("""
d <- d0
for (j in seq_len(ncol(B))) {
    d[[paste0("b", j)]]  <- B[, j]
    d[[paste0("eb", j)]] <- B[, j] * d0$Exog
}
d$Bookies <- factor(d$Bookies)
""")
t0 = time.time()
ro.r("""
m <- lmer(as.formula(fml), data = d, REML = FALSE)
fx <- fixef(m); Vf <- as.matrix(vcov(m))
""")
secs = time.time() - t0
with localconverter(ro.default_converter + numpy2ri.converter):
    fx = np.asarray(ro.globalenv["fx"], float)
    Vf = np.asarray(ro.globalenv["Vf"], float)
fx_names = list(ro.r("names(fx)"))
Cl = np.zeros((len(HRS), len(fx)))
Cl[:, fx_names.index("Exog")] = 1.0
for j in range(nb):
    Cl[:, fx_names.index(f"eb{j + 1}")] = Bg[:, j]
b1_l = Cl @ fx
se_l = np.sqrt(np.einsum("ij,jk,ik->i", Cl, Vf, Cl))
print(f"    lmer {secs:.1f} s")

print(f"\n  Punktschätzer: max |beta_1(OLS) - beta_1(M_c lme4)| = "
      f"{np.max(np.abs(b1 - b1_l)):.5f}")
print("  -> " + ("OLS-Sandwich ist für M_c verwendbar."
                 if np.max(np.abs(b1 - b1_l)) < 0.01 else
                 "ACHTUNG: Punktschätzer weichen ab, Sandwich nicht "
                 "übertragbar."))

res = pd.DataFrame({"hours": HRS, "beta_1": b1, "se_cluster": se_cr,
                    "se_ols": se_ols, "beta_1_lmer": b1_l,
                    "se_lmer_model": se_l})
res["ci_lo"] = res["beta_1"] - 1.96 * res["se_cluster"]
res["ci_up"] = res["beta_1"] + 1.96 * res["se_cluster"]
res["inflation_vs_lmer"] = res["se_cluster"] / res["se_lmer_model"]
res.to_csv(f"{OUT}/cluster_robust_beta1.csv", index=False)

print(f"\n  SE-Vergleich (Faktor Cluster/modellbasiert): Median "
      f"{res['inflation_vs_lmer'].median():.2f}, Spanne "
      f"{res['inflation_vs_lmer'].min():.2f}-"
      f"{res['inflation_vs_lmer'].max():.2f}")
print(f"  SE-Vergleich (Faktor Cluster/OLS-iid):        Median "
      f"{(res['se_cluster'] / res['se_ols']).median():.2f}")

with localconverter(ro.default_converter + numpy2ri.converter):
    ro.globalenv["hrs"] = np.asarray(MARKS, float)
ro.r('Bg <- PredictMat(sm, data.frame(X = log(hrs)))')
with localconverter(ro.default_converter + numpy2ri.converter):
    Bk = np.asarray(ro.globalenv["Bg"], float)
Ck = np.zeros((len(MARKS), Kp))
Ck[:, names.index("Exog")] = 1.0
for j in range(nb):
    Ck[:, names.index(f"eb{j + 1}")] = Bk[:, j]
Ckl = np.zeros((len(MARKS), len(fx)))
Ckl[:, fx_names.index("Exog")] = 1.0
for j in range(nb):
    Ckl[:, fx_names.index(f"eb{j + 1}")] = Bk[:, j]
mk = pd.DataFrame({
    "hours": MARKS, "beta_1": Ck @ beta,
    "se_cluster": np.sqrt(np.einsum("ij,jk,ik->i", Ck, V_cr, Ck)),
    "se_lmer_model": np.sqrt(np.einsum("ij,jk,ik->i", Ckl, Vf, Ckl))})
mk["ci_lo"] = mk["beta_1"] - 1.96 * mk["se_cluster"]
mk["ci_up"] = mk["beta_1"] + 1.96 * mk["se_cluster"]
mk.to_csv(f"{OUT}/cluster_robust_marks.csv", index=False)
print("\n  Stundenmarken mit cluster-robustem Band:")
print(mk.to_string(index=False, float_format=lambda v: f"{v:,.4f}"))

print(f"\ngeschrieben: {OUT}/absorption_anova.csv, pref_within_between.csv, "
      f"cluster_robust_{{beta1,marks}}.csv")
