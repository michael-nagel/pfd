#!/usr/bin/env python3
"""Cluster-robuste Inferenz fuer Eq. 1 und Eq. 2 (R1-ii).

Die Unbiasedness-Regression ist bereits auf CR1-Cluster-Sandwich auf
Matchup-Ebene umgestellt (`continuous_unbiasedness/main_spec/`), Eq. 3 auf
Kontraktebene ebenfalls (`eq3_contract_level/`). Dieses Skript zieht die
beiden verbleibenden Modelle nach:

  Eq. 1  resp_to_info  RtrnClsEnd ~ RtrnOpnCls + TsDur + Compet_*
                       (`fit_gpm_mod.py`)
  Eq. 2  ags_test      Endog ~ Exog + TsDur + Compet_*   ("All"-Zweig)
                       (`fit_rfa_mod.py`)

Vier Schritte je Modell:

  1) GATE   |beta(OLS) - beta(lme4, Bookmaker-only)| gegen die Schwelle 0,01.
            Nur wenn der Punktschaetzer uebereinstimmt, ist der auf dem
            OLS-Residuum gebaute Sandwich auf das Mixed Model uebertragbar.
  2) CR1-Sandwich auf Matchup-Ebene, gegen die modellbasierte SE.
  3) Fixed-Effects-Variante mit Bookmaker-Dummies UND Interaktionen, dazu
     ein gemeinsamer Wald-Test cluster-robust -- der Random Slope faellt mit
     dem Sandwich weg, die Heterogenitaetsfrage bleibt aber offen.
  4) Crossed (1 + x | Bookies) + (1 | Matchup) auf der normalisierten
     Baseline, plus der Anteil der Between-Match-Varianz an der AV. Belegt,
     dass der erste Weg geprueft wurde, bevor auf den Sandwich gewechselt
     wird.

Rein diagnostisch, kein Eingriff in die Produktions-Pipeline.
"""

import sys
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
from pfd.utils import scale_vars  # noqa: E402

OUT = "revision/snapshots/cluster_inference_eq12"
FRAME = ("/mnt/c/Users/micha/AppData/Local/Temp/claude/"
         "C--Users-micha-OneDrive-Michi-pfd/"
         "faf3f6fb-65b6-4ea7-a5e5-08b35a6557d8/scratchpad/"
         "pfd_eq12_frame.parquet")
COMPETS = ["Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
           "Compet_WTA"]
COVS = ["TsDur"] + COMPETS
GATE = 0.01

pd.set_option("display.width", 220)
ro.r("library(lme4)")


def block(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78, flush=True)


def build():
    """df_oc exakt wie `bookmaker_accuracy.py:81-126`, normalisiert."""
    cfg = OmegaConf.create({"estimation": {
        "spec": "BmHome", "normalize": True, "compets": None,
        "bm_quantile": 0.25, "ts_dur": [12, 72], "period": None,
        "resample_freq": "1min", "pctl": 2}})
    raw = pd.read_hdf("data/processed/shaped_data.h5", "df")
    for c in ("Date", "Update"):
        raw[c] = pd.to_datetime(raw[c])
    df, *_ = filter_and_shape_data(raw.copy(), cfg)

    d = df.groupby("GroupId", as_index=False).first()
    d["RtrnClsEnd"] = d["Match"] / d["ClsOdds"] - 1
    d["RtrnOpnCls"] = d["ClsOdds"] / d["OpnOdds"] - 1
    d = d[d["RtrnOpnCls"].abs() > 0].copy()

    # Eq. 2 wie im "All"-Zweig von fit_rfa_mod: FEOpn/FECls je Bookmaker
    # zentriert, Summe standardisiert. Endog nutzt die UNzentrierten Werte.
    d["FEOpn"] = (d["Match"] - d["OpnOdds"]).abs()
    d["FECls"] = (d["Match"] - d["ClsOdds"]).abs()
    d["Endog"] = d["FEOpn"] - d["FECls"]
    fo = d["FEOpn"] - d.groupby("Bookies")["FEOpn"].transform("mean")
    fc = d["FECls"] - d.groupby("Bookies")["FECls"].transform("mean")
    d["Exog"] = scale_vars(X=(fo + fc).to_numpy().reshape(-1, 1))

    keep = (["GroupId", "Matchup", "Bookies", "RtrnClsEnd", "RtrnOpnCls",
             "Endog", "Exog"] + COVS)
    d = d[keep].reset_index(drop=True)
    d.to_parquet(FRAME)
    return d


