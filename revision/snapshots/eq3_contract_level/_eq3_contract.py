#!/usr/bin/env python3
"""Eq. 3 auf Kontraktebene (R2-C1, berührt R3-2/R3-5).

Referee R2-C1: die bestehende Fassung (Tabelle 6) regressiert Gewinnraten je
Preisänderungs-Bin auf die mittlere Preisänderung des Bins. Gefordert ist eine
Spezifikation auf Kontraktebene, die für den Opening-Preis kontrolliert --
bei effizientem Opening sollte die Preisänderung dann keine eigenständige
Information mehr tragen.

Hauptspezifikation (lineares Wahrscheinlichkeitsmodell):

    Match = eta_0 + eta_1 * OpnOdds + eta_2 * DltOpnCls
            + TsDur + Compet_* + (1 + DltOpnCls | Bookies)

LPM bewusst gewählt: die Vorhersagen des Papers stehen in
Wahrscheinlichkeitseinheiten (eta_0 = 0,5, eta_1 > 0), und bei effizienten
Opening-Preisen ist eta_1 = 1 ein direkt testbarer Punktwert. Der Logit-Check
unten sichert ab, dass der Befund nicht an der Linearitätsannahme hängt.

Rein diagnostisch, kein Eingriff in die Produktions-Pipeline.
"""

import sys
import tempfile
import time

import numpy as np
import pandas as pd
import rpy2.robjects as ro
from omegaconf import OmegaConf
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter
from scipy import stats

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

OUT = "revision/snapshots/eq3_contract_level"
FRAME = f"{tempfile.gettempdir()}/pfd_eq3_frame.parquet"
COMPETS = ["Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
           "Compet_WTA"]

pd.set_option("display.width", 220)
ro.r("library(lme4)")


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
    keep = ["GroupId", "Matchup", "Bookies", "Match", "OpnOdds", "ClsOdds",
            "DltOpnCls", "RtrnOpnCls", "TsDur"] + COMPETS
    d = d[keep].reset_index(drop=True)
    d.to_parquet(FRAME)
    return d


try:
    d_all = pd.read_parquet(FRAME)
    print(f"Frame aus Cache: {len(d_all):,d} Kontrakte")
except (FileNotFoundError, OSError):
    d_all = build()
    print(f"Frame neu gebaut: {len(d_all):,d} Kontrakte")

# Produktions-df_oc filtert Serien ohne Preisbewegung heraus; das ist eine
# Selektion und wird unten als Sensitivität mitgeführt.
d = d_all[d_all["RtrnOpnCls"].abs() > 0].reset_index(drop=True)
print(f"  ohne Preisbewegung entfernt: {len(d_all) - len(d):,d} "
      f"({(1 - len(d) / len(d_all)) * 100:.1f} %)  ->  {len(d):,d} Kontrakte")
print(f"  Matchups {d['Matchup'].nunique():,d}   "
      f"Bookmaker {d['Bookies'].nunique()}")
print(f"  Match          Mittel {d['Match'].mean():.4f}")
print(f"  OpnOdds        Mittel {d['OpnOdds'].mean():.4f}   Spanne "
      f"{d['OpnOdds'].min():.4f}-{d['OpnOdds'].max():.4f}")
print(f"  DltOpnCls      Mittel {d['DltOpnCls'].mean():+.5f}   sd "
      f"{d['DltOpnCls'].std():.5f}")

# ------------------------------- 1) Wäre ein Match-RE identifiziert?
block("1) IST EIN MATCH-RANDOM-INTERCEPT HIER IDENTIFIZIERT?")
grand = d["Match"].var(ddof=0)
btw = d.groupby("Matchup")["Match"].transform("mean").var(ddof=0)
print(f"  var(Match) gesamt   {grand:.6f}")
print(f"  var between Matchup {btw:.6f}   Anteil {btw / grand * 100:.2f} %")
print(f"  var within  Matchup {grand - btw:.6e}")
nun = int((d.groupby("Matchup")["Match"].nunique() > 1).sum())
print(f"  Matchups mit mehr als einem Match-Wert: {nun} von "
      f"{d['Matchup'].nunique():,d}")
print("\n  -> Match ist der Ausgang des Spiels und damit per Konstruktion\n"
      "     KONSTANT über die Bookmaker eines Matchups. Ein Match-RE würde\n"
      "     die abhängige Variable vollständig absorbieren.")
