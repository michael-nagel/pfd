#!/usr/bin/env python3
"""Within-Bookmaker-Test für den Verspätungseffekt (R2-C2).

Offene Einschränkung der Quartilsanalyse: Verspätung und Bookmaker-Identität
sind konfundiert (manche Bookmaker eröffnen systematisch früh). Dieser Test
identifiziert den Effekt WITHIN Bookmaker -- derselbe Bookmaker mal früh, mal
spät eingestiegen.

  1) Kreuztabelle Bookmaker x Verspätungsquartil, Streuungsmaße und die
     Varianzzerlegung von log1p(Verspätung) in between/within Bookmaker
  2) drei GAM-Stufen:
       M0  gepoolt              te(X,LD) + te(X,LD,by=Exog)
       M1  + Bookmaker-FE und bookmakerspezifische Steigung, Verspätung
           within Bookmaker zentriert (DW)  -> reine Within-Identifikation
       M2  wie M1, aber ohne Exog:B (Kontrolle der Rangfrage)
     beta_1 wird über die Bookmaker-Verteilung marginalisiert (feste Gewichte
     über alle Verspätungsstufen), damit kein Kompositionseffekt einläuft
  3) modellfrei: je Bookmaker Split an der EIGENEN Median-Verspätung, beta_1
     getrennt für früh/spät, gewichteter Mittelwert der Within-Differenz

Spezifikation sonst wie `_entry_delay.py` / `_attenuation.py`: echte
Beobachtungen, Matchup-Perzentilachse, p_ref = erster echt beobachteter Preis,
ungewichtet, k=6. Rein diagnostisch.
"""

import sys
import tempfile

import numpy as np
import pandas as pd
import rpy2.robjects as ro
from omegaconf import OmegaConf
from rpy2.robjects import numpy2ri, pandas2ri
from rpy2.robjects.conversion import localconverter

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

OUT = "revision/snapshots/continuous_unbiasedness/entry_delay"
FRAME = f"{tempfile.gettempdir()}/pfd_delay_frame.parquet"
K = 6
GRID = np.linspace(0.01, 0.99, 100)
QQ = [0.10, 0.25, 0.50, 0.75, 0.90]     # Verspätungsstufen zur Auswertung
MIN_N = 3000                            # Serien je Bookmaker für Panel 3

pd.set_option("display.width", 250)
ro.r("library(mgcv)")


def build():
    """Kontinuierlichen Frame exakt wie `_entry_delay.py` aufbauen."""
    cfg = OmegaConf.create({"estimation": {
        "spec": "BmHome", "normalize": True, "compets": None,
        "bm_quantile": 0.25, "ts_dur": [12, 72], "period": None,
        "resample_freq": "1min", "pctl": 2}})

    raw = pd.read_hdf("data/processed/shaped_data.h5", "df")
    for c in ("Date", "Update"):
        raw[c] = pd.to_datetime(raw[c])
    df, *_ = filter_and_shape_data(raw.copy(), cfg)

    df["TsStart"] = df.groupby("Matchup")["Update"].transform("min")
    df["TsEnd"] = df.groupby("Matchup")["Update"].transform("max")
    df = df[df.groupby("GroupId")["OddsMvt"].transform("std") > 0]
    df = df[df["NumOddsMvt"] < 20]

    span = (df["TsEnd"] - df["TsStart"]).dt.total_seconds()
    df["SpanH"] = span / 3600.0
    df["X"] = np.where(span > 0,
                       (df["Update"] - df["TsStart"]).dt.total_seconds() / span,
                       np.nan)
    df = df.sort_values(["GroupId", "Update"])
    df["PRef"] = df.groupby("GroupId", sort=False)["OddsMvt"].transform("first")

    own_start = df.groupby("GroupId")["Update"].transform("min")
    own_end = df.groupby("GroupId")["Update"].transform("max")
    df["DelayH"] = (own_start - df["TsStart"]).dt.total_seconds() / 3600.0
    df["OwnSpanH"] = (own_end - own_start).dt.total_seconds() / 3600.0
    df["OwnXSpan"] = (own_end - own_start).dt.total_seconds() / span

    df["Endog"] = df["Match"] - df["PRef"]
    df["Exog"] = df["OddsMvt"] - df["PRef"]
    df["ObsIdx"] = df.groupby("GroupId").cumcount()
    df = df[df["ObsIdx"] > 0]
    df = df[np.isfinite(df["X"])]

    keep = ["GroupId", "Matchup", "Bookies", "X", "Exog", "Endog", "DelayH",
            "SpanH", "OwnSpanH", "OwnXSpan", "NumOddsMvt", "TsDur"]
    df = df[keep].reset_index(drop=True)
    df.to_parquet(FRAME)
    return df