try:
    d = pd.read_parquet(FRAME)
    print(f"Frame aus Cache: {len(d):,d} Kontrakte")
except (FileNotFoundError, OSError):
    d = build()
    print(f"Frame neu gebaut: {len(d):,d} Kontrakte")

print(f"  Matchups {d['Matchup'].nunique():,d}   "
      f"Bookmaker {d['Bookies'].nunique()}")

codes, uniq = pd.factorize(d["Matchup"], sort=False)
G = len(uniq)
bk = sorted(d["Bookies"].unique())

MODELS = {
    "Eq1_resp_to_info": {"y": "RtrnClsEnd", "x": "RtrnOpnCls",
                         "label": "Eq. 1  close-to-end auf open-to-close"},
    "Eq2_ags_test": {"y": "Endog", "x": "Exog",
                     "label": "Eq. 2  relative Prognosegenauigkeit (All)"},
}


bcodes = pd.factorize(d["Bookies"], sort=True)[0]
GB = bcodes.max() + 1


def sandwich(X, u, XtXi, cl):
    """CR1-Sandwich fuer eine Clusterdimension `cl` (Integer-Codes)."""
    N, K = X.shape
    ng = cl.max() + 1
    S = np.zeros((ng, K))
    np.add.at(S, cl, X * u[:, None])
    return (ng / (ng - 1)) * ((N - 1) / (N - K)) * (XtXi @ (S.T @ S) @ XtXi)


def ols(cols, y):
    """OLS plus CR1-Sandwich auf Matchup-, Bookmaker- und beiden Ebenen."""
    X = np.column_stack([np.ones(len(d))] + [d[c].to_numpy(float)
                                             for c in cols])
    XtXi = np.linalg.inv(X.T @ X)
    b = XtXi @ (X.T @ y)
    u = y - X @ b
    N, K = X.shape
    s2 = (u @ u) / (N - K)
    se_iid = np.sqrt(np.diag(s2 * XtXi))
    V_m = sandwich(X, u, XtXi, codes)
    V_b = sandwich(X, u, XtXi, bcodes)
    # Cameron-Gelbach-Miller: der Schnitt Matchup x Bookies ist die einzelne
    # Beobachtung, die Schnittkomponente also der HC-Sandwich.
    V_i = XtXi @ ((X * u[:, None]).T @ (X * u[:, None])) @ XtXi
    V_2 = V_m + V_b - V_i
    ev = np.linalg.eigvalsh(V_2)
    if ev.min() < 0:                       # nicht positiv semidefinit
        w, Q = np.linalg.eigh(V_2)
        V_2 = Q @ np.diag(np.maximum(w, 0)) @ Q.T
    return (b, se_iid, np.sqrt(np.diag(V_m)), np.sqrt(np.diag(V_b)),
            np.sqrt(np.diag(V_2)), float(ev.min()), V_m,
            ["(Intercept)"] + cols)


