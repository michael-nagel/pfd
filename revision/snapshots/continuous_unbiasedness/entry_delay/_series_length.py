#!/usr/bin/env python3
"""Kontrolle des Verspätungseffekts für die Serienlänge (R2-C2).

Letzter offener Konfundierer aus `README.md`: Verspätung korreliert mechanisch
mit der Serienlänge (`TsDur`, `NumOddsMvt`) -- wer spät einsteigt, hat weniger
Zeit und weniger Preisbewegungen. Der Endwert-Abfall von beta_1 könnte also ein
Längeneffekt sein.

  1) Korrelationen von log1p(Verspätung) mit TsDur, NumOddsMvt und der eigenen
     Fensterlänge -- gesamt und within Bookmaker -- plus Kollinearitätsmaße
     (within-R^2, VIF, Restvarianz der Verspätung nach Partialling-out)
  2) Within-Modell M1 mit der Serienlänge als zusätzlichem te(X, .)-Term
     (Haupteffekt und Interaktion mit Exog), zusätzlich ein Modell mit echter
     3-fach-Interaktion te(X, Verspätung, Länge). Ausgewertet wird beta_1 über
     die Verspätungsstufen bei FESTER Länge und über die Längenstufen bei
     FESTER Verspätung; dazu mgcvs Concurvity-Maße je Term
  3) modellfrei: Split an der eigenen Median-Verspätung wie in
     `_within_bookmaker.py`, aber INNERHALB von Längenklassen (je Bookmaker
     unter/über der eigenen Median-Länge), danach über die Klassen aggregiert

Spezifikation sonst wie `_within_bookmaker.py`: echte Beobachtungen,
Matchup-Perzentilachse, p_ref = erster echt beobachteter Preis, ungewichtet,
k=6, Bookmaker-FE + Exog:B, Verspätung und Länge within Bookmaker zentriert.
beta_1 wird über die Bookmaker-Verteilung mit FESTEN Gewichten marginalisiert.
Rein diagnostisch.
"""

import sys
import tempfile

import numpy as np
import pandas as pd
import rpy2.robjects as ro
from omegaconf import OmegaConf
from rpy2.rinterface_lib.embedded import RRuntimeError
from rpy2.robjects import numpy2ri, pandas2ri
from rpy2.robjects.conversion import localconverter
from scipy import stats

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

OUT = "revision/snapshots/continuous_unbiasedness/entry_delay"
FRAME = f"{tempfile.gettempdir()}/pfd_delay_frame.parquet"
K = 6
GRID = np.linspace(0.01, 0.99, 100)
QQ = [0.10, 0.25, 0.50, 0.75, 0.90]     # Auswertungsstufen
MIN_SER = 250                           # Serien je Hälfte einer Längenklasse
MIN_ROWS = 2500                         # Zeilen je Hälfte einer Längenklasse

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
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78, flush=True)


def demean(s, by):
    """Within-Zentrierung: Abweichung vom Bookmaker-Mittel."""
    return s - s.groupby(by).transform("mean")


def r2(y, xs):
    """R^2 einer OLS-Regression von y auf xs (mit Konstante)."""
    Xm = np.column_stack([np.ones(len(y))] + [x.to_numpy() for x in xs])
    yv = y.to_numpy()
    res = yv - Xm @ np.linalg.lstsq(Xm, yv, rcond=None)[0]
    return 1 - res.var() / yv.var()


def fit_model(d, formula, label, cols):
    """bam-Fit; das Modell bleibt als `m` in R für `eval_beta1` liegen."""
    num = ["Endog", "Exog", "X"] + cols
    dd = d[num + ["B"]].copy()
    dd = dd[np.isfinite(dd[num]).all(axis=1)]
    with localconverter(ro.default_converter + pandas2ri.converter):
        ro.globalenv["d"] = dd
    ro.globalenv["kk"] = K
    ro.globalenv["fml"] = formula
    print(f"\n  {label}:  n={len(dd):,d}\n    {formula}", flush=True)
    ro.r("""
    d$B <- factor(d$B)
    m <- bam(as.formula(fml), data = d, method = "fREML", discrete = TRUE)
    st <- as.data.frame(summary(m)$s.table)
    st$term <- rownames(st)
    cc <- tryCatch({x <- as.data.frame(concurvity(m, full = TRUE))
                    x$measure <- rownames(x); x},
                   error = function(e) data.frame(measure = paste("FEHLER:",
                                                                  e$message)))
    """)
    with localconverter(ro.default_converter + pandas2ri.converter):
        st = ro.conversion.get_conversion().rpy2py(ro.globalenv["st"])
        cc = ro.conversion.get_conversion().rpy2py(ro.globalenv["cc"])
    print(st.set_index("term").round(3).to_string(), flush=True)
    print("\n    Concurvity (0 = orthogonal, 1 = vollständig kollinear):")
    print(cc.set_index("measure").round(3).to_string(), flush=True)
    return st.assign(model=label, n=len(dd))


