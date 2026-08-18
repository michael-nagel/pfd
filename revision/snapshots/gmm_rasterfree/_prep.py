#!/usr/bin/env python3
"""Vorklaerung fuer die rasterfreie Schaetzung. NUR Diagnostik, kein Schaetzer.

(1) Zeitdefinition: verstrichene Zeit ab eigenem Opening vs. Stunden bis
    Kickoff - unterscheidbar?
(2) Verteilung von log[(P - omega)^2]
(3) Bodensatz K und Jensen-Luecke
"""

import sys

import numpy as np
import pandas as pd
from omegaconf import OmegaConf

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

H = np.timedelta64(1, "h")
cfg = OmegaConf.create({"estimation": {
    "spec": "BmHome", "normalize": True, "compets": None,
    "bm_quantile": 0.25, "ts_dur": [12, 72], "period": None,
    "resample_freq": "1min", "pctl": 2}})
raw = pd.read_hdf("data/processed/shaped_data.h5", "df")
for c in ("Date", "Update"):
    raw[c] = pd.to_datetime(raw[c])
df, *_ = filter_and_shape_data(raw.copy(), cfg)
gstd = df.groupby("GroupId")["OddsMvt"].transform("std")
df = df[gstd > 0].copy()
print(f"Echte Beobachtungen: {len(df):,d} in "
      f"{df['GroupId'].nunique():,d} Serien\n")

df["own_start"] = df.groupby("GroupId")["Update"].transform("min")
df["own_end"] = df.groupby("GroupId")["Update"].transform("max")
df["m_end"] = df.groupby("Matchup")["Update"].transform("max")
df["t_elapsed"] = (df["Update"] - df["own_start"]) / H
df["t_tokick"] = (df["m_end"] - df["Update"]) / H

p = df["OddsMvt"].to_numpy(float)
w = df["Match"].to_numpy(float)
err2 = (p - w) ** 2

print("=" * 74)
print("(1) ZEITDEFINITION")
print("=" * 74)
z = df["t_elapsed"] == 0
print(f"  Beobachtungen mit t_elapsed = 0 (eigenes Opening): "
      f"{int(z.sum()):,d} ({z.mean() * 100:.1f} %)")
print(f"  -> log(t) dort nicht definiert; Offset oder Verwerfen noetig")
print(f"\n  t_elapsed (h): " + df["t_elapsed"].describe(
    percentiles=[.01, .25, .5, .75, .99]).round(3).to_string().replace(
    "\n", "  "))
print(f"\n  t_tokick  (h): " + df["t_tokick"].describe(
    percentiles=[.01, .25, .5, .75, .99]).round(3).to_string().replace(
    "\n", "  "))
mask = (df["t_elapsed"] > 0) & (df["t_tokick"] > 0)
le = np.log(df.loc[mask, "t_elapsed"].to_numpy(float))
lk = np.log(df.loc[mask, "t_tokick"].to_numpy(float))
print(f"\n  corr(log t_elapsed, log t_tokick) = {np.corrcoef(le, lk)[0, 1]:.4f}"
      f"   (n = {mask.sum():,d})")
print("  -> die beiden Achsen sind empirisch klar trennbar")

print("\n" + "=" * 74)
print("(2) VERTEILUNG VON log[(P - omega)^2]")
print("=" * 74)
ly = np.log(err2)
print(f"  P-Bereich: {p.min():.4f} bis {p.max():.4f}  "
      f"-> (P-omega)^2 in [{err2.min():.6f}, {err2.max():.6f}]")
print(f"  exakte Nullen: {int((err2 == 0).sum())}")
qs = [0, .001, .01, .05, .25, .5, .75, .95, 1]
print("\n  Perzentile von log[(P-omega)^2]:")
for q in qs:
    print(f"    {q * 100:6.1f} %: {np.quantile(ly, q):8.3f}")
print(f"\n  Mittel {ly.mean():.3f}   sd {ly.std():.3f}")
print(f"  Anteil unter -5: {(ly < -5).mean() * 100:.3f} %   "
      f"unter -6: {(ly < -6).mean() * 100:.4f} %")
print("  -> nach unten beschraenkt, weil P nie 0 oder 1 erreicht;")
print("     kein Beobachtungspunkt mit unbeschraenktem Hebel")

print("\n" + "=" * 74)
print("(3) BODENSATZ K UND JENSEN-LUECKE")
print("=" * 74)
floor = p * (1 - p)
print(f"  E[(P - omega)^2]  = {err2.mean():.6f}")
print(f"  E[P(1-P)]         = {floor.mean():.6f}   <- irreduzible")
print(f"                                              Bernoulli-Varianz")
print(f"  Differenz         = {err2.mean() - floor.mean():.6f}")
print(f"  Anteil des Bodensatzes am Gesamtfehler: "
      f"{floor.mean() / err2.mean() * 100:.2f} %")
print("\n  Zerlegung ueber die Zeit (Quintile von t_elapsed):")
qb = pd.qcut(df["t_elapsed"].rank(method="first"), 5,
             labels=["Q1 frueh", "Q2", "Q3", "Q4", "Q5 spaet"])
tab = pd.DataFrame({"err2": err2, "floor": floor, "q": qb}).groupby(
    "q", observed=True).mean()
tab["ueberschuss"] = tab["err2"] - tab["floor"]
print("    " + tab.round(6).to_string().replace("\n", "\n    "))
print("\n  -> der Ueberschuss ueber den Bodensatz ist die Groesse,")
print("     die ueberhaupt zerfallen kann")

print("\n  Jensen-Luecke E[log Y] - log E[Y] nach Preisniveau:")
pb = pd.cut(np.minimum(p, 1 - p), [0, .1, .2, .3, .4, .5])
jt = pd.DataFrame({"ly": ly, "y": err2, "b": pb}).groupby("b", observed=True)
out = pd.DataFrame({"E_log_Y": jt["ly"].mean(),
                    "log_E_Y": np.log(jt["y"].mean()),
                    "n": jt["y"].size()})
out["Luecke"] = out["E_log_Y"] - out["log_E_Y"]
print("    " + out.round(4).to_string().replace("\n", "\n    "))
print("\n  -> die Luecke haengt stark vom Preisniveau ab. Da sich das")
print("     Preisniveau ueber das Fenster systematisch veraendert, geht")
print("     sie NICHT in den Achsenabschnitt, sondern in die STEIGUNG.")

print("\n  Preisniveau ueber die Zeit (Median von min(P, 1-P)):")
print("    " + pd.DataFrame({"m": np.minimum(p, 1 - p), "q": qb}).groupby(
    "q", observed=True)["m"].median().round(4).to_string().replace(
    "\n", "\n    "))