pd.DataFrame([{"var_total": grand, "var_between": btw,
               "var_within": grand - btw, "share_between": btw / grand,
               "matchups_multivalued": nun}]).to_csv(
    f"{OUT}/match_anova.csv", index=False)

# --------------------------------------------------- 2) Stufenreihe
block("2) STUFENREIHE S1-S4")
X_COLS = {
    "S1": ["DltOpnCls"],
    "S2": ["OpnOdds", "DltOpnCls"],
    "S3": ["OpnOdds", "DltOpnCls", "TsDur"] + COMPETS,
    "S4": ["OpnOdds", "DltOpnCls", "TsDur"] + COMPETS,
}
LAB = {"S1": "nur Preisänderung", "S2": "+ OpnOdds (Referee-Spez.)",
       "S3": "+ Kovariaten", "S4": "+ (1 + DltOpnCls | Bookies)"}

y = d["Match"].to_numpy(float)


def ols(cols):
    X = np.column_stack([np.ones(len(d))] + [d[c].to_numpy(float)
                                             for c in cols])
    XtXi = np.linalg.inv(X.T @ X)
    b = XtXi @ (X.T @ y)
    u = y - X @ b
    s2 = (u @ u) / (len(y) - X.shape[1])
    se = np.sqrt(np.diag(s2 * XtXi))
    r2 = 1 - (u @ u) / ((y - y.mean()) @ (y - y.mean()))
    return X, b, se, u, r2, XtXi


rows = []
for s in ("S1", "S2", "S3"):
    X, b, se, u, r2, _ = ols(X_COLS[s])
    names = ["(Intercept)"] + X_COLS[s]
    rec = {"Stufe": s, "Beschreibung": LAB[s], "R2": r2,
           "eta_0": b[0], "se_eta_0": se[0]}
    for nm in ("OpnOdds", "DltOpnCls"):
        if nm in names:
            i = names.index(nm)
            rec[f"{'eta_1' if nm == 'OpnOdds' else 'eta_2'}"] = b[i]
            rec[f"se_{'eta_1' if nm == 'OpnOdds' else 'eta_2'}"] = se[i]
    rows.append(rec)
    print(f"  {s} {LAB[s]:<30s} R2={r2:.5f}")
    for nm, bi, si in zip(names, b, se, strict=True):
        print(f"      {nm:<24s} {bi:>10.5f}  ({si:.5f})   t={bi / si:>8.2f}")

# S4: lmer
with localconverter(ro.default_converter + pandas2ri.converter):
    ro.globalenv["d"] = d[["Match", "OpnOdds", "DltOpnCls", "TsDur",
                           "Bookies", "Matchup"] + COMPETS]
fe = " + ".join(["OpnOdds", "DltOpnCls", "TsDur"] + COMPETS)
ro.globalenv["fml"] = f"Match ~ {fe} + (1 + DltOpnCls | Bookies)"
t0 = time.time()
ro.r("""
d$Bookies <- factor(d$Bookies); d$Matchup <- factor(d$Matchup)
msgs <- character(0)
m4 <- withCallingHandlers(lmer(as.formula(fml), data = d, REML = FALSE),
    warning = function(x) {msgs <<- c(msgs, conditionMessage(x))
                           invokeRestart("muffleWarning")})
cnv <- m4@optinfo$conv$lme4$messages; if (is.null(cnv)) cnv <- "keine"
fx <- fixef(m4); Vf <- as.matrix(vcov(m4))
vc <- as.data.frame(VarCorr(m4))
r2m <- var(as.vector(model.matrix(m4) %*% fx)) / var(d$Match)
r2c <- var(fitted(m4)) / var(d$Match)
""")
secs = time.time() - t0
with localconverter(ro.default_converter + pandas2ri.converter):
    vc4 = ro.conversion.get_conversion().rpy2py(ro.globalenv["vc"])
fx = np.asarray(ro.globalenv["fx"], float)
Vf = np.asarray(ro.globalenv["Vf"], float)
fx_nm = list(ro.r("names(fx)"))
se4 = np.sqrt(np.diag(Vf))
r2m, r2c = float(ro.globalenv["r2m"][0]), float(ro.globalenv["r2c"][0])
print(f"\n  S4 {LAB['S4']:<30s} {secs:.1f} s   "
      f"R2 marginal {r2m:.5f}  konditional {r2c:.5f}")
