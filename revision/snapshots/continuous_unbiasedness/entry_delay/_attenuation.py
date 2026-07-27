#!/usr/bin/env python3
"""Attenuations-Check für die Quartilskurven der Eintrittsverspätung (R2-C2).

Die Q4-Kurve fällt am Fensterende auf beta_1 = 0,482. Klassischer Messfehler
im Regressor dämpft die Steigung um die Reliabilität
lambda = var(x*)/(var(x*)+sigma_u^2). Hat Q4 schlicht deutlich weniger
Regressorvarianz als Q1, wäre der Abfall ein Varianzartefakt und keine
Überreaktion.

Ausgabe je Verspätungsquartil:
  1) var(Exog) = var(p_t - p_ref), sd, mittlere absolute Preisbewegung
  2) Fensterlänge (Matchup-Fenster, eigenes Fenster, Beobachtungszahl)
  3) var(Exog) nach Fensterposition (X-Dezile) -- entscheidend, weil der
     Q4-Abfall am Fensterende sitzt
  4) die Attenuations-Arithmetik selbst: welches sigma_u^2 wäre nötig, und
     was sagt dasselbe sigma_u^2 für die anderen Quartile voraus

Stichprobenaufbau identisch zu `_entry_delay.py`. Rein diagnostisch.
"""

import sys
import tempfile

import numpy as np
import pandas as pd
from omegaconf import OmegaConf

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

OUT = "revision/snapshots/continuous_unbiasedness/entry_delay"
# Cache außerhalb des Repos; löschen erzwingt einen Neuaufbau
FRAME = f"{tempfile.gettempdir()}/pfd_delay_frame.parquet"
QL = {0: "Q1 (zeitgleich)", 1: "Q2", 2: "Q3", 3: "Q4 (spät)"}

pd.set_option("display.width", 200)


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


try:
    df = pd.read_parquet(FRAME)
    print(f"Frame aus Cache: {len(df):,d} Zeilen")
except (FileNotFoundError, OSError):
    df = build()
    print(f"Frame neu gebaut: {len(df):,d} Zeilen")

ser = df.groupby("GroupId").agg(
    DelayH=("DelayH", "first"), SpanH=("SpanH", "first"),
    OwnSpanH=("OwnSpanH", "first"), OwnXSpan=("OwnXSpan", "first"),
    NumOddsMvt=("NumOddsMvt", "first"), NObs=("X", "size"),
    LastExog=("Exog", "last"))
ser["Q"] = pd.qcut(ser["DelayH"], 4, labels=False, duplicates="drop")
df = df.merge(ser[["Q"]], left_on="GroupId", right_index=True, how="left")
print(f"Serien: {len(ser):,d}   Quartile: {sorted(ser['Q'].unique())}")


def block(title):
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def row(label, d, s):
    return {"Quartil": label, "n_Serien": len(s), "n_Zeilen": len(d),
            "Verspätung_Median_h": s["DelayH"].median(),
            "var_Exog": d["Exog"].var(), "sd_Exog": d["Exog"].std(),
            "mean_abs_Exog": d["Exog"].abs().mean(),
            "mean_abs_Endbewegung": s["LastExog"].abs().mean(),
            "var_Endog": d["Endog"].var()}


# --------------------------------------------------- 1) Regressor-Varianz
block("1) REGRESSOR-VARIANZ  var(Exog) = var(p_t - p_ref)  je Quartil")
t1 = pd.DataFrame([row(QL[q], df[df["Q"] == q], ser[ser["Q"] == q])
                   for q in range(4)]
                  + [row("volle Stichprobe", df, ser)])
t1["var_Exog_rel_Q1"] = t1["var_Exog"] / t1["var_Exog"].iloc[0]
print(t1.to_string(index=False, float_format=lambda v: f"{v:,.4f}"))

# --------------------------------------------------------- 2) Fensterlänge
block("2) FENSTERLÄNGE je Quartil")


def wrow(label, s):
    return {"Quartil": label,
            "Matchup_Fenster_h_Median": s["SpanH"].median(),
            "eigenes_Fenster_h_Median": s["OwnSpanH"].median(),
            "eigenes_Fenster_h_Mittel": s["OwnSpanH"].mean(),
            "Anteil_am_Matchup_Fenster": s["OwnXSpan"].mean(),
            "NumOddsMvt_Median": s["NumOddsMvt"].median(),
            "Beob_je_Serie_Median": s["NObs"].median()}


