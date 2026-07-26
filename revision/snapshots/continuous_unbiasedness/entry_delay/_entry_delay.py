#!/usr/bin/env python3
"""Off-Market-Learning control for the continuous beta_1 estimate (R2-C2).

Entry delay = hours between the matchwide start (earliest price over ALL
bookmakers of the matchup) and a series' own first observed price.

  1) distribution of the entry delay
  2) beta_1 curves fitted separately per delay quartile
  3) one interaction model: beta_1 free to depend on time AND log delay
  4) control: continuous fit on the 24,568 fully observed series only,
     against the full sample -- separates composition from measurement

Reference spec is model R of the channel decomposition: real observations,
matchup percentile axis, p_ref = first real observed price, unweighted, k=6.
Diagnostic only, nothing in the production pipeline is touched.
"""

import sys

import numpy as np
import pandas as pd
import rpy2.robjects as ro
from omegaconf import OmegaConf
from rpy2.robjects import numpy2ri, pandas2ri
from rpy2.robjects.conversion import localconverter

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

OUT = "revision/snapshots/continuous_unbiasedness/entry_delay"
CACHE = ("/mnt/c/Users/micha/AppData/Local/Temp/claude/"
         "C--Users-micha-OneDrive-Michi-pfd/"
         "a7ef249b-96b6-4348-a367-df03535e0ea1/scratchpad/gmm_mask_cache.h5")
K = 6
GRID = np.linspace(0.01, 0.99, 200)

ro.r("library(mgcv)")


def fit(d, label):
    """bam(Endog ~ s(X,k) + s(X,by=Exog,k)); returns beta_1(X) on GRID."""
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
    print(f"  {label:<32s} n={len(d):>9,d}  beta1 mean={o['beta_1'].mean():.3f}"
          f"  Rand {o['beta_1'].iloc[0]:.3f} -> {o['beta_1'].iloc[-1]:.3f}",
          flush=True)
    return o


# ------------------------------------------------------------- base data
cfg = OmegaConf.create({"estimation": {
    "spec": "BmHome", "normalize": True, "compets": None, "bm_quantile": 0.25,
    "ts_dur": [12, 72], "period": None, "resample_freq": "1min", "pctl": 2}})

raw = pd.read_hdf("data/processed/shaped_data.h5", "df")
for c in ("Date", "Update"):
    raw[c] = pd.to_datetime(raw[c])
df, *_ = filter_and_shape_data(raw.copy(), cfg)

# matchup window, exactly as resample_and_impute.py:90-91
df["TsStart"] = df.groupby("Matchup")["Update"].transform("min")
df["TsEnd"] = df.groupby("Matchup")["Update"].transform("max")
g = df.groupby("GroupId")["OddsMvt"].transform("std")
df = df[g > 0]
df = df[df["NumOddsMvt"] < 20]

span = (df["TsEnd"] - df["TsStart"]).dt.total_seconds()
df["X"] = np.where(
    span > 0, (df["Update"] - df["TsStart"]).dt.total_seconds() / span, np.nan)
df = df.sort_values(["GroupId", "Update"])
df["PRef"] = df.groupby("GroupId", sort=False)["OddsMvt"].transform("first")

# ------------------------------------------------ 1) entry delay per series
own_start = df.groupby("GroupId")["Update"].transform("min")
df["DelayH"] = (own_start - df["TsStart"]).dt.total_seconds() / 3600.0

df["Endog"] = df["Match"] - df["PRef"]
df["Exog"] = df["OddsMvt"] - df["PRef"]
df["ObsIdx"] = df.groupby("GroupId").cumcount()
df = df[df["ObsIdx"] > 0]
df = df[np.isfinite(df["X"])]
print(f"\nStichprobe: {len(df):,d} Zeilen, {df['GroupId'].nunique():,d} Serien")

ser = df.groupby("GroupId").agg(DelayH=("DelayH", "first"),
                                Matchup=("Matchup", "first"),
                                Bookies=("Bookies", "first"))
print("\n" + "=" * 72)
print("1) EINTRITTSVERSPÄTUNG (Stunden nach dem matchweiten Marktstart)")
print("=" * 72)
qs = [0, .01, .05, .10, .25, .50, .75, .90, .95, .99, 1]
for q in qs:
    print(f"  q{q:<5} {ser['DelayH'].quantile(q):10.3f} h")
print(f"\n  mean {ser['DelayH'].mean():.3f} h   sd {ser['DelayH'].std():.3f} h")
print(f"  exakt 0        : {(ser['DelayH'] == 0).sum():>7,d} "
      f"({(ser['DelayH'] == 0).mean() * 100:5.2f}%)")
for thr in (1 / 60, 1, 6, 24):
    print(f"  <= {thr:>6.3f} h    : {(ser['DelayH'] <= thr).sum():>7,d} "
          f"({(ser['DelayH'] <= thr).mean() * 100:5.2f}%)")
ser["DelayH"].describe().to_csv(f"{OUT}/delay_describe.csv")

# quartiles
ser["Q"], cuts = pd.qcut(ser["DelayH"], 4, labels=False, retbins=True,
                         duplicates="drop")