def eval_beta1(evalvar, levels, others, wt):
    """beta_1(X) an festen Stufen von `evalvar`, andere Kovariaten auf `others`
    fixiert, über die Bookmaker-Verteilung marginalisiert (Gewichte `wt`, über
    alle Stufen fest, damit kein Kompositionseffekt einläuft)."""
    gg = pd.DataFrame([(x, lv) for lv in levels for x in GRID],
                      columns=["X", evalvar])
    for c, v in others.items():
        gg[c] = float(v)
    gg["gid"] = np.arange(len(gg))
    g2 = gg.merge(wt.rename("wt").rename_axis("B").reset_index(), how="cross")

    with localconverter(ro.default_converter + pandas2ri.converter):
        ro.globalenv["g2"] = g2
    ro.r("""
    g2$B <- factor(g2$B, levels = levels(d$B))
    Xp <- predict(m, transform(g2, Exog = 1), type = "lpmatrix") -
          predict(m, transform(g2, Exog = 0), type = "lpmatrix")
    Xa <- rowsum(Xp * g2$wt, g2$gid)
    Xa <- Xa[order(as.integer(rownames(Xa))), , drop = FALSE]
    out <- data.frame(beta_1 = as.vector(Xa %*% coef(m)),
                      se = sqrt(pmax(0, rowSums((Xa %*% vcov(m)) * Xa))))
    """)
    with localconverter(ro.default_converter + pandas2ri.converter):
        o = ro.conversion.get_conversion().rpy2py(ro.globalenv["out"])
    o["pctl"] = np.tile(GRID * 100, len(levels))
    o["level"] = np.repeat(np.asarray(levels, float), len(GRID))
    return o


def fit_simple(d, label):
    """bam(Endog ~ s(X,k) + s(X,by=Exog,k)); beta_1(X) auf GRID."""
    d = d[["Endog", "Exog", "X"]].astype(float)
    d = d[np.isfinite(d).all(axis=1)]
    with localconverter(ro.default_converter + pandas2ri.converter):
        ro.globalenv["ds"] = d
    with localconverter(ro.default_converter + numpy2ri.converter):
        ro.globalenv["grid"] = GRID
    ro.globalenv["kk"] = K
    ro.r("""
    ms <- bam(Endog ~ s(X, k = kk) + s(X, by = Exog, k = kk), data = ds,
              method = "fREML", discrete = TRUE)
    Xs <- predict(ms, data.frame(X = grid, Exog = 1), type = "lpmatrix") -
          predict(ms, data.frame(X = grid, Exog = 0), type = "lpmatrix")
    outs <- data.frame(pctl = grid * 100, beta_1 = as.vector(Xs %*% coef(ms)))
    """)
    with localconverter(ro.default_converter + pandas2ri.converter):
        o = ro.conversion.get_conversion().rpy2py(ro.globalenv["outs"])
    print(f"      {label:<34s} n={len(d):>8,d}  Mittel "
          f"{o['beta_1'].mean():>7.3f}  Ende {o['beta_1'].iloc[-1]:>7.3f}",
          flush=True)
    return o


# ------------------------------------------------------------------- Daten
try:
    df = pd.read_parquet(FRAME)
    print(f"Frame aus Cache: {len(df):,d} Zeilen")
except (FileNotFoundError, OSError):
    df = build()
    print(f"Frame neu gebaut: {len(df):,d} Zeilen")

df["B"] = df["Bookies"].astype(str)

ser = df.groupby("GroupId").agg(
    B=("B", "first"), DelayH=("DelayH", "first"), TsDur=("TsDur", "first"),
    NumOddsMvt=("NumOddsMvt", "first"), OwnSpanH=("OwnSpanH", "first"),
    OwnXSpan=("OwnXSpan", "first"), SpanH=("SpanH", "first"))
