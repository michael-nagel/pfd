#!/usr/bin/env python3
"""Hauptspezifikation über lme4: Regressionsspline-Basis + crossed REs.

mgcv/bam kann den Match-Intercept nicht tragen (20.741 Level, dichte
Behandlung, ~25 h und >= 17 GB -- siehe `_feasibility.py`). lme4 nutzt die
Sparsity der Random Effects und erlaubt zusätzlich KORRELIERTE
Intercept-Slope-REs, wie in der R1-ii-Arbeit (`bookies_cov`).

Preis: die Spline-Basis ist fest (Regressionsspline mit k Knoten) statt
penalisiert. Die k-Sensitivität aus `_ladder.py` zeigt Niveau-Invarianz
(beobachtungsgewichtetes beta_1 = 0,988 für k = 6, 10 und 20), der Preis
ist also gering.

Ablauf:
  1) Basis für X = log(Stunden bis Anpfiff), k, bs = "cr", über mgcvs
     smoothCon -- identisch für Haupteffekt und Exog-Interaktion
  2) GATE: lme4-Äquivalent zu M_c (ohne Matchup) gegen die mgcv-Werte
     (beta_1 Mittel 0,9881, Rand 0,8129, sd_Bookies 0,00325,
     sd_Slope 0,07693, Residual 0,45883). Bei größerer Abweichung ANHALTEN.
  3) Hauptspezifikation: + (1 | Matchup), REML = FALSE
  4) k-Sensitivität (6, 10, 20) für die Hauptspezifikation

Rein diagnostisch, nichts an der Produktions-Pipeline.
"""

import resource
import sys
import tempfile
import threading
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
LIMIT_GB = 9
COVS = ["TsDur", "Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
        "Compet_WTA"]
NGRID, NQ = 100, 500
MARKS = [24.0, 12.0, 6.0, 3.0, 1.0, 0.25]

# mgcv-M_c als Referenz für das Gate
REF = {"beta1_obs_mean": 0.9881, "beta1_end": 0.8129,
       "sd_bookies_int": 0.00325, "sd_bookies_slope": 0.07693,
       "sd_resid": 0.45883}
GATE_BETA = 0.05                        # zulässige Abweichung in beta_1
GATE_SD = 2.0                           # zulässiger Faktor bei den sd

resource.setrlimit(resource.RLIMIT_AS, (LIMIT_GB << 30, LIMIT_GB << 30))
pd.set_option("display.width", 220)
ro.r("library(mgcv); library(lme4)")

PAGE = resource.getpagesize()


def rss_gb():
    """Aktueller Resident Set in GB (nicht der Prozess-Höchststand)."""
    with open("/proc/self/statm") as f:
        return int(f.read().split()[1]) * PAGE / 1024**3


class Watch:
    """Peak des AKTUELLEN RSS über die Dauer eines Fits."""

    def __init__(self):
        self.peak, self.stop = 0.0, False

    def __enter__(self):
        self.t0 = time.time()
        self.th = threading.Thread(target=self.run, daemon=True)
        self.th.start()
        return self

    def run(self):
        while not self.stop:
            self.peak = max(self.peak, rss_gb())
            time.sleep(0.25)

    def __exit__(self, *a):
        self.stop = True
        self.th.join(timeout=2)
        self.peak = max(self.peak, rss_gb())
        self.secs = time.time() - self.t0


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
            "Exog", "NumOddsMvt"] + COVS
    d = d[keep].reset_index(drop=True)
    d.to_parquet(FRAME)
    return d


try:
    df = pd.read_parquet(FRAME)
except (FileNotFoundError, OSError):
    df = build()
df["Bookies"] = df["Bookies"].astype(str)
df["Matchup"] = df["Matchup"].astype(str)
print(f"Frame: {len(df):,d} Zeilen, {df['GroupId'].nunique():,d} Serien, "
      f"{df['Matchup'].nunique():,d} Matchups, "
      f"{df['Bookies'].nunique()} Bookmaker", flush=True)

h_lo, h_hi = df["HoursToKick"].quantile([0.01, 0.99])
HRS = np.exp(np.linspace(np.log(h_hi), np.log(h_lo), NGRID))
HQ = np.exp(np.quantile(df["X"], np.linspace(0.001, 0.999, NQ)))

with localconverter(ro.default_converter + pandas2ri.converter):
    ro.globalenv["d0"] = df[["Endog", "Exog", "X", "Bookies", "Matchup"]
                            + COVS]


def make_basis(k):
    """Cubic-Regression-Spline-Basis für X, k Knoten, Zentrierungsconstraint
    absorbiert. Dieselben Spalten tragen Haupteffekt und Exog-Interaktion."""
    ro.globalenv["kk"] = k
    ro.r("""
    sm <- smoothCon(s(X, k = kk, bs = "cr"), data = d0,
                    absorb.cons = TRUE)[[1]]
    B  <- PredictMat(sm, d0)
    nb <- ncol(B)
    d  <- d0
    for (j in seq_len(nb)) {
        d[[paste0("b", j)]]  <- B[, j]
        d[[paste0("eb", j)]] <- B[, j] * d0$Exog
    }
    d$Bookies <- factor(d$Bookies); d$Matchup <- factor(d$Matchup)
    """)
    return int(ro.globalenv["nb"][0])


