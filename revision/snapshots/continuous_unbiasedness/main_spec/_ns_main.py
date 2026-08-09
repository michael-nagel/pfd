#!/usr/bin/env python3
"""Hauptspezifikation auf der ns(df=4)-Basis: Punktschaetzer, Band, RMSE-Kurve.

Basiswahl entschieden (R1-vii): natural cubic spline mit linearen
Randbedingungen statt der cr-Basis. Grund ist das Randartefakt der
unpenalisierten cr-Basis -- sie faellt bei 45,5 h auf 0,82 und prallt
danach auf 1,244 bei 24 h zurueck, waehrend die penalisierte mgcv-Referenz
dort monoton bei 1,151 liegt (`_basis_options.py`). Die ns-Basis hat das
Artefakt nicht und trifft die Referenz.

Drei Ausgaben:

  1) beta_1 auf dem Gitter, CR1-Sandwich auf Matchup, plus SIMULTANES
     sup-t-Band. Das Band ist VORLAEUFIG aus dem Sandwich gerechnet; der
     Cluster-Bootstrap auf derselben Basis laeuft separat
     (`_ns_bootstrap.py`) und ersetzt es, sobald er fertig ist.
  2) Die Stundenmarken als Tabelle.
  3) Die deskriptive RMSE-Kurve fuer das untere Panel: Wurzel des mittleren
     quadrierten Prognosefehlers der PREISE, (p(t) - Ausgang)^2, gebinnt
     ueber die Zeitachse. KEIN Modell, keine Glaettung -- ausdruecklich eine
     andere Groesse als der Residual-RMSE der 50 Perzentilregressionen.

Rein diagnostisch, nichts an der Produktions-Pipeline.
"""

import tempfile

import numpy as np
import pandas as pd
import rpy2.robjects as ro
from rpy2.robjects import numpy2ri, pandas2ri
from rpy2.robjects.conversion import localconverter

OUT = "revision/snapshots/continuous_unbiasedness/main_spec"
FRAME = f"{tempfile.gettempdir()}/pfd_mainspec_frame2.parquet"
COVS = ["TsDur", "Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
        "Compet_WTA"]
DF = 4
NGRID = 100
MARKS = [24.0, 12.0, 6.0, 3.0, 1.0, 0.25]
HMAX = 48.0
ALPHA = 0.05
NSIM = 200_000
NBINS = 22

pd.set_option("display.width", 220)
rng = np.random.default_rng(20260809)
ro.r("library(splines)")

df = pd.read_parquet(FRAME)
h_lo, h_hi = df["HoursToKick"].quantile([0.01, 0.99])
HRS = np.exp(np.linspace(np.log(h_hi), np.log(h_lo), NGRID))
print(f"{len(df):,d} Zeilen, {df['GroupId'].nunique():,d} Serien, "
      f"{df['Matchup'].nunique():,d} Matchups")

# ------------------------------------------------------------- 1) Basis
with localconverter(ro.default_converter + pandas2ri.converter):
    ro.globalenv["d0"] = df[["X"]]
with localconverter(ro.default_converter + numpy2ri.converter):
    ro.globalenv["hrs"] = HRS
ro.globalenv["dfree"] = DF
ro.r("""
sm <- ns(d0$X, df = dfree)
B  <- predict(sm, d0$X)
Bg <- predict(sm, log(hrs))
""")
with localconverter(ro.default_converter + numpy2ri.converter):
    B = np.asarray(ro.globalenv["B"], float)
    Bg = np.asarray(ro.globalenv["Bg"], float)
nb = B.shape[1]
print(f"ns-Basis: {nb} Spalten (df = {DF}, lineare Randbedingungen)")

# -------------------------------------------------- 2) OLS + CR1-Sandwich
exog = df["Exog"].to_numpy()
y = df["Endog"].to_numpy()
C_cov = df[COVS].to_numpy()
X = np.column_stack([np.ones(len(df)), B, exog, B * exog[:, None], C_cov])
names = (["const"] + [f"b{j}" for j in range(1, nb + 1)] + ["Exog"]
         + [f"eb{j}" for j in range(1, nb + 1)] + COVS)

xtx_inv = np.linalg.inv(X.T @ X)
beta = xtx_inv @ (X.T @ y)
u = y - X @ beta
n, k = X.shape

