#!/usr/bin/env python3
"""Stufenreihe M_a bis M_c der Hauptspezifikation + Diagnostik + k-Sensitivität.

Rein diagnostisch. M_d (zusätzlich Match-Random-Intercept) ist auf dieser
Maschine NICHT rechenbar -- siehe `_feasibility.py`: 20.741 Matchup-Level
ergeben p ~ 20.800, mgcv behandelt Random Effects dicht
(`?random.effects`: "does not exploit the sparsity"), die gemessene
Laufzeitskalierung ist ~p^3 (~25 h) und der Speicherbedarf >= 17 GB gegen
11,4 GB verfügbar. Diese Stufen haben p <= 65 und laufen in Sekunden.

  M_a  ohne REs
  M_b  + Bookmaker-Intercept        s(Bookies, bs = "re")
  M_c  + Bookmaker-Slope auf Exog   s(Exog, Bookies, bs = "re")

Die beiden REs sind in mgcv per Konstruktion UNABHÄNGIG (i.i.d. je Term,
Ridge-Penalty); eine Korrelation zwischen Intercept und Slope wie in der
lme4-Struktur aus R1-ii ist mit `bs="re"` nicht darstellbar.

Spezifikation: Endog = Match - p_ref, Exog = p(t) - p_ref, p_ref = erster
echt beobachteter normalisierter Preis der EIGENEN Serie, X = log(Stunden
bis Anpfiff), Kovariaten TsDur + 4 Competition-Dummies (NumOddsMvt bewusst
NICHT), ungewichtet, k = 6, bs = "cr", fREML, discrete = TRUE.

beta_1 wird auf drei Achsen berichtet:
  - Gitter gleichmäßig in log(Stunden)  -> Kurve für den Plot
  - Quantile von X                      -> beobachtungsgewichtetes Mittel,
                                           das Gegenstück zum gepoolten
                                           beta_1 = 1,006 des bisherigen
                                           Checks (achsenunabhängig)
  - feste Stundenmarken                 -> ablesbare Stützstellen
Zusätzlich die empirische Zuordnung Stunden -> mittlere relative Position
im Matchup-Fenster, damit der Plot eine zweite, zur Baseline vergleichbare
x-Achse bekommen kann.
"""

import resource
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
FRAME = f"{tempfile.gettempdir()}/pfd_mainspec_frame.parquet"
LIMIT_GB = 8
COVS = ["TsDur", "Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
        "Compet_WTA"]
NGRID = 100
NQ = 500                                 # Quantilstützstellen für das Mittel
MARKS = [24.0, 12.0, 6.0, 3.0, 1.0, 0.25]

resource.setrlimit(resource.RLIMIT_AS, (LIMIT_GB << 30, LIMIT_GB << 30))
pd.set_option("display.width", 220)
ro.r("library(mgcv)")


def build():
    """Frame der Hauptspezifikation (identisch zu `_feasibility.py`)."""
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
    d = d[d["HoursToKick"] > 0]                    # Updates nach Anpfiff raus
    d = d[d.groupby("GroupId")["OddsMvt"].transform("std") > 0]
    d = d[d["NumOddsMvt"] < 20]

    d = d.sort_values(["GroupId", "Update"])
    d["PRef"] = d.groupby("GroupId", sort=False)["OddsMvt"].transform("first")
    d["Endog"] = d["Match"] - d["PRef"]
    d["Exog"] = d["OddsMvt"] - d["PRef"]
    d["ObsIdx"] = d.groupby("GroupId").cumcount()
    d = d[d["ObsIdx"] > 0]                         # Referenzbeobachtung raus

    d["X"] = np.log(d["HoursToKick"])
    keep = ["GroupId", "Matchup", "Bookies", "X", "HoursToKick", "Endog",
            "Exog", "NumOddsMvt"] + COVS
    d = d[keep].reset_index(drop=True)
    d.to_parquet(FRAME)
    return d


try:
    df = pd.read_parquet(FRAME)
except (FileNotFoundError, OSError):
    df = build()
df["Bookies"] = df["Bookies"].astype(str)
print(f"Frame: {len(df):,d} Zeilen, {df['GroupId'].nunique():,d} Serien, "
      f"{df['Matchup'].nunique():,d} Matchups", flush=True)

# relative Position im Matchup-Fenster: die Fenstergrenzen sind max/min der
# Stunden bis Anpfiff innerhalb des Matchups (= TsStart/TsEnd der Baseline)
hmax = df.groupby("Matchup")["HoursToKick"].transform("max")
hmin = df.groupby("Matchup")["HoursToKick"].transform("min")
df["RelPos"] = np.where(hmax > hmin, (hmax - df["HoursToKick"])
                        / (hmax - hmin), np.nan)