print(f"      Konvergenz: {'; '.join(ro.globalenv['cnv'])}")
for nm, bi, si in zip(fx_nm, fx, se4, strict=True):
    print(f"      {nm:<24s} {bi:>10.5f}  ({si:.5f})   t={bi / si:>8.2f}")
print("      Varianzkomponenten:")
print("        " + vc4.round(6).to_string(index=False)
      .replace("\n", "\n        "))
rows.append({"Stufe": "S4", "Beschreibung": LAB["S4"], "R2": r2m,
             "R2_conditional": r2c,
             "eta_0": fx[fx_nm.index("(Intercept)")],
             "se_eta_0": se4[fx_nm.index("(Intercept)")],
             "eta_1": fx[fx_nm.index("OpnOdds")],
             "se_eta_1": se4[fx_nm.index("OpnOdds")],
             "eta_2": fx[fx_nm.index("DltOpnCls")],
             "se_eta_2": se4[fx_nm.index("DltOpnCls")]})
lad = pd.DataFrame(rows)
lad.to_csv(f"{OUT}/ladder.csv", index=False)
vc4.to_csv(f"{OUT}/s4_varcomp.csv", index=False)

# ------------------------------------- 3) Cluster-robuste Inferenz
block("3) CLUSTER-ROBUSTE SEs AUF MATCHUP-EBENE (S4-Fixed-Effects)")
X, b_ols, se_ols, u, _, XtXi = ols(X_COLS["S4"])
names = ["(Intercept)"] + X_COLS["S4"]
print(f"  max |beta(OLS) - beta(lmer)| = "
      f"{np.max(np.abs(b_ols - fx[[fx_nm.index(n) for n in names]])):.6f}")
codes = pd.factorize(d["Matchup"], sort=False)[0]
G, N, K = codes.max() + 1, len(y), X.shape[1]
S = np.zeros((G, K))
np.add.at(S, codes, X * u[:, None])
cf = (G / (G - 1)) * ((N - 1) / (N - K))
V_cr = cf * (XtXi @ (S.T @ S) @ XtXi)
se_cr = np.sqrt(np.diag(V_cr))
print(f"  G = {G:,d} Matchups, N = {N:,d}, K = {K}")
print(f"\n  {'Term':<24s} {'beta':>10s} {'SE Modell':>11s} "
      f"{'SE Cluster':>11s} {'Faktor':>8s}")
inf = []
for i, nm in enumerate(names):
    j = fx_nm.index(nm)
    print(f"  {nm:<24s} {b_ols[i]:>10.5f} {se4[j]:>11.5f} "
          f"{se_cr[i]:>11.5f} {se_cr[i] / se4[j]:>8.2f}")
    inf.append({"term": nm, "beta_ols": b_ols[i], "beta_lmer": fx[j],
                "se_model": se4[j], "se_ols_iid": se_ols[i],
                "se_cluster": se_cr[i], "ratio": se_cr[i] / se4[j]})
pd.DataFrame(inf).to_csv(f"{OUT}/cluster_robust.csv", index=False)

# --------------------------------- 4) Crossed-Variante zur Illustration
block("4) CROSSED-VARIANTE + (1 | Matchup) ZUR ILLUSTRATION")
ro.globalenv["fml2"] = (f"Match ~ {fe} + (1 + DltOpnCls | Bookies) "
                        "+ (1 | Matchup)")
try:
    ro.r("""
    msgs2 <- character(0)
    m5 <- withCallingHandlers(lmer(as.formula(fml2), data = d, REML = FALSE),
        warning = function(x) {msgs2 <<- c(msgs2, conditionMessage(x))
                               invokeRestart("muffleWarning")})
    cnv2 <- m5@optinfo$conv$lme4$messages; if (is.null(cnv2)) cnv2 <- "keine"
    vc2 <- as.data.frame(VarCorr(m5)); fx2 <- fixef(m5)
    """)
    with localconverter(ro.default_converter + pandas2ri.converter):
        vc5 = ro.conversion.get_conversion().rpy2py(ro.globalenv["vc2"])
    print("  Varianzkomponenten:")
    print("    " + vc5.round(8).to_string(index=False)
          .replace("\n", "\n    "))
    print(f"  Konvergenz: {'; '.join(ro.globalenv['cnv2'])}")
    for s in list(ro.globalenv["msgs2"]):
        print(f"  WARNUNG: {s.strip()}")
    vc5.to_csv(f"{OUT}/crossed_varcomp.csv", index=False)