ser["LD"] = np.log1p(ser["DelayH"])
ser["LN"] = np.log(ser["NumOddsMvt"])
print(f"Serien: {len(ser):,d}   Bookmaker: {ser['B'].nunique()}")

# --------------------------------------------------------- 1) Korrelationen
block("1) KORRELATION log1p(VERSPÄTUNG) MIT DER SERIENLÄNGE")

# TsDur ist in `filter_and_shape` z-standardisiert; prüfen, ob es bis auf die
# affine Transformation dasselbe ist wie die eigene Fensterlänge in Stunden.
r_id = ser["TsDur"].corr(ser["OwnSpanH"])
print(f"  corr(TsDur, eigene Fensterlänge in h) = {r_id:.6f}"
      f"   -> {'dieselbe Variable' if r_id > 0.9999 else 'verschieden'}")
print(f"  TsDur: Mittel {ser['TsDur'].mean():.4f}  sd {ser['TsDur'].std():.4f}"
      f"   (z-standardisiert)")
print(f"  eigene Fensterlänge h: Median {ser['OwnSpanH'].median():.2f}   IQR "
      f"{ser['OwnSpanH'].quantile(.75) - ser['OwnSpanH'].quantile(.25):.2f}")

LENVARS = [
    ("TsDur", "TsDur (z-std. eigene Dauer)"),
    ("NumOddsMvt", "NumOddsMvt (Zahl der Bewegungen)"),
    ("LN", "log(NumOddsMvt)"),
    ("OwnSpanH", "eigene Fensterlänge (h)"),
    ("OwnXSpan", "eigener Anteil am Matchup-Fenster"),
    ("SpanH", "Matchup-Fensterlänge (h)"),
]

nb = ser.groupby("B").size()
rows = []
for v, lab in LENVARS:
    per_b = pd.Series({b: g["LD"].corr(g[v], method="spearman")
                       for b, g in ser.groupby("B")})
    rows.append({
        "Variable": lab,
        "Pearson_gesamt": ser["LD"].corr(ser[v]),
        "Spearman_gesamt": ser["LD"].corr(ser[v], method="spearman"),
        "Pearson_within": demean(ser["LD"], ser["B"]).corr(
            demean(ser[v], ser["B"])),
        "Spearman_within": np.average(per_b, weights=nb.loc[per_b.index]),
    })
cor = pd.DataFrame(rows)
print("\n  (within = Bookmaker-Mittel abgezogen; Spearman_within = "
      "n-gewichtetes Mittel\n   der bookmakerweisen Rangkorrelationen)")