h_lo, h_hi = df["HoursToKick"].quantile([0.01, 0.99])
HRS = np.exp(np.linspace(np.log(h_hi), np.log(h_lo), NGRID))   # fern -> nah
HQ = np.exp(np.quantile(df["X"], np.linspace(0.001, 0.999, NQ)))
print(f"Gitter: {h_hi:.2f} h bis {h_lo:.3f} h vor Anpfiff "
      f"(Fensterende = {h_lo:.3f} h)\n", flush=True)

BASE = ("Endog ~ s(X, k = kk, bs = 'cr') + s(X, by = Exog, k = kk, bs = 'cr')"
        " + " + " + ".join(COVS))
SPECS = [
    ("M_a ohne REs", BASE),
    ("M_b + Bookmaker-Intercept", BASE + " + s(Bookies, bs = 're')"),
    ("M_c + Bookmaker-Slope", BASE + " + s(Bookies, bs = 're')"
     " + s(Exog, Bookies, bs = 're')"),
]


def fit_model(fml, k):
    """bam-Fit; `m` bleibt für `beta1()` in R liegen."""
    cols = ["Endog", "Exog", "X", "Bookies"] + COVS
    dd = df[cols]
    dd = dd[np.isfinite(dd[[c for c in cols if c != "Bookies"]]).all(axis=1)]
    with localconverter(ro.default_converter + pandas2ri.converter):
        ro.globalenv["d"] = dd
    ro.globalenv["kk"] = k
    ro.globalenv["fml"] = fml
    t0 = time.time()
    ro.r("""
    d$Bookies <- factor(d$Bookies)
    m <- bam(as.formula(fml), data = d, method = "fREML", discrete = TRUE,
             nthreads = 4)
    st <- as.data.frame(summary(m)$s.table); st$term <- rownames(st)
    # Varianzkomponenten: fuer ein re-Smooth ist die Strafe lambda * I, also
    # sigma^2_re = scale / lambda. gam.vcomp() scheitert auf diesen bam-Fits
    # ("differing number of rows"), daher direkt aus sp und scale. Hier hat
    # jedes Smooth genau eine Strafe (cr und re sind einfach bestraft), sonst
    # greift der Fallback auf die sp-Namen.
    vc <- data.frame(term = sapply(m$smooth, function(s) s$label),
                     is_re = sapply(m$smooth,
                                    function(s) inherits(s, "random.effect")))
    if (nrow(vc) != length(m$sp))
        vc <- data.frame(term = names(m$sp), is_re = NA)
    vc$lambda <- as.numeric(m$sp)
    # sig2, NICHT scale: `m$scale` matcht per Teilstring auf `scale.estimated`
    # (TRUE) und ergibt still eine Residualvarianz von exakt 1.
    vc$sd <- sqrt(m$sig2 / vc$lambda)
    scl <- m$sig2; np <- length(coef(m))
    """)
    secs = time.time() - t0
    with localconverter(ro.default_converter + pandas2ri.converter):
        st = ro.conversion.get_conversion().rpy2py(ro.globalenv["st"])
        vc = ro.conversion.get_conversion().rpy2py(ro.globalenv["vc"])
    return st, vc, float(ro.globalenv["scl"][0]), int(ro.globalenv["np"][0]), \
        secs


def beta1(hours):
    """beta_1 auf den gegebenen Stunden vor Anpfiff, REs auf Populationsmittel
    (Random-Effect-Spalten der Kontrastmatrix auf 0)."""
    with localconverter(ro.default_converter + numpy2ri.converter):
        ro.globalenv["hrs"] = np.asarray(hours, float)
    ro.r("""
    g <- data.frame(X = log(hrs), Bookies = levels(d$Bookies)[1])
    for (cv in c("TsDur", "Compet_Challenger_Men", "Compet_ITF_Men",
                 "Compet_Misc", "Compet_WTA")) g[[cv]] <- 0
    Xp <- predict(m, transform(g, Exog = 1), type = "lpmatrix") -
          predict(m, transform(g, Exog = 0), type = "lpmatrix")
    rec <- unlist(lapply(m$smooth, function(s)
        if (inherits(s, "random.effect")) s$first.para:s$last.para else NULL))
    if (!is.null(rec)) Xp[, rec] <- 0
    out <- data.frame(hours = hrs, beta_1 = as.vector(Xp %*% coef(m)),
                      se = sqrt(pmax(0, rowSums((Xp %*% vcov(m)) * Xp))))
    """)
    with localconverter(ro.default_converter + pandas2ri.converter):
        return ro.conversion.get_conversion().rpy2py(ro.globalenv["out"])


