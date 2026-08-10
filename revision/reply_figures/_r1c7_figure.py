#!/usr/bin/env python3
"""Abbildung 2 der R1-vii-Antwort: die revidierte Fassung, zwei Panels.

Oben:  beta_1 als glatte Funktion von X = log(Stunden bis Anpfiff), natural
       cubic spline df = 4 (lineare Randbedingungen), mit SIMULTANEM
       95-%-Band. Punktweise Baender werden bewusst nicht gezeigt -- der
       Referee kritisiert genau die punktweise Lesart.
Unten: RMSE der PREISE gegen die Zeit bis Anpfiff, rein deskriptiv: Wurzel
       des mittleren quadrierten Prognosefehlers (p(t) - Ausgang)^2, gebinnt,
       ohne Modell und ohne Glaettung. Das ist eine ANDERE Groesse als das
       untere Panel der eingereichten Abbildung, das die Residuen der 50
       Perzentilregressionen zeigt.

Gemeinsame logarithmische x-Achse, Anpfiff rechts.

Quelle: `../snapshots/continuous_unbiasedness/main_spec/ns4_beta1.csv` und
`ns4_rmse_bins.csv`.
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

SPEC = "revision/snapshots/continuous_unbiasedness/main_spec"
OUT = "revision/reply_figures/r1c7_revised_path"
HMAX = 48.0

INK, MUTED, GREY = "#0b0b0b", "#52514e", "#8a8984"
BLUE = "#2a78d6"

plt.rcParams.update({
    "figure.dpi": 150, "savefig.bbox": "tight",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": GREY, "axes.labelcolor": MUTED, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "font.size": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
})

b = pd.read_csv(f"{SPEC}/ns4_final_band.csv")   # Band aus dem Cluster-Bootstrap
b = b[b["hours"] <= HMAX]
r = pd.read_csv(f"{SPEC}/ns4_rmse_bins.csv")

fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(6.6, 5.4), sharex=True,
    gridspec_kw={"height_ratios": [1.45, 1], "hspace": 0.16})

# ------------------------------------------------------------- oben: beta_1
ax1.fill_between(b["hours"], b["sim_lo"], b["sim_up"], color=BLUE,
                 alpha=0.20, lw=0,
                 label="95% simultaneous band (cluster bootstrap, $B=100$)")
ax1.plot(b["hours"], b["beta_1"], color=BLUE, lw=1.9,
         label=r"$\beta_1(X)$, natural cubic spline, $df=4$")
ax1.axhline(1, color=INK, lw=0.9, ls=(0, (4, 3)))
ax1.set_ylabel(r"$\beta_1$")
ax1.legend(frameon=False, fontsize=7.5, loc="lower left", labelcolor=MUTED)
ax1.text(0.995, 0.94, "underreaction above 1, overreaction below",
         transform=ax1.transAxes, ha="right", fontsize=7, color=MUTED)

# --------------------------------------------------------- unten: RMSE
# Referenzlinie Muenzwurf. Ohne sie steht die Kurve auf einer 0,013 breiten
# Achse und das Rauschen wirkt dramatisch, obwohl es rund 1 % des Niveaus
# ist -- genau der Eindruck, den der Text gerade nicht erwecken soll.
ax2.axhline(0.5, color=INK, lw=0.9, ls=(0, (4, 3)))
ax2.text(HMAX, 0.4975, "uninformed forecast ($p \\equiv 0.5$)", fontsize=7,
         color=MUTED, va="top", ha="left")
ax2.plot(r["h_mid"], r["rmse"], color=MUTED, lw=1.2, marker="o", ms=3.2,
         mfc="white", mec=MUTED, mew=0.9,
         label="RMSE of the price as a forecast, binned")
ax2.set_ylim(0.442, 0.506)
ax2.set_ylabel("RMSE")
ax2.set_xlabel("hours before kickoff (log scale, kickoff at right)")
ax2.legend(frameon=False, fontsize=7.5, loc="lower left", labelcolor=MUTED)

ax2.set_xscale("log")
ax2.set_xlim(HMAX, b["hours"].min())
ax2.set_xticks([48, 24, 12, 6, 3, 1, 0.25, 0.1])
ax2.set_xticklabels(["48", "24", "12", "6", "3", "1", "0.25", "0.1"])

fig.align_ylabels([ax1, ax2])
for ext in ("pdf", "png"):
    fig.savefig(f"{OUT}.{ext}")
print(f"-> {OUT}.pdf / .png")
print(f"   beta_1 {b['beta_1'].min():.3f}-{b['beta_1'].max():.3f}, "
      f"RMSE {r['rmse'].min():.4f}-{r['rmse'].max():.4f} "
      f"ueber {len(r)} Bins")