def fit_lmer(with_match, nb, label):
    """lmer-Fit; Warnungen werden vollständig eingesammelt."""
    fe = (" + ".join(f"b{j}" for j in range(1, nb + 1)) + " + Exog + "
          + " + ".join(f"eb{j}" for j in range(1, nb + 1)) + " + "
          + " + ".join(COVS))
    re = "(1 + Exog | Bookies)" + (" + (1 | Matchup)" if with_match else "")
    ro.globalenv["fml"] = f"Endog ~ {fe} + {re}"
    print(f"\n  {label}\n    {ro.globalenv['fml'][0]}", flush=True)
    with Watch() as w:
        ro.r("""
        msgs <- character(0)
        m <- withCallingHandlers(
            lmer(as.formula(fml), data = d, REML = FALSE),
            warning = function(x) {msgs <<- c(msgs, conditionMessage(x))
                                   invokeRestart("muffleWarning")})
        cnv <- m@optinfo$conv$lme4$messages
        if (is.null(cnv)) cnv <- "keine"
        vc <- as.data.frame(VarCorr(m))
        fx <- fixef(m); Vf <- as.matrix(vcov(m))
        """)
    with localconverter(ro.default_converter + pandas2ri.converter):
        vc = ro.conversion.get_conversion().rpy2py(ro.globalenv["vc"])
    msgs = list(ro.globalenv["msgs"])
    cnv = list(ro.globalenv["cnv"])
    print(f"    {w.secs:>7.1f} s   Peak-RSS {w.peak:.2f} GB", flush=True)
    print(f"    Konvergenz: {'; '.join(cnv)}")
    if msgs:
        for s in msgs:
            print(f"    WARNUNG: {s.strip()}")
    else:
        print("    Warnungen: keine")
    print("    Varianzkomponenten:")
    print("      " + vc.round(6).to_string(index=False)
          .replace("\n", "\n      "), flush=True)
    return vc, w.secs, w.peak, cnv, msgs


def beta1(hours, nb):
    """beta_1(X) = coef(Exog) + sum_j coef(eb_j) * B_j(X), mit SE aus der
    Fixed-Effects-Kovarianz."""
    with localconverter(ro.default_converter + numpy2ri.converter):
        ro.globalenv["hrs"] = np.asarray(hours, float)
    ro.r("""
    Bg <- PredictMat(sm, data.frame(X = log(hrs)))
    cvec <- matrix(0, nrow = length(hrs), ncol = length(fx))
    colnames(cvec) <- names(fx)
    cvec[, "Exog"] <- 1
    for (j in seq_len(ncol(Bg))) cvec[, paste0("eb", j)] <- Bg[, j]
    out <- data.frame(hours = hrs, beta_1 = as.vector(cvec %*% fx),
                      se = sqrt(pmax(0, rowSums((cvec %*% Vf) * cvec))))
    """)
    with localconverter(ro.default_converter + pandas2ri.converter):
        return ro.conversion.get_conversion().rpy2py(ro.globalenv["out"])


def sds(vc):
    """sd von Bookmaker-Intercept, Bookmaker-Slope, Kovarianz, Match, Rest.

    rpy2 liefert Rs NA_character_ als LITERALEN String "NA_character_", nicht
    als NaN -- `isna()` greift hier also nicht."""
    def isna(col):
        return col.isna() | (col.astype(str) == "NA_character_")

    def row(grp, v1=None, v2=None):
        s = vc[vc["grp"] == grp]
        s = s[isna(s["var1"]) if v1 is None else s["var1"] == v1]
        s = s[isna(s["var2"]) if v2 is None else s["var2"] == v2]
        return s

    def sd(grp, v1=None, v2=None):
        s = row(grp, v1, v2)
        return float(s["sdcor"].iloc[0]) if len(s) else np.nan

    cov = row("Bookies", "(Intercept)", "Exog")
    return {
        "sd_bookies_int": sd("Bookies", "(Intercept)"),
        "sd_bookies_slope": sd("Bookies", "Exog"),
        "cor_bookies": sd("Bookies", "(Intercept)", "Exog"),
        "cov_bookies": float(cov["vcov"].iloc[0]) if len(cov) else np.nan,
        "sd_matchup": sd("Matchup", "(Intercept)"),
        "sd_resid": sd("Residual"),
    }


# ------------------------------------------------------------------ 2) GATE
print(f"\nRLIMIT_AS = {LIMIT_GB} GB\n")
print("=" * 78 + "\n2) GATE: lme4-Äquivalent zu mgcv-M_c (ohne Matchup)\n"
      + "=" * 78)
nb = make_basis(6)
print(f"  Basisspalten: {nb} (k = 6, cr, Constraint absorbiert)")
vc_g, secs_g, peak_g, cnv_g, msg_g = fit_lmer(False, nb, "GATE M_c(lme4)")
og, oqg = beta1(HRS, nb), beta1(HQ, nb)
sg = sds(vc_g)