print("3) STUFENREIHE")
curves, rows = [], []
for label, fml in SPECS:
    st, vc, scale, p, secs = fit_model(fml, 6)
    o, oq = beta1(HRS), beta1(HQ)
    curves.append(o.assign(model=label))
    rows.append({"model": label, "p": p, "secs": secs,
                 "beta1_grid_mean": o["beta_1"].mean(),
                 "beta1_obs_mean": oq["beta_1"].mean(),
                 "beta1_far": o["beta_1"].iloc[0],
                 "beta1_end": o["beta_1"].iloc[-1],
                 "se_end": o["se"].iloc[-1], "resid_sd": np.sqrt(scale)})
    print(f"\n  {label:<28s} p={p:>4,d}  {secs:>6.1f} s")
    print(f"    beta_1  Gittermittel {o['beta_1'].mean():.3f}   "
          f"beobachtungsgewichtet {oq['beta_1'].mean():.3f}")
    print(f"            fern ({o['hours'].iloc[0]:.1f} h) "
          f"{o['beta_1'].iloc[0]:.3f}   Ende ({o['hours'].iloc[-1]:.3f} h) "
          f"{o['beta_1'].iloc[-1]:.3f} (SE {o['se'].iloc[-1]:.3f})")
    print("    edf/F:")
    print("      " + st.set_index("term").round(3).to_string()
          .replace("\n", "\n      "))
    print("    Varianzkomponenten (sd; is_re = echte Varianzkomponente):")
    print("      " + vc.round(5).to_string(index=False)
          .replace("\n", "\n      "))
    print(f"    Residual-sd {np.sqrt(scale):.5f}", flush=True)

pd.concat(curves, ignore_index=True).to_csv(
    f"{OUT}/ladder_beta1.csv", index=False)
lad = pd.DataFrame(rows)
lad.to_csv(f"{OUT}/ladder_summary.csv", index=False)
print("\n" + lad.to_string(index=False, float_format=lambda v: f"{v:,.4f}"))

# ---- Stundenmarken + Zuordnung zur relativen Position (fuer die 2. Achse)
mk = beta1(MARKS)
mk["rel_pos"] = [df.loc[(df["HoursToKick"] > h * 0.9)
                        & (df["HoursToKick"] < h * 1.1), "RelPos"].mean()
                 for h in MARKS]
mk.to_csv(f"{OUT}/ladder_marks.csv", index=False)
print("\n  Stundenmarken (M_c) mit mittlerer relativer Fensterposition:")
print(mk.to_string(index=False, float_format=lambda v: f"{v:,.4f}"))

# ------------------------------------------------ Diagnostik auf M_c
print("\n  gam.check() und concurvity(full = FALSE) fuer M_c:")
ro.r("""
ck <- capture.output(gam.check(m))
cv <- tryCatch(round(concurvity(m, full = FALSE)$estimate, 3),
               error = function(e) paste("FEHLER:", e$message))
""")
print("    " + "\n    ".join(list(ro.r("ck"))))
print("    concurvity(full = FALSE), estimate:")
print("      " + str(ro.r("paste(capture.output(print(cv)), collapse='\n')")[0])
      .replace("\n", "\n      "))

print("\n4) k-SENSITIVITÄT auf M_c (Niveau-Invarianz erwartet)")
ks = []
for k in (6, 10, 20):
    st, vc, scale, p, secs = fit_model(SPECS[-1][1], k)
    o, oq = beta1(HRS), beta1(HQ)
    ks.append({"k": k, "p": p, "secs": secs,
               "beta1_grid_mean": o["beta_1"].mean(),
               "beta1_obs_mean": oq["beta_1"].mean(),
               "beta1_far": o["beta_1"].iloc[0],
               "beta1_end": o["beta_1"].iloc[-1]})
    print(f"  k={k:<3d} p={p:>4,d}  {secs:>6.1f} s  Gittermittel "
          f"{o['beta_1'].mean():.3f}  beob.gew. {oq['beta_1'].mean():.3f}  "
          f"Ende {o['beta_1'].iloc[-1]:.3f}", flush=True)
pd.DataFrame(ks).to_csv(f"{OUT}/ladder_k_sensitivity.csv", index=False)

print(f"\ngeschrieben: {OUT}/ladder_{{beta1,summary,marks,k_sensitivity}}.csv")