print(cor.to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
cor.to_csv(f"{OUT}/series_length_correlations.csv", index=False)

# ------------------------------------------------ Kollinearitätsdiagnostik
block("1b) KOLLINEARITÄT: IST DIE VERSPÄTUNG NEBEN DER LÄNGE IDENTIFIZIERT?")

SETS = [
    ("TsDur", ["TsDur"]),
    ("log(NumOddsMvt)", ["LN"]),
    ("TsDur + log(NumOddsMvt)", ["TsDur", "LN"]),
    ("TsDur + log(NumOddsMvt) + eig. Anteil", ["TsDur", "LN", "OwnXSpan"]),
]
rows = []
for lab, vs in SETS:
    wit = r2(demean(ser["LD"], ser["B"]),
             [demean(ser[v], ser["B"]) for v in vs])
    rows.append({"Regressorsatz": lab,
                 "R2_gesamt": r2(ser["LD"], [ser[v] for v in vs]),
                 "R2_within": wit, "VIF_within": 1 / (1 - wit),
                 "Rest_sd_rel": np.sqrt(1 - wit)})
col = pd.DataFrame(rows)
print("  R^2 der Regression von log1p(Verspätung) auf die Längenmaße;")
print("  Rest_sd_rel = sd der Verspätung nach Partialling-out, relativ zu roh")
print(col.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
col.to_csv(f"{OUT}/series_length_collinearity.csv", index=False)

r2w = col.loc[col["Regressorsatz"] == "TsDur + log(NumOddsMvt)",
              "R2_within"].iloc[0]
print(f"\n  Urteil: within-R^2 = {r2w:.4f}, VIF = {1 / (1 - r2w):.2f}, "
      f"{np.sqrt(1 - r2w) * 100:.1f} % der Verspätungsstreuung\n  bleiben nach "
      f"Kontrolle übrig.")
print("  -> " + ("KOLLINEAR: beide Effekte sind nicht getrennt "
                 "identifizierbar." if r2w > 0.80 else
                 "getrennt identifizierbar (within-R^2 < 0,80)."))

# ------------------------------------------ 2) GAM mit Längenkontrolle
block("2) WITHIN-MODELL M1 MIT SERIENLÄNGE ALS KONTROLL-/INTERAKTIONSTERM")

lvl = {}
for v, src in (("DW", "LD"), ("NW", "LN"), ("TW", "TsDur")):
    ser[v] = demean(ser[src], ser["B"])
    lvl[v] = [float(ser[v].quantile(q)) for q in QQ]
df = df.merge(ser[["DW", "NW", "TW"]], left_on="GroupId", right_index=True,
              how="left")
wt = ser.groupby("B").size()
wt = wt / wt.sum()

print("  Auswertungsstufen (within-zentriert, q10 ... q90):")
for v, lab in (("DW", "Verspätung log1p(h)"), ("NW", "log(NumOddsMvt)"),
               ("TW", "TsDur (sd)")):
    print(f"    {v} {lab:<22s} {', '.join(f'{x:+.2f}' for x in lvl[v])}")

BASE = "Endog ~ B + Exog:B"
TE = "te(X, {0}, k = c(kk, kk))"
TE3 = "te(X, {0}, {1}, k = c(5, 5, 5))"


def spec(vs):
    """Additive Fassung: je Variable ein te(X, .)-Paar (Niveau und Steigung)."""
    parts = [TE.format(v) for v in vs]
    parts += [TE.format(v)[:-1] + ", by = Exog)" for v in vs]
    return f"{BASE} + " + " + ".join(parts)


def spec_ti(vs):
    """ti-Zerlegung. Zwei te(X, .)-Flächen enthalten BEIDE den vollen
    X-Marginaleffekt und sind deshalb nicht getrennt identifiziert (siehe die
    Concurvity-Ausgabe von `spec`). Hier steht der X-Marginaleffekt genau
    einmal, jede Zusatzvariable bekommt einen eigenen Haupteffekt und eine
    eigene, marginalfreie X-Interaktion."""
    lev = ["s(X, k = kk)"] + [f"s({v}, k = kk)" for v in vs] \
        + [f"ti(X, {v}, k = c(kk, kk))" for v in vs]
    slp = ["s(X, by = Exog, k = kk)"] \
        + [f"s({v}, by = Exog, k = kk)" for v in vs] \
        + [f"ti(X, {v}, k = c(kk, kk), by = Exog)" for v in vs]
    return f"{BASE} + " + " + ".join(lev + slp)


def spec3(a, b):
    """3-fach-Fassung: EINE Fläche te(X, a, b) für Niveau und Steigung, damit
    keine zwei Terme um denselben X-Marginaleffekt konkurrieren."""
    t = TE3.format(a, b)
    return f"{BASE} + {t} + {t[:-1]}, by = Exog)"


# M1nt (drei te-Flächen) ist bewusst NICHT mehr dabei: der Fit lief zwar
# durch, war aber rangdefizient (concurvity() scheiterte mit "singular matrix
# in 'backsolve'") und lieferte im Mittel NEGATIVE beta_1 -- der Befund ist
# damit gesichert. Auf dieser Maschine hat genau dieses Modell den Speicher
# gesprengt und die WSL-VM mitgenommen; es kostet nur Laufzeit und Risiko.
SPECS = [
    ("M1  nur Verspätung", ["DW"], spec(["DW"])),
    ("M1n te+te + log(NumOddsMvt)", ["DW", "NW"], spec(["DW", "NW"])),
    ("M1t te+te + TsDur", ["DW", "TW"], spec(["DW", "TW"])),
    ("T1  ti, nur Verspätung", ["DW"], spec_ti(["DW"])),
    ("T1n ti + log(NumOddsMvt)", ["DW", "NW"], spec_ti(["DW", "NW"])),
    ("T1t ti + TsDur", ["DW", "TW"], spec_ti(["DW", "TW"])),
    ("T1nt ti + beide", ["DW", "NW", "TW"], spec_ti(["DW", "NW", "TW"])),
    ("M1x 3-fach te(X,DW,NW)", ["DW", "NW"], spec3("DW", "NW")),
]
NAMES = {"DW": "Verspätung", "NW": "log(NumOddsMvt)", "TW": "TsDur"}

curves, summ, tables, failed = [], [], [], []
for label, vs, fml in SPECS:
    # Überlappende te(X, .)-Flächen können exakt rangdefizient werden; das ist
    # selbst ein Befund und darf den Lauf nicht abbrechen.
    try:
        tables.append(fit_model(df, fml, label, vs))
    except RRuntimeError as e:
        failed.append((label, str(e).strip().splitlines()[-1]))
        print(f"    NICHT SCHÄTZBAR: {failed[-1][1]}", flush=True)
        continue
    for ev in vs:
        others = {v: 0.0 for v in vs if v != ev}
        o = eval_beta1(ev, lvl[ev], others, wt)
        curves.append(o.assign(model=label, evalvar=ev))
        fix = ", ".join(f"{v}=0" for v in others) or "-"
        print(f"\n    beta_1 über {NAMES[ev]} (fix: {fix})", flush=True)
        for i, v in enumerate(lvl[ev]):
            s = o[o["level"] == v]
            summ.append({"model": label, "evalvar": ev, "q": QQ[i], "level": v,
                         "beta_1_mean": s["beta_1"].mean(),
                         "beta_1_start": s["beta_1"].iloc[0],
                         "beta_1_end": s["beta_1"].iloc[-1],
                         "se_end": s["se"].iloc[-1]})
            print(f"      q{QQ[i]:<5.2f} ({v:+.2f})  Mittel "
                  f"{s['beta_1'].mean():>7.3f}  Anfang "
                  f"{s['beta_1'].iloc[0]:>7.3f}  Ende "
                  f"{s['beta_1'].iloc[-1]:>7.3f} ({s['se'].iloc[-1]:.3f})",
                  flush=True)
        sp = [x for x in summ if x["model"] == label and x["evalvar"] == ev]
        print(f"      Spreizung q90-q10:  Mittel "
              f"{sp[-1]['beta_1_mean'] - sp[0]['beta_1_mean']:+.3f}   Ende "
              f"{sp[-1]['beta_1_end'] - sp[0]['beta_1_end']:+.3f}", flush=True)

    pd.concat(curves, ignore_index=True).to_csv(
        f"{OUT}/beta1_series_length_models.csv", index=False)
    pd.DataFrame(summ).to_csv(
        f"{OUT}/beta1_series_length_summary.csv", index=False)
    pd.concat(tables, ignore_index=True).to_csv(
        f"{OUT}/series_length_gam_terms.csv", index=False)

for label, msg in failed:
    print(f"\n  {label}: NICHT SCHÄTZBAR -- {msg}")

sm = pd.DataFrame(summ)
print("\n  Endspreizung (q90 - q10) je Modell und Auswertungsvariable;"
      "\n  Anteil bezogen auf M1s Verspätungsspreizung:")
ref = None
for (label, ev), s in sm.groupby(["model", "evalvar"], sort=False):
    spe = s["beta_1_end"].iloc[-1] - s["beta_1_end"].iloc[0]
    spm = s["beta_1_mean"].iloc[-1] - s["beta_1_mean"].iloc[0]
    ref = spe if ref is None else ref
    print(f"    {label:<26s} {NAMES[ev]:<16s} Ende {spe:+.3f} "
          f"({spe / ref * 100:6.1f} %)   Mittel {spm:+.3f}")

# --------------------- 3) Modellfreier Split innerhalb von Längenklassen
block("3) SPLIT AN DER EIGENEN MEDIAN-VERSPÄTUNG INNERHALB VON LÄNGENKLASSEN")

ser["Late"] = ser["DelayH"] > ser.groupby("B")["DelayH"].transform("median")
imb = ser.groupby(["B", "Late"])[["TsDur", "NumOddsMvt", "OwnSpanH"]].mean()
imb = imb.xs(True, level="Late") - imb.xs(False, level="Late")
print("  Längenimbalance im UNKONTROLLIERTEN Split (spät - früh), je "
      "Bookmaker:")
for c in ("TsDur", "NumOddsMvt", "OwnSpanH"):
    print(f"    {c:<11s} Median {imb[c].median():+.3f}   Spanne "
          f"[{imb[c].min():+.3f}, {imb[c].max():+.3f}]   negativ "
          f"{int((imb[c] < 0).sum())}/{len(imb)}")

rows = []
for lv in ("TsDur", "NumOddsMvt"):
    ser["Long"] = ser[lv] > ser.groupby("B")[lv].transform("median")
    ser["LateC"] = ser["DelayH"] > ser.groupby(
        ["B", "Long"])["DelayH"].transform("median")
    df["Long"] = df["GroupId"].map(ser["Long"])
    df["LateC"] = df["GroupId"].map(ser["LateC"])
    print(f"\n  --- Längenklassen nach {lv} (je Bookmaker eigener Median) ---",
          flush=True)
    for b in sorted(ser["B"].unique()):
        for lng in (False, True):
            key = ser[(ser["B"] == b) & (ser["Long"] == lng)]
            cellrows = df[(df["B"] == b) & (df["Long"] == lng)]
            early = cellrows[~cellrows["LateC"]]
            late = cellrows[cellrows["LateC"]]
            n_e = int((~key["LateC"]).sum())
            n_l = int(key["LateC"].sum())
            cell = f"{b} / {'lang' if lng else 'kurz'}"
            if (min(n_e, n_l) < MIN_SER
                    or min(len(early), len(late)) < MIN_ROWS):
                print(f"    {cell:<26s} übersprungen ({n_e}/{n_l} Serien)",
                      flush=True)
                continue
            gap = (key.loc[key["LateC"], lv].mean()
                   - key.loc[~key["LateC"], lv].mean())
            print(f"    {cell:<26s} Serien {n_e:,d}/{n_l:,d}   "
                  f"Median-Verspätung {key['DelayH'].median():.2f} h   "
                  f"Rest-Längengap {gap:+.3f}", flush=True)
            oe = fit_simple(early, f"{cell} früh")
            ol = fit_simple(late, f"{cell} spät")
            rows.append({
                "len_var": lv, "B": b, "long": lng, "n_ser_early": n_e,
                "n_ser_late": n_l, "median_delay_h": key["DelayH"].median(),
                "len_gap": gap,
                "beta1_early_mean": oe["beta_1"].mean(),
                "beta1_late_mean": ol["beta_1"].mean(),
                "beta1_early_end": oe["beta_1"].iloc[-1],
                "beta1_late_end": ol["beta_1"].iloc[-1]})

cells = pd.DataFrame(rows)
cells["d_mean"] = cells["beta1_late_mean"] - cells["beta1_early_mean"]
cells["d_end"] = cells["beta1_late_end"] - cells["beta1_early_end"]
cells["n"] = cells["n_ser_early"] + cells["n_ser_late"]
cells.to_csv(f"{OUT}/beta1_length_split_cells.csv", index=False)

for lv, g in cells.groupby("len_var"):
    block(f"3) ERGEBNIS, LÄNGENKLASSEN NACH {lv}")
    agg = pd.DataFrame([{
        "B": b, "n_Zellen": len(x), "n_Serien": x["n"].sum(),
        "len_gap": np.average(x["len_gap"], weights=x["n"]),
        "d_mean": np.average(x["d_mean"], weights=x["n"]),
        "d_end": np.average(x["d_end"], weights=x["n"])}
        for b, x in g.groupby("B")]).set_index("B").sort_values("d_end")
    print(agg.to_string(float_format=lambda v: f"{v:,.3f}"))

    n = len(agg)
    for c in ("d_end", "d_mean"):
        neg = int((agg[c] < 0).sum())
        print(f"\n  {c}:  negativ {neg}/{n}   Vorzeichentest "
              f"p={stats.binomtest(neg, n, 0.5).pvalue:.4f}   t-Test "
              f"p={stats.ttest_1samp(agg[c], 0).pvalue:.4f}   gew. Mittel "
              f"{np.average(agg[c], weights=agg['n_Serien']):+.3f}   Median "
              f"{agg[c].median():+.3f}")
    agg.to_csv(f"{OUT}/beta1_length_split_{lv}.csv")

print(f"\ngeschrieben: {OUT}/series_length_correlations.csv, "
      f"series_length_collinearity.csv, series_length_gam_terms.csv, "
      f"beta1_series_length_{{models,summary}}.csv, "
      f"beta1_length_split_{{cells,TsDur,NumOddsMvt}}.csv")
