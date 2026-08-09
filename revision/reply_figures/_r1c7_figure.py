#!/usr/bin/env python3
"""Abbildung fuer die R1-vii-Antwort: der Koeffizientenpfad, alt gegen neu.

Die Belegabbildung in `../snapshots/continuous_unbiasedness/main_spec/` ist
deutsch beschriftet und traegt Diagnosekurven, die den Referee nicht
interessieren. Diese Fassung ist englisch, auf die Aussage reduziert und
zeigt zusaetzlich das SIMULTANE Band -- genau das, wonach R1-vii fragt.

Links die neue Spezifikation: beta_1 als glatte Funktion der Zeit bis
Anpfiff, mit punktweisem und simultanem 95-%-Band aus dem Cluster-Bootstrap
(B = 100, Cluster = Matchup). Rechts die publizierte Fassung: 50 getrennte
Regressionen auf dem Perzentilraster mit ihren punktweisen, modellbasierten
Intervallen. Gleiche y-Achse, damit die Niveaus vergleichbar sind; die
x-Achsen sind verschieden und deshalb getrennt gezeichnet.
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

SPEC = "revision/snapshots/continuous_unbiasedness/main_spec"
BASE = "revision/snapshots/C_normalized/beta1_curve.csv"
OUT = "revision/reply_figures/r1c7_coefficient_path"

INK, MUTED, GREY = "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE = "#2a78d6", "#eb6834"

plt.rcParams.update({
    "figure.dpi": 150, "savefig.bbox": "tight",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": GREY, "axes.labelcolor": MUTED, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "font.size": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
})

band = pd.read_csv(f"{SPEC}/simultaneous_band.csv")
pub = pd.read_csv(BASE)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 3.6))

# ------------------------------------------------- links: neue Spezifikation
h = band["hours"]
ax1.fill_between(h, band["sim_lo"], band["sim_up"], color=BLUE, alpha=0.13,
                 lw=0, label="95% simultaneous band")
ax1.fill_between(h, band["pw_lo"], band["pw_up"], color=BLUE, alpha=0.28,
                 lw=0, label="95% pointwise band")
ax1.plot(h, band["beta_1"], color=BLUE, lw=1.8, label=r"$\beta_1(t)$, smooth")
ax1.axhline(1, color=INK, lw=0.9, ls=(0, (4, 3)))

ax1.set_xscale("log")
ax1.set_xlim(band["hours"].max(), band["hours"].min())
ax1.set_xticks([48, 24, 12, 6, 3, 1, 0.25, 0.1])
ax1.set_xticklabels(["48", "24", "12", "6", "3", "1", "0.25", "0.1"])
ax1.set_xlabel("hours before kickoff (kickoff at right)")
ax1.set_ylabel(r"$\beta_1$")
ax1.set_title("Revised: one smooth coefficient path", fontsize=10,
              color=INK, loc="left", pad=10)
ax1.legend(frameon=False, fontsize=7.5, loc="lower left", labelcolor=MUTED)

# ------------------------------------------- rechts: publizierte Fassung
ax2.errorbar(pub["pctl"], pub["beta_1"],
             yerr=1.959964 * pub["std_beta_1"],
             fmt="o", ms=2.6, lw=0.8, color=ORANGE, ecolor=ORANGE,
             elinewidth=0.7, capsize=1.4, alpha=0.85,
             label="50 separate regressions, pointwise 95%")
ax2.axhline(1, color=INK, lw=0.9, ls=(0, (4, 3)))

ax2.set_xlabel("percentile of the betting window")
ax2.set_ylabel(r"$\beta_1$")
ax2.set_title("Submitted: 50 pointwise estimates", fontsize=10,
              color=INK, loc="left", pad=10)
ax2.legend(frameon=False, fontsize=7.5, loc="upper right", labelcolor=MUTED)

# Gemeinsame y-Achse. Der Randpunkt der publizierten Kurve (Perzentil 2,
# beta_1 = 2,59) wuerde beide Panels stauchen und ist selbst ein Artefakt des
# Fensterrands; die Achse wird deshalb ohne ihn gesetzt und der Punkt als
# ausserhalb ausgewiesen, statt die Kurven unleserlich zu machen.
rest = pub.iloc[1:]
lo = min(band["sim_lo"].min(), (rest["beta_1"] - 2 * rest["std_beta_1"]).min())
hi = max(band["sim_up"].max(), (rest["beta_1"] + 2 * rest["std_beta_1"]).max())
pad = 0.06 * (hi - lo)
lo, hi = lo - pad, hi + pad
for ax in (ax1, ax2):
    ax.set_ylim(lo, hi)

n_out = int(((pub["beta_1"] > hi) | (pub["beta_1"] < lo)).sum())
if n_out:
    ax2.annotate(f"{n_out} estimate off scale\n(percentile 2: "
                 f"{pub['beta_1'].iloc[0]:.2f})",
                 xy=(pub["pctl"].iloc[0], hi), xytext=(8, -26),
                 textcoords="offset points", fontsize=7, color=MUTED,
                 arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.7))

fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(f"{OUT}.{ext}")
print(f"-> {OUT}.pdf / .png   y-Achse {lo - pad:.2f} .. {hi + pad:.2f}")
print(f"   Perzentilkurve: {len(pub)} Punkte, "
      f"glatte Kurve: {len(band)} Gitterpunkte bis {band['hours'].max():.1f} h")
