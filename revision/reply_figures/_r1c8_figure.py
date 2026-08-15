#!/usr/bin/env python3
"""Abbildung der R1-viii-Antwort: die Kalibrierungssteigung ueber die Zeit.

lambda(X) aus `Match = a(X) + lambda(X) * p + Kovariaten`, natural cubic
spline df = 4 in X = log(Stunden bis Anpfiff), CR1 auf Matchup. Dieselbe
Basis, dasselbe Gitter und dieselbe Achse wie die beta_1-Kurve der
R1-vii-Antwort, damit die beiden Abbildungen nebeneinander lesbar sind.

Der Punkt der Abbildung ist ein NULLBEFUND: die Kurve laeuft nicht auf 1 zu.
Deshalb ist die 1 als Referenzlinie eingezeichnet und das Band punktweise --
anders als bei beta_1, wo die simultane Lesart der Streitpunkt war.

Quelle: `../snapshots/flb_calibration/continuous_calibration_grid.csv`.
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

SRC = "revision/snapshots/flb_calibration/continuous_calibration_grid.csv"
OUT = "revision/reply_figures/r1c8_calibration_path"
HMAX = 48.0

INK, MUTED, GREY = "#0b0b0b", "#52514e", "#8a8984"
RED = "#c0504d"

plt.rcParams.update({
    "figure.dpi": 150, "savefig.bbox": "tight",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": GREY, "axes.labelcolor": MUTED, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "font.size": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
})

d = pd.read_csv(SRC)
d = d[d["hours"] <= HMAX]

fig, ax = plt.subplots(figsize=(6.6, 3.1))
ax.fill_between(d["hours"], d["pw_lo"], d["pw_up"], color=RED, alpha=0.18,
                lw=0, label="95% pointwise band (match-clustered)")
ax.plot(d["hours"], d["lambda"], color=RED, lw=1.9,
        label=r"$\lambda(X)$, natural cubic spline, $df=4$")
ax.axhline(1, color=INK, lw=0.9, ls=(0, (4, 3)))
ax.text(HMAX, 1.002, "no favorite-longshot bias ($\\lambda = 1$)", fontsize=7,
        color=MUTED, va="bottom", ha="left")
ax.set_ylabel(r"$\lambda$")
ax.set_xlabel("hours before kickoff (log scale, kickoff at right)")
ax.legend(frameon=False, fontsize=7.5, loc="upper right", labelcolor=MUTED)

ax.set_xscale("log")
ax.set_xlim(HMAX, d["hours"].min())
ax.set_xticks([48, 24, 12, 6, 3, 1, 0.25, 0.1])
ax.set_xticklabels(["48", "24", "12", "6", "3", "1", "0.25", "0.1"])

for ext in ("pdf", "png"):
    fig.savefig(f"{OUT}.{ext}")
print(f"-> {OUT}.pdf / .png")
print(f"   lambda {d['lambda'].min():.3f}-{d['lambda'].max():.3f} "
      f"ueber {len(d)} Gitterpunkte bis {HMAX:.0f} h")
print(f"   untere Bandgrenze min {d['pw_lo'].min():.3f} "
      f"(ueberdeckt 1: {'ja' if (d['pw_lo'] < 1).any() else 'nein'})")