def block(title):
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def fit_simple(d, label):
    """bam(Endog ~ s(X,k) + s(X,by=Exog,k)); beta_1(X) auf GRID."""
    d = d[["Endog", "Exog", "X"]].astype(float)
    d = d[np.isfinite(d).all(axis=1)]
    with localconverter(ro.default_converter + pandas2ri.converter):
        ro.globalenv["d"] = d
    with localconverter(ro.default_converter + numpy2ri.converter):
        ro.globalenv["grid"] = GRID
    ro.globalenv["kk"] = K
    ro.r("""
    m <- bam(Endog ~ s(X, k = kk) + s(X, by = Exog, k = kk), data = d,
             method = "fREML", discrete = TRUE)
    Xp <- predict(m, data.frame(X = grid, Exog = 1), type = "lpmatrix") -
          predict(m, data.frame(X = grid, Exog = 0), type = "lpmatrix")
    out <- data.frame(pctl = grid * 100, beta_1 = as.vector(Xp %*% coef(m)),
                      se = sqrt(pmax(0, rowSums((Xp %*% vcov(m)) * Xp))))
    """)
    with localconverter(ro.default_converter + pandas2ri.converter):
        o = ro.conversion.get_conversion().rpy2py(ro.globalenv["out"])
    print(f"  {label:<34s} n={len(d):>9,d}  beta1 mean={o['beta_1'].mean():.3f}"
          f"  Rand {o['beta_1'].iloc[0]:.3f} -> {o['beta_1'].iloc[-1]:.3f}",
          flush=True)
    return o


def fit_delay(d, dvar, formula, label, levels, wt):
    """Ein GAM mit Verspätungs-Interaktion; beta_1(X, dvar) über die
    Bookmaker-Verteilung marginalisiert (Gewichte wt, über alle Stufen fest)."""
    cols = ["Endog", "Exog", "X", dvar, "B"]
    dd = d[cols].copy()
    dd = dd[np.isfinite(dd[["Endog", "Exog", "X", dvar]]).all(axis=1)]

    # Auswertungsgitter: (X, Verspätungsstufe) x Bookmaker, mit Gewichten
    gg = pd.DataFrame([(x, lv) for lv in levels for x in GRID],
                      columns=["X", dvar])
    gg["gid"] = np.arange(len(gg))          # eine gid je (X, Verspätungsstufe)
    g2 = gg.merge(wt.rename("wt").rename_axis("B").reset_index(), how="cross")

    with localconverter(ro.default_converter + pandas2ri.converter):
        ro.globalenv["d"] = dd
        ro.globalenv["g2"] = g2
    ro.globalenv["kk"] = K
    ro.globalenv["fml"] = formula
    ro.globalenv["dv"] = dvar
    ro.r("""
    d$B <- factor(d$B); g2$B <- factor(g2$B, levels = levels(d$B))
    m <- bam(as.formula(fml), data = d, method = "fREML", discrete = TRUE)
    Xp <- predict(m, transform(g2, Exog = 1), type = "lpmatrix") -
          predict(m, transform(g2, Exog = 0), type = "lpmatrix")
    Xa <- rowsum(Xp * g2$wt, g2$gid)
    Xa <- Xa[order(as.integer(rownames(Xa))), , drop = FALSE]
    V  <- vcov(m)
    out <- data.frame(beta_1 = as.vector(Xa %*% coef(m)),
                      se = sqrt(pmax(0, rowSums((Xa %*% V) * Xa))))
    st <- summary(m)$s.table
    edf_tot <- sum(summary(m)$edf)
    """)
    with localconverter(ro.default_converter + pandas2ri.converter):
        o = ro.conversion.get_conversion().rpy2py(ro.globalenv["out"])
    o["pctl"] = np.tile(GRID * 100, len(levels))
    o["level"] = np.repeat(np.asarray(levels, float), len(GRID))
    o["model"] = label
    print(f"\n  {label}:  n={len(dd):,d}")
    print(ro.r("paste(capture.output(print(round(st, 3))), collapse='\n')")[0])
    return o