def lmer(fml, dat, cols):
    """lme4-Fit; gibt Fixed Effects, SEs und Varianzkomponenten zurueck."""
    with localconverter(ro.default_converter + pandas2ri.converter):
        ro.globalenv["dd"] = dat[cols]
    ro.globalenv["fml"] = fml
    t0 = time.time()
    ro.r("""
    dd$Bookies <- factor(dd$Bookies)
    if ("Matchup" %in% names(dd)) dd$Matchup <- factor(dd$Matchup)
    msgs <- character(0)
    m <- withCallingHandlers(lmer(as.formula(fml), data = dd, REML = FALSE),
        warning = function(w) {msgs <<- c(msgs, conditionMessage(w))
                               invokeRestart("muffleWarning")})
    cnv <- m@optinfo$conv$lme4$messages; if (is.null(cnv)) cnv <- "keine"
    fx <- fixef(m); se <- sqrt(diag(as.matrix(vcov(m))))
    vc <- as.data.frame(VarCorr(m))
    """)
    secs = time.time() - t0
    with localconverter(ro.default_converter + pandas2ri.converter):
        vc = ro.conversion.get_conversion().rpy2py(ro.globalenv["vc"])
    fx = np.asarray(ro.globalenv["fx"], float)
    se = np.asarray(ro.globalenv["se"], float)
    nm = list(ro.r("names(fx)"))
    warn = [w.strip() for w in ro.globalenv["msgs"]]
    return fx, se, nm, vc, secs, list(ro.globalenv["cnv"]), warn


gate_rows, cl_rows, wald_rows, vc_rows, anova_rows = [], [], [], [], []