t2 = pd.DataFrame([wrow(QL[q], ser[ser["Q"] == q]) for q in range(4)]
                  + [wrow("volle Stichprobe", ser)])
print(t2.to_string(index=False, float_format=lambda v: f"{v:,.4f}"))

# ------------------------------------------------- 3) Varianz über die Achse
block("3) var(Exog) NACH FENSTERPOSITION (X-Dezile) -- entscheidend, weil der"
      "\n   Q4-Abfall am Fensterende sitzt")
df["Xbin"] = pd.cut(df["X"], np.arange(0, 1.01, 0.1), include_lowest=True)
piv_v = df.pivot_table(index="Xbin", columns="Q", values="Exog",
                       aggfunc="var", observed=True)
piv_n = df.pivot_table(index="Xbin", columns="Q", values="Exog",
                       aggfunc="size", observed=True)
piv_v.columns = [QL[c] for c in piv_v.columns]
piv_n.columns = [QL[c] for c in piv_n.columns]
print("\nvar(Exog):")
print(piv_v.to_string(float_format=lambda v: f"{v:.5f}"))
print("\nrelativ zu Q1 im selben Dezil:")
print(piv_v.div(piv_v.iloc[:, 0], axis=0).to_string(
    float_format=lambda v: f"{v:.3f}"))
print("\nZeilen je Zelle:")
print(piv_n.to_string(float_format=lambda v: f"{v:,.0f}"))

# ------------------------------------------------ 4) Attenuations-Arithmetik
block("4) REICHT ATTENUATION AUS?  klassischer EIV-Faktor "
      "lambda = var(x*)/(var(x*)+sigma_u^2)")
tail = df[df["X"] > 0.9]
v = {q: tail.loc[tail["Q"] == q, "Exog"].var() for q in range(4)}
end = {}
for q in range(4):
    c = pd.read_csv(f"{OUT}/beta1_delay_Q{q + 1}.csv")
    end[q] = (c["beta_1"].iloc[-1], c["se"].iloc[-1])

print("\nam Fensterende (X > 0,9):")
for q in range(4):
    b, se = end[q]
    print(f"  {QL[q]:<16s} var(Exog)={v[q]:.5f}  rel. Q1={v[q] / v[0]:5.3f}"
          f"   beta_1 Ende={b:6.3f} (SE {se:.3f})")

# Welches gemeinsame sigma_u^2 müsste vorliegen, damit Attenuation allein Q4
# von 1 auf den beobachteten Wert drückt -- und was folgt daraus für Q1?
b4 = end[3][0]
sig2 = v[3] * (1.0 / b4 - 1.0)
print(f"\n  benötigtes sigma_u^2, damit Q4 allein durch Attenuation von 1 auf"
      f" {b4:.3f} fällt:\n    sigma_u^2 = {sig2:.5f}  "
      f"({sig2 / v[3]:.2f}-fache der Q4-Regressorvarianz)")
print("  dasselbe sigma_u^2 auf die anderen Quartile angewandt:")
for q in range(4):
    print(f"    {QL[q]:<16s} vorhergesagt {v[q] / (v[q] + sig2):6.3f}   "
          f"beobachtet {end[q][0]:6.3f}")

# umgekehrt: Q1 als (nahezu) unverzerrt nehmen und dessen sigma_u^2 hochrechnen
sig2_q1 = v[0] * (1.0 / end[0][0] - 1.0)
print(f"\n  umgekehrt: Q1 als unverzerrt gesetzt -> sigma_u^2 = {sig2_q1:.6f};"
      f"\n  damit vorhergesagt für Q4: beta_1 = "
      f"{v[3] / (v[3] + sig2_q1):.3f}  gegenüber beobachtet {b4:.3f}")

t1.to_csv(f"{OUT}/attenuation_by_quartile.csv", index=False)
t2.to_csv(f"{OUT}/window_length_by_quartile.csv", index=False)
piv_v.to_csv(f"{OUT}/var_exog_by_position.csv")
print(f"\ngeschrieben: {OUT}/attenuation_by_quartile.csv, "
      f"window_length_by_quartile.csv, var_exog_by_position.csv")