# ------------------------------------------------------------------- Daten
try:
    df = pd.read_parquet(FRAME)
    print(f"Frame aus Cache: {len(df):,d} Zeilen")
except (FileNotFoundError, OSError):
    df = build()
    print(f"Frame neu gebaut: {len(df):,d} Zeilen")

df["B"] = df["Bookies"].astype(str)
ser = df.groupby("GroupId").agg(DelayH=("DelayH", "first"), B=("B", "first"))
ser["Q"] = pd.qcut(ser["DelayH"], 4, labels=False, duplicates="drop")
ser["LD"] = np.log1p(ser["DelayH"])
print(f"Serien: {len(ser):,d}   Bookmaker: {ser['B'].nunique()}")

# ------------------------------------------- 1) Kreuztabelle und Überlappung
block("1) BOOKMAKER x VERSPÄTUNGSQUARTIL (Zeilenanteile)")
ct = pd.crosstab(ser["B"], ser["Q"], normalize="index")
ct.columns = [f"Q{c + 1}" for c in ct.columns]
tab = pd.concat([
    ser.groupby("B").size().rename("n_Serien"),
    ser.groupby("B")["DelayH"].median().rename("Median_h"),
    ser.groupby("B")["DelayH"].agg(
        lambda s: s.quantile(.75) - s.quantile(.25)).rename("IQR_h"),
    ser.groupby("B")["LD"].std().rename("sd_logDelay"), ct], axis=1)
tab["HHI"] = (ct ** 2).sum(axis=1)      # 0,25 = perfekt gestreut, 1 = konz.
tab["min_Q_Anteil"] = ct.min(axis=1)
tab = tab.sort_values("n_Serien", ascending=False)
print(tab.to_string(float_format=lambda v: f"{v:,.3f}"))

grand = ser["LD"].var(ddof=0)
btw = ser.groupby("B")["LD"].transform("mean").var(ddof=0)
print("\nVarianzzerlegung von log1p(Verspätung):")
print(f"  gesamt  {grand:.4f}")
print(f"  between {btw:.4f}  ({btw / grand * 100:.1f} %)")
print(f"  within  {grand - btw:.4f}  ({(1 - btw / grand) * 100:.1f} %)")
print(f"\nalle 4 Quartile >= 5 %  : {int((ct.min(axis=1) >= .05).sum())} "
      f"von {len(ct)} Bookmakern")
print(f"alle 4 Quartile >= 10 % : {int((ct.min(axis=1) >= .10).sum())} "
      f"von {len(ct)} Bookmakern")
print(f"mittlerer HHI {tab['HHI'].mean():.3f}  (0,250 = perfekte Streuung, "
      f"1,000 = ein Quartil)")
tab.to_csv(f"{OUT}/bookie_delay_crosstab.csv")

# --------------------------------------------------------- 2) GAM-Stufen
block("2) GAM MIT VERSPÄTUNGS-INTERAKTION: GEPOOLT vs. WITHIN BOOKMAKER")
df = df.merge(ser[["LD"]], left_on="GroupId", right_index=True, how="left")
df["DW"] = df["LD"] - df.groupby("B")["LD"].transform("mean")
wt = ser.groupby("B").size()
wt = wt / wt.sum()