for key, spec in MODELS.items():
    yname, xname = spec["y"], spec["x"]
    y = d[yname].to_numpy(float)
    cols = [xname] + COVS

    block(f"{spec['label']}   ({yname} ~ {xname} + Kovariaten)")

    # ------------------------------------------------ 4a) Between-Match
    grand = float(np.var(y))
    btw = float(np.var(d.groupby("Matchup")[yname].transform("mean")))
    print(f"  Varianz der AV gesamt {grand:.6f}   between Matchup "
          f"{btw:.6f}   Anteil {btw / grand * 100:.2f} %")
    anova_rows.append({"model": key, "dv": yname, "var_total": grand,
                       "var_between": btw, "share_between": btw / grand})

    # ------------------------------------------------------- 1) GATE
    b_ols, se_iid, se_cl, se_bk, se_2w, ev_min, V, nm_ols = ols(cols, y)
    fml_bm = (f"{yname} ~ {' + '.join(cols)} + (1 + {xname} | Bookies)")
    fx, se_m, nm_m, vc, secs, cnv, warn = lmer(
        fml_bm, d, [yname, xname, "Bookies"] + COVS)
    i_ols, i_m = nm_ols.index(xname), nm_m.index(xname)
    diff = abs(b_ols[i_ols] - fx[i_m])
    ok = diff < GATE
    print(f"\n  1) GATE   lme4 Bookmaker-only, {secs:.1f} s, "
          f"Konvergenz: {'; '.join(cnv)}")
    for w in warn:
        print(f"     WARNUNG: {w}")
    print(f"     beta(OLS)  {b_ols[i_ols]:+.6f}")
    print(f"     beta(lme4) {fx[i_m]:+.6f}")
    print(f"     |Differenz| {diff:.6f}   Schwelle {GATE}   ->  "
          f"{'GATE HAELT' if ok else 'GATE VERLETZT'}")
    max_all = max(abs(b_ols[nm_ols.index(n)] - fx[nm_m.index(n)])
                  for n in nm_ols if n in nm_m)
    print(f"     max |Differenz| ueber alle Fixed Effects: {max_all:.6f}")
    gate_rows.append({"model": key, "term": xname, "beta_ols": b_ols[i_ols],
                      "beta_lmer": fx[i_m], "abs_diff": diff,
                      "threshold": GATE, "gate_holds": ok,
                      "max_abs_diff_all_fe": max_all})

    # -------------------------------------------- 2) CR1 auf Matchup
    print(f"\n  2) CR1-SANDWICH   G(Matchup) = {G:,d}, G(Bookies) = {GB}, "
          f"N = {len(y):,d}, K = {len(cols) + 1}")
    print(f"     {'Term':<24s} {'beta':>11s} {'SE lme4':>10s} "
          f"{'SE iid':>10s} {'SE Match':>10s} {'Faktor':>7s} "
          f"{'SE Bookie':>10s} {'SE 2-fach':>10s}")
    for i, n in enumerate(nm_ols):
        j = nm_m.index(n)
        print(f"     {n:<24s} {b_ols[i]:>11.5f} {se_m[j]:>10.5f} "
              f"{se_iid[i]:>10.5f} {se_cl[i]:>10.5f} "
              f"{se_cl[i] / se_m[j]:>7.2f} {se_bk[i]:>10.5f} "
              f"{se_2w[i]:>10.5f}")
        cl_rows.append({"model": key, "term": n, "beta_ols": b_ols[i],
                        "beta_lmer": fx[j], "se_model_lme4": se_m[j],
                        "se_iid": se_iid[i], "se_cluster_match": se_cl[i],
                        "se_cluster_bookie": se_bk[i],
                        "se_cluster_twoway": se_2w[i],
                        "ratio_vs_model": se_cl[i] / se_m[j],
                        "ratio_vs_iid": se_cl[i] / se_iid[i],
                        "t_match": b_ols[i] / se_cl[i],
                        "t_twoway": b_ols[i] / se_2w[i]})
    t_m = b_ols[i_ols] / se_m[nm_m.index(xname)]
    print(f"     kleinster Eigenwert der 2-fach-Matrix: {ev_min:.3e}"
          f"{'   (auf 0 gesetzt)' if ev_min < 0 else ''}")
    print(f"     Kernkoeffizient {xname}: t lme4 {t_m:+.2f}  ->  "
          f"t Match {b_ols[i_ols] / se_cl[i_ols]:+.2f}  ->  "
          f"t 2-fach {b_ols[i_ols] / se_2w[i_ols]:+.2f}")
    print(f"     Intercept:      t lme4 "
          f"{b_ols[0] / se_m[nm_m.index('(Intercept)')]:+.2f}  ->  "
          f"t Match {b_ols[0] / se_cl[0]:+.2f}  ->  "
          f"t 2-fach {b_ols[0] / se_2w[0]:+.2f}")
    print("     Hinweis: nur 24 Bookmaker-Cluster; die Bookmaker-Dimension"
          " ist entsprechend grob.")

    # ---------------------------- 3) Bookmaker-FE + Wald cluster-robust
    print("\n  3) BOOKMAKER-FIXED-EFFECTS UND WALD-TEST (cluster-robust)")
    dfe = d.copy()
    for b_ in bk[1:]:
        dfe[f"B_{b_}"] = (dfe["Bookies"] == b_).astype(float)
        dfe[f"BX_{b_}"] = dfe[f"B_{b_}"] * dfe[xname]
    dcols = [f"B_{b_}" for b_ in bk[1:]]
    xcols = [f"BX_{b_}" for b_ in bk[1:]]
    Xf = np.column_stack([np.ones(len(dfe))]
                         + [dfe[c].to_numpy(float)
                            for c in cols + dcols + xcols])
    nmf = ["(Intercept)"] + cols + dcols + xcols
    XtXif = np.linalg.inv(Xf.T @ Xf)
    bf = XtXif @ (Xf.T @ y)
    uf = y - Xf @ bf
    Nf, Kf = Xf.shape
    Sf = np.zeros((G, Kf))
    np.add.at(Sf, codes, Xf * uf[:, None])
    Vf = (G / (G - 1)) * ((Nf - 1) / (Nf - Kf)) * (XtXif @ (Sf.T @ Sf) @ XtXif)
    r2_base = 1 - (u_ := y - np.column_stack(
        [np.ones(len(d))] + [d[c].to_numpy(float) for c in cols]) @ b_ols) @ \
        u_ / ((y - y.mean()) @ (y - y.mean()))
    r2_fe = 1 - (uf @ uf) / ((y - y.mean()) @ (y - y.mean()))

    for lab, idx in (("Interaktionen (Steigung)",
                      [nmf.index(c) for c in xcols]),
                     ("Dummies (Niveau)", [nmf.index(c) for c in dcols]),
                     ("beide gemeinsam",
                      [nmf.index(c) for c in dcols + xcols])):
        bb = bf[idx]
        W = float(bb @ np.linalg.solve(Vf[np.ix_(idx, idx)], bb))
        q = len(idx)
        p = 1 - stats.chi2.cdf(W, q)
        print(f"     {lab:<26s} chi2({q}) = {W:8.2f}   p = {p:.4f}")
        wald_rows.append({"model": key, "test": lab, "df": q, "chi2": W,
                          "p": p})
    # bookmakerspezifische Steigungen als Linearkombination
    i_x = nmf.index(xname)
    sl = []
    for b_ in bk:
        c = np.zeros(Kf)
        c[i_x] = 1.0
        if b_ != bk[0]:
            c[nmf.index(f"BX_{b_}")] = 1.0
        est = float(c @ bf)
        sl.append({"model": key, "bookie": b_, "slope": est,
                   "se_cluster": float(np.sqrt(c @ Vf @ c))})
    sldf = pd.DataFrame(sl)
    print(f"     R2 ohne Bookmaker-Terme {r2_base:.6f}  ->  mit "
          f"{r2_fe:.6f}   Zuwachs {r2_fe - r2_base:.6f}")
    print(f"     Steigungen {sldf['slope'].min():.4f} bis "
          f"{sldf['slope'].max():.4f}   sd {sldf['slope'].std():.4f}")
    sldf.to_csv(f"{OUT}/{key}_bookie_fe_slopes.csv", index=False)

    # ------------------------------------------------- 4) crossed
    print("\n  4) CROSSED (1 + x | Bookies) + (1 | Matchup), normalisiert")
    fml_cr = fml_bm + " + (1 | Matchup)"
    try:
        fx2, se2, nm2, vc2, secs2, cnv2, warn2 = lmer(
            fml_cr, d, [yname, xname, "Bookies", "Matchup"] + COVS)
        print(f"     {secs2:.1f} s   Konvergenz: {'; '.join(cnv2)}")
        for w in warn2:
            print(f"     WARNUNG: {w}")
        print("     Varianzkomponenten:")
        print("       " + vc2.round(8).to_string(index=False)
              .replace("\n", "\n       "))
        j2 = nm2.index(xname)
        print(f"     beta({xname}) crossed {fx2[j2]:+.6f}  gegen "
              f"Bookmaker-only {fx[i_m]:+.6f}   "
              f"Differenz {fx2[j2] - fx[i_m]:+.6f}")
        vc2 = vc2.assign(model=key, variant="crossed")
        vc_rows.append(vc2)
    except Exception as e:  # noqa: BLE001
        print(f"     NICHT SCHAETZBAR: {type(e).__name__}: "
              f"{str(e).strip().splitlines()[-1]}")
    vc_rows.append(vc.assign(model=key, variant="bookmaker_only"))

pd.DataFrame(gate_rows).to_csv(f"{OUT}/gate.csv", index=False)
pd.DataFrame(cl_rows).to_csv(f"{OUT}/cluster_robust.csv", index=False)
pd.DataFrame(wald_rows).to_csv(f"{OUT}/bookie_wald.csv", index=False)
pd.DataFrame(anova_rows).to_csv(f"{OUT}/match_anova.csv", index=False)
pd.concat(vc_rows, ignore_index=True).to_csv(f"{OUT}/varcomp.csv",
                                             index=False)
print(f"\ngeschrieben: {OUT}/gate.csv, cluster_robust.csv, bookie_wald.csv, "
      f"match_anova.csv, varcomp.csv, *_bookie_fe_slopes.csv")