except Exception as e:  # noqa: BLE001
    print(f"  NICHT SCHÄTZBAR: {type(e).__name__}: "
          f"{str(e).strip().splitlines()[-1]}")

# ------------------------------------------- 5) Logit-Robustheitscheck
block("5) LOGIT-KALIBRIERUNG (Nebenrechnung)")
print(f"  OpnOdds in (0,1)? min {d['OpnOdds'].min():.6f}  "
      f"max {d['OpnOdds'].max():.6f}")
ro.globalenv["fml3"] = ("Match ~ logit_opn + DltOpnCls "
                        "+ (1 + DltOpnCls | Bookies)")
t0 = time.time()
ro.r("""
d$logit_opn <- log(d$OpnOdds / (1 - d$OpnOdds))
msgs3 <- character(0)
g1 <- withCallingHandlers(
    glmer(as.formula(fml3), data = d, family = binomial),
    warning = function(x) {msgs3 <<- c(msgs3, conditionMessage(x))
                           invokeRestart("muffleWarning")})
cnv3 <- g1@optinfo$conv$lme4$messages; if (is.null(cnv3)) cnv3 <- "keine"
gfx <- fixef(g1); gse <- sqrt(diag(as.matrix(vcov(g1))))
""")
print(f"  glmer {time.time() - t0:.1f} s   Konvergenz: "
      f"{'; '.join(ro.globalenv['cnv3'])}")
gfx = np.asarray(ro.globalenv["gfx"], float)
gse = np.asarray(ro.globalenv["gse"], float)
gnm = list(ro.r("names(gfx)"))
for s in list(ro.globalenv["msgs3"]):
    print(f"  WARNUNG: {s.strip()}")
lg = []
for nm, bi, si in zip(gnm, gfx, gse, strict=True):
    print(f"    {nm:<14s} {bi:>10.5f}  ({si:.5f})   t={bi / si:>8.2f}")
    lg.append({"term": nm, "coef": bi, "se": si})
pd.DataFrame(lg).to_csv(f"{OUT}/logit_check.csv", index=False)

# ------------------------------------------------ 6) Zentrale Fragen
block("6) ZENTRALE FRAGEN")
i1, i2 = names.index("OpnOdds"), names.index("DltOpnCls")
j1 = fx_nm.index("OpnOdds")
j2 = fx_nm.index("DltOpnCls")


def test(b, se, h0):
    t = (b - h0) / se
    return t, 2 * (1 - stats.norm.cdf(abs(t)))


print("\n  (1) Bleibt eta_2 nach Kontrolle für OpnOdds signifikant?")
for lab, se_ in (("modellbasiert", se4[j2]), ("cluster-robust", se_cr[i2])):
    t, p = test(fx[j2], se_, 0.0)
    print(f"      eta_2 = {fx[j2]:+.5f}   SE {se_:.5f} ({lab})   "
          f"t = {t:+.2f}   p = {p:.3g}")

print("\n  (2) Wie nahe liegt eta_1 an 1?")
for lab, se_ in (("modellbasiert", se4[j1]), ("cluster-robust", se_cr[i1])):
    t0_, p0 = test(fx[j1], se_, 0.0)
    t1_, p1 = test(fx[j1], se_, 1.0)
    print(f"      eta_1 = {fx[j1]:.5f}   SE {se_:.5f} ({lab})")
    print(f"        gegen 0: t = {t0_:+.2f}  p = {p0:.3g}")
    print(f"        gegen 1: t = {t1_:+.2f}  p = {p1:.3g}")

print("\n  (3) Logit-Kalibrierung gegen die Effizienzwerte:")
for nm, h0 in (("logit_opn", 1.0), ("(Intercept)", 0.0)):
    k = gnm.index(nm)
    t, p = test(gfx[k], gse[k], h0)
    print(f"      {nm:<12s} = {gfx[k]:+.5f}  gegen {h0:.0f}: "
          f"t = {t:+.2f}  p = {p:.3g}")

print(f"\ngeschrieben: {OUT}/match_anova.csv, ladder.csv, s4_varcomp.csv, "
      f"cluster_robust.csv, crossed_varcomp.csv, logit_check.csv")