lv_ld = [float(ser["LD"].quantile(q)) for q in QQ]
lv_dw = [float((ser["LD"] - ser.groupby("B")["LD"].transform("mean"))
               .quantile(q)) for q in QQ]
print(f"  Auswertungsstufen LD (q{QQ}): "
      f"{', '.join(f'{np.expm1(v):.2f} h' for v in lv_ld)}")
print(f"  Auswertungsstufen DW (q{QQ}): "
      f"{', '.join(f'{v:+.2f}' for v in lv_dw)} (log-Abweichung)")

specs = [
    ("M0 gepoolt (raw LD)", "LD", lv_ld,
     "Endog ~ te(X, LD, k = c(kk, kk)) + te(X, LD, k = c(kk, kk), by = Exog)"),
    ("M1 FE + Exog:B, within (DW)", "DW", lv_dw,
     "Endog ~ B + Exog:B + te(X, DW, k = c(kk, kk)) + "
     "te(X, DW, k = c(kk, kk), by = Exog)"),
    ("M2 FE ohne Exog:B, within (DW)", "DW", lv_dw,
     "Endog ~ B + te(X, DW, k = c(kk, kk)) + "
     "te(X, DW, k = c(kk, kk), by = Exog)"),
]
res, summ = [], []
for label, dv, lv, fml in specs:
    o = fit_delay(df, dv, fml, label, lv, wt)
    res.append(o)
    print(f"    {'Stufe':<12s} {'beta_1':>10s} {'Anfang':>9s} {'Ende':>9s}")
    for i, v in enumerate(lv):
        s = o[o["level"] == v]
        hrs = np.expm1(v) if dv == "LD" else v
        unit = "h" if dv == "LD" else ""
        summ.append({"model": label, "q": QQ[i], "level": v,
                     "level_h": hrs if dv == "LD" else np.nan,
                     "beta_1_mean": s["beta_1"].mean(),
                     "beta_1_start": s["beta_1"].iloc[0],
                     "beta_1_end": s["beta_1"].iloc[-1],
                     "se_mean": s["se"].mean()})
        print(f"    q{QQ[i]:<11.2f} {s['beta_1'].mean():>14.3f} "
              f"{s['beta_1'].iloc[0]:>9.3f} {s['beta_1'].iloc[-1]:>9.3f}"
              f"   ({hrs:+.2f}{unit})")
    sp = [s for s in summ if s["model"] == label]
    print(f"    Spreizung q10->q90:  Mittel "
          f"{sp[-1]['beta_1_mean'] - sp[0]['beta_1_mean']:+.3f}   Ende "
          f"{sp[-1]['beta_1_end'] - sp[0]['beta_1_end']:+.3f}")

out = pd.concat(res, ignore_index=True)
out.to_csv(f"{OUT}/beta1_within_bookmaker_models.csv", index=False)
sm = pd.DataFrame(summ)
sm.to_csv(f"{OUT}/beta1_within_bookmaker_summary.csv", index=False)

print("\n  Spreizung (q90 - q10) je Modell, Within-Anteil bezogen auf M0:")
base_sp = {}
for label in sm["model"].unique():
    s = sm[sm["model"] == label]
    spm = s["beta_1_mean"].iloc[-1] - s["beta_1_mean"].iloc[0]
    spe = s["beta_1_end"].iloc[-1] - s["beta_1_end"].iloc[0]
    base_sp[label] = (spm, spe)
    ref = base_sp[specs[0][0]]
    print(f"    {label:<32s} Mittel {spm:+.3f} ({spm / ref[0] * 100:6.1f} %)"
          f"   Ende {spe:+.3f} ({spe / ref[1] * 100:6.1f} %)")

# ------------------------------ 3) Split an der EIGENEN Median-Verspätung
block(f"3) JE BOOKMAKER: SPLIT AN DER EIGENEN MEDIAN-VERSPÄTUNG "
      f"(n >= {MIN_N:,d})")