g = pd.factorize(df["Matchup"])[0]
Xu = X * u[:, None]
order = np.argsort(g)
Xu_s, g_s = Xu[order], g[order]
bounds = np.flatnonzero(np.r_[True, g_s[1:] != g_s[:-1], True])
meat = np.zeros((k, k))
for a, b in zip(bounds[:-1], bounds[1:]):
    s = Xu_s[a:b].sum(axis=0)
    meat += np.outer(s, s)
G = len(bounds) - 1
c = (G / (G - 1)) * ((n - 1) / (n - k))
V = c * xtx_inv @ meat @ xtx_inv

# Kontrastmatrix: beta_1(x) = coef(Exog) + sum_j coef(eb_j) * B_j(x)
Cm = np.zeros((NGRID, k))
Cm[:, names.index("Exog")] = 1.0
for j in range(nb):
    Cm[:, names.index(f"eb{j + 1}")] = Bg[:, j]

b1 = Cm @ beta
Vb1 = Cm @ V @ Cm.T
se = np.sqrt(np.diag(Vb1))
print(f"CR1: G = {G:,d} Cluster, N = {n:,d}, K = {k}")

# ------------------------------------- 3) Simultanes Band aus dem Sandwich
m = HRS <= HMAX
w, v = np.linalg.eigh(Vb1[np.ix_(m, m)])
keep = w > w.max() * 1e-10
root = v[:, keep] * np.sqrt(w[keep])
draws = rng.standard_normal((NSIM, root.shape[1])) @ root.T
crit = float(np.percentile(np.abs(draws / se[m]).max(axis=1),
                           100 * (1 - ALPHA)))
z_pw = 1.959964
print(f"Rang der beta_1-Kovarianz: {int(keep.sum())}   "
      f"sup-t-Wert {crit:.3f} gegen {z_pw:.3f} punktweise")

res = pd.DataFrame({
    "hours": HRS, "beta_1": b1, "se_cluster": se,
    "pw_lo": b1 - z_pw * se, "pw_up": b1 + z_pw * se,
    "sim_lo": b1 - crit * se, "sim_up": b1 + crit * se,
})
res["excl_1_sim"] = (res["sim_lo"] > 1) | (res["sim_up"] < 1)
res.to_csv(f"{OUT}/ns4_beta1.csv", index=False)

mk = pd.DataFrame([res.iloc[int(np.abs(HRS - h).argmin())] for h in MARKS])
mk.to_csv(f"{OUT}/ns4_marks.csv", index=False)
print("\nStundenmarken (Band VORLAEUFIG, Sandwich):")
print(mk[["hours", "beta_1", "se_cluster", "sim_lo", "sim_up"]].to_string(
    index=False, float_format=lambda v: f"{v:8.3f}"))
print(f"\nGitterpunkte <= {HMAX:.0f} h, an denen das simultane Band 1 "
      f"ausschliesst: {int(res.loc[m, 'excl_1_sim'].sum())} von {int(m.sum())}")

# ---------------------------------- 4) Deskriptive RMSE-Kurve der Preise
p = df["PRef"].to_numpy() + exog
sq = (df["Match"].to_numpy() - p) ** 2
edges = np.exp(np.linspace(np.log(HRS.min()), np.log(HMAX), NBINS + 1))
idx = np.digitize(df["HoursToKick"].to_numpy(), edges) - 1
ok = (idx >= 0) & (idx < NBINS)

rows = []
for i in range(NBINS):
    s = sq[ok & (idx == i)]
    if len(s) < 500:
        continue
    rows.append({"h_lo": edges[i], "h_up": edges[i + 1],
                 "h_mid": np.sqrt(edges[i] * edges[i + 1]),
                 "n": len(s), "brier": s.mean(), "rmse": np.sqrt(s.mean())})
rm = pd.DataFrame(rows)
rm.to_csv(f"{OUT}/ns4_rmse_bins.csv", index=False)
print(f"\nRMSE-Bins: {len(rm)} besetzt, "
      f"RMSE {rm['rmse'].min():.4f} bis {rm['rmse'].max():.4f}")
print(rm[["h_mid", "n", "rmse"]].to_string(
    index=False, float_format=lambda v: f"{v:.4f}"))

print(f"\nDateien: {OUT}/ns4_beta1.csv, ns4_marks.csv, ns4_rmse_bins.csv")