ser.reset_index().to_csv(f"{OUT}/delay_per_series.csv", index=False)
nq = int(ser["Q"].nunique())
print(f"\n  Quartilsgrenzen (h): "
      f"{', '.join(f'{c:.3f}' for c in cuts)}   -> {nq} Gruppen")
if nq < 4:
    print("  WARNUNG: Quartile degeneriert (zu viele exakte Nullen).")
for q in range(nq):
    s = ser.loc[ser["Q"] == q, "DelayH"]
    print(f"    Q{q + 1}  n={len(s):>7,d}  Median {s.median():8.3f} h  "
          f"Spanne [{s.min():.3f}, {s.max():.3f}]")
df = df.merge(ser[["Q"]], left_on="GroupId", right_index=True, how="left")

# ------------------------------------------- 2) stratified beta_1 curves
print("\n" + "=" * 72)
print("2) BETA_1 JE QUARTIL DER EINTRITTSVERSPÄTUNG")
print("=" * 72)
curves = {}
for q in range(nq):
    o = fit(df[df["Q"] == q], f"Q{q + 1}")
    o.to_csv(f"{OUT}/beta1_delay_Q{q + 1}.csv", index=False)
    curves[f"Q{q + 1}"] = o
full = fit(df, "volle Stichprobe")
full.to_csv(f"{OUT}/beta1_delay_full.csv", index=False)

# --------------------------------------------------- 3) interaction model
print("\n" + "=" * 72)
print("3) INTERAKTIONSMODELL  beta_1(Zeit, log Verspätung)")
print("=" * 72)
d = df[["Endog", "Exog", "X"]].copy()
d["D"] = np.log1p(df["DelayH"])          # log1p: Verspätung 0 ist häufig
d = d.astype(float)
d = d[np.isfinite(d).all(axis=1)]
dmed = [float(np.log1p(ser.loc[ser["Q"] == q, "DelayH"].median()))
        for q in range(nq)]
gx = np.linspace(0.01, 0.99, 100)
gg = pd.DataFrame([(x, dd) for dd in dmed for x in gx], columns=["X", "D"])

with localconverter(ro.default_converter + pandas2ri.converter):
    ro.globalenv["d"] = d
    ro.globalenv["gg"] = gg
ro.r("""
m <- bam(Endog ~ te(X, D, k = c(6, 6)) + te(X, D, k = c(6, 6), by = Exog),
         data = d, method = "fREML", discrete = TRUE)
Xp <- predict(m, transform(gg, Exog = 1), type = "lpmatrix") -
      predict(m, transform(gg, Exog = 0), type = "lpmatrix")
out <- data.frame(X = gg$X, D = gg$D,
                  beta_1 = as.vector(Xp %*% coef(m)),
                  se = sqrt(pmax(0, rowSums((Xp %*% vcov(m)) * Xp))))
sm <- summary(m)
""")
with localconverter(ro.default_converter + pandas2ri.converter):
    inter = ro.conversion.get_conversion().rpy2py(ro.globalenv["out"])
inter["pctl"] = inter["X"] * 100
inter["DelayH"] = np.expm1(inter["D"])
inter.to_csv(f"{OUT}/beta1_interaction.csv", index=False)
print(ro.r("paste(capture.output(print(sm$s.table)), collapse='\n')")[0])
for i, dd in enumerate(dmed):
    s = inter[np.isclose(inter["D"], dd)]
    print(f"  Q{i + 1} (Median {np.expm1(dd):7.3f} h)  beta1 mean "
          f"{s['beta_1'].mean():.3f}  Rand {s['beta_1'].iloc[0]:.3f} -> "
          f"{s['beta_1'].iloc[-1]:.3f}")

# ------------------------------------------------------ 4) control sample
print("\n" + "=" * 72)
print("4) KONTROLLE: nur die 24.568 vollständig beobachteten Serien")
print("=" * 72)
cand = pd.read_hdf(CACHE, key="true")[["Matchup", "Bookies"]]
cand["Matchup"] = cand["Matchup"].astype("int64")
key = df[["Matchup", "Bookies"]].astype({"Matchup": "int64"})
hit = pd.MultiIndex.from_frame(key).isin(
    pd.MultiIndex.from_frame(cand))
sub = df[hit]
print(f"  gematcht: {sub['GroupId'].nunique():,d} von {len(cand):,d} "
      f"Kandidatenserien ({len(sub):,d} Zeilen)")
sd = ser.loc[sub["GroupId"].unique(), "DelayH"]
print(f"  deren Verspätung: median {sd.median():.4f} h, mean {sd.mean():.4f} h,"
      f" q90 {sd.quantile(.9):.4f} h, exakt 0: {(sd == 0).mean() * 100:.1f}%")
print(f"  übrige Serien   : median "
      f"{ser.loc[~ser.index.isin(sub['GroupId'].unique()), 'DelayH'].median():.4f} h")
o = fit(sub, "nur vollständig beobachtete")
o.to_csv(f"{OUT}/beta1_fully_observed.csv", index=False)
curves["fully_observed"] = o

print("\n  Vergleich (mittleres beta_1 über die Kurve):")
print(f"    volle Stichprobe            {full['beta_1'].mean():.3f}")
print(f"    nur vollständig beobachtet  {o['beta_1'].mean():.3f}")
print(f"    Differenz                   {o['beta_1'].mean() - full['beta_1'].mean():+.3f}")