med = ser.groupby("B")["DelayH"].median()
ser["Late"] = ser["DelayH"] > ser["B"].map(med)
df = df.merge(ser[["Late"]], left_on="GroupId", right_index=True, how="left")

cand = tab[tab["n_Serien"] >= MIN_N].nlargest(5, "sd_logDelay")
CAND_COLS = ["n_Serien", "Median_h", "IQR_h", "sd_logDelay"]
print("  5 Bookmaker mit der breitesten eigenen Verteilung:")
print(cand[CAND_COLS].to_string(float_format=lambda v: f"{v:,.3f}"))

rows, curves = [], []
for b in tab.index:
    sub = df[df["B"] == b]
    early, late = sub[~sub["Late"]], sub[sub["Late"]]
    ns = ser[ser["B"] == b]
    n_e = int((~ns["Late"]).sum())
    n_l = int(ns["Late"].sum())
    if min(len(early), len(late)) < 5000 or min(n_e, n_l) < 500:
        print(f"  {b:<14s} übersprungen (zu dünn: {n_e}/{n_l} Serien)")
        continue
    print(f"  {b:<14s} Serien früh/spät {n_e:,d}/{n_l:,d}   Median-Verspätung "
          f"{med[b]:.3f} h")
    oe = fit_simple(early, f"    {b} früh")
    ol = fit_simple(late, f"    {b} spät")
    for o, lab in ((oe, "early"), (ol, "late")):
        o = o.assign(B=b, half=lab)
        curves.append(o)
    rows.append({"B": b, "n_ser_early": n_e, "n_ser_late": n_l,
                 "median_delay_h": med[b],
                 "sd_logDelay": tab.loc[b, "sd_logDelay"],
                 "beta1_early_mean": oe["beta_1"].mean(),
                 "beta1_late_mean": ol["beta_1"].mean(),
                 "beta1_early_end": oe["beta_1"].iloc[-1],
                 "beta1_late_end": ol["beta_1"].iloc[-1]})

sp = pd.DataFrame(rows)
sp["d_mean"] = sp["beta1_late_mean"] - sp["beta1_early_mean"]
sp["d_end"] = sp["beta1_late_end"] - sp["beta1_early_end"]
sp = sp.sort_values("sd_logDelay", ascending=False)
print("\n  Within-Bookmaker-Differenz spät - früh:")
print(sp[["B", "n_ser_early", "n_ser_late", "median_delay_h", "sd_logDelay",
          "beta1_early_mean", "beta1_late_mean", "d_mean",
          "beta1_early_end", "beta1_late_end", "d_end"]].to_string(
    index=False, float_format=lambda v: f"{v:,.3f}"))

w = sp["n_ser_early"] + sp["n_ser_late"]
print(f"\n  Bookmaker mit d_mean < 0 (spät niedriger): "
      f"{int((sp['d_mean'] < 0).sum())} von {len(sp)}")
print(f"  Bookmaker mit d_end  < 0                 : "
      f"{int((sp['d_end'] < 0).sum())} von {len(sp)}")
wm, we = (np.average(sp[c], weights=w) for c in ("d_mean", "d_end"))
print(f"  gewichteter Mittelwert  d_mean {wm:+.3f}   d_end {we:+.3f}")
print(f"  ungewichteter Median    d_mean {sp['d_mean'].median():+.3f}"
      f"   d_end {sp['d_end'].median():+.3f}")

sp.to_csv(f"{OUT}/beta1_within_bookmaker_split.csv", index=False)
pd.concat(curves, ignore_index=True).to_csv(
    f"{OUT}/beta1_within_bookmaker_curves.csv", index=False)
cand.to_csv(f"{OUT}/bookie_widest_delay.csv")
print(f"\ngeschrieben: {OUT}/bookie_delay_crosstab.csv, "
      f"beta1_within_bookmaker_{{models,summary,split,curves}}.csv, "
      f"bookie_widest_delay.csv")