got = {"beta1_obs_mean": oqg["beta_1"].mean(),
       "beta1_end": og["beta_1"].iloc[-1],
       "sd_bookies_int": sg["sd_bookies_int"],
       "sd_bookies_slope": sg["sd_bookies_slope"],
       "sd_resid": sg["sd_resid"]}

print("\n  Vergleich gegen mgcv-M_c:")
print(f"    {'Größe':<20s} {'mgcv':>10s} {'lme4':>10s} {'Diff':>10s}")
fail = []
for kk, ref in REF.items():
    g = got[kk]
    print(f"    {kk:<20s} {ref:>10.5f} {g:>10.5f} {g - ref:>+10.5f}")
    if kk.startswith("beta1"):
        if abs(g - ref) > GATE_BETA:
            fail.append(f"{kk}: |{g - ref:+.4f}| > {GATE_BETA}")
    elif not (1 / GATE_SD <= g / ref <= GATE_SD):
        fail.append(f"{kk}: Faktor {g / ref:.2f} ausserhalb "
                    f"[{1 / GATE_SD:.2f}, {GATE_SD:.2f}]")

pd.DataFrame([{**got, "secs": secs_g, "peak_gb": peak_g,
               "conv": "; ".join(cnv_g)}]).to_csv(
    f"{OUT}/lme4_gate.csv", index=False)

if fail:
    print("\n  GATE NICHT BESTANDEN -- angehalten, kein Match-RE gefittet:")
    for f in fail:
        print(f"    {f}")
    sys.exit(1)
print("\n  GATE bestanden.", flush=True)

# --------------------------------------------------- 3) Hauptspezifikation
print("\n" + "=" * 78 + "\n3) HAUPTSPEZIFIKATION: + (1 | Matchup), REML = FALSE"
      "\n" + "=" * 78)
vc_m, secs_m, peak_m, cnv_m, msg_m = fit_lmer(True, nb, "Hauptspezifikation")
om, oqm, mk = beta1(HRS, nb), beta1(HQ, nb), beta1(MARKS, nb)
sm_ = sds(vc_m)

print(f"\n  beta_1  beobachtungsgewichtet {oqm['beta_1'].mean():.4f}"
      f"   Gittermittel {om['beta_1'].mean():.4f}")
print(f"          fern ({om['hours'].iloc[0]:.1f} h) "
      f"{om['beta_1'].iloc[0]:.4f}   Ende ({om['hours'].iloc[-1]:.3f} h) "
      f"{om['beta_1'].iloc[-1]:.4f} (SE {om['se'].iloc[-1]:.4f})")
print("\n  Stundenmarken:")
print(mk.to_string(index=False, float_format=lambda v: f"{v:,.4f}"))

om.assign(model="Hauptspezifikation").to_csv(
    f"{OUT}/lme4_beta1.csv", index=False)
mk.to_csv(f"{OUT}/lme4_marks.csv", index=False)
vc_m.to_csv(f"{OUT}/lme4_varcomp.csv", index=False)
pd.DataFrame([{**sm_, "beta1_obs_mean": oqm["beta_1"].mean(),
               "beta1_end": om["beta_1"].iloc[-1],
               "se_end": om["se"].iloc[-1], "secs": secs_m,
               "peak_gb": peak_m, "conv": "; ".join(cnv_m),
               "warnings": " | ".join(msg_m)}]).to_csv(
    f"{OUT}/lme4_main_summary.csv", index=False)

# ------------------------------------------------------ 4) k-Sensitivität
print("\n" + "=" * 78 + "\n4) k-SENSITIVITÄT der Hauptspezifikation\n"
      + "=" * 78)
ks = []
for k in (6, 10, 20):
    nbk = make_basis(k)
    vck, sk, pk, ck, mgk = fit_lmer(True, nbk, f"Hauptspezifikation k={k}")
    ok, oqk = beta1(HRS, nbk), beta1(HQ, nbk)
    s = sds(vck)
    ks.append({"k": k, "nb": nbk, "secs": sk, "peak_gb": pk,
               "beta1_obs_mean": oqk["beta_1"].mean(),
               "beta1_grid_mean": ok["beta_1"].mean(),
               "beta1_end": ok["beta_1"].iloc[-1],
               "sd_matchup": s["sd_matchup"], "conv": "; ".join(ck)})
    print(f"    k={k:<3d} beob.gew. {oqk['beta_1'].mean():.4f}   "
          f"Ende {ok['beta_1'].iloc[-1]:.4f}", flush=True)
pd.DataFrame(ks).to_csv(f"{OUT}/lme4_k_sensitivity.csv", index=False)
print("\n" + pd.DataFrame(ks).to_string(
    index=False, float_format=lambda v: f"{v:,.4f}"))

print(f"\ngeschrieben: {OUT}/lme4_{{gate,beta1,marks,varcomp,main_summary,"
      f"k_sensitivity}}.csv")
