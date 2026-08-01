#!/usr/bin/env python3
"""Randdiagnostik-Abbildung: voller beobachteter Bereich und Datendichte.

Zeigt, was das 1.-99.-Perzentil-Gitter der Hauptabbildung abschneidet, wie
stabil der linke Rand über k ist, und dass der Knick bei ~45 h eine
Eigenschaft der UNPENALISIERTEN festen Basis ist (die die lme4-/Sandwich-/
Bootstrap-Route braucht), nicht der penalisierten mgcv-Schätzung.
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

OUT = "revision/snapshots/continuous_unbiasedness/main_spec"
GREY, INK, MUTED = "#8a8984", "#0b0b0b", "#52514e"
CAT1, CAT2 = "#2a78d6", "#eb6834"
KC = ["#86b6ef", "#3987e5", "#0d366b"]        # k = 6, 10, 20

cur = pd.read_csv(f"{OUT}/edge_beta1_fullrange.csv")
cr = pd.read_csv(f"{OUT}/cluster_robust_beta1.csv")
frame = pd.read_parquet("/tmp/pfd_mainspec_frame2.parquet")
h = frame["HoursToKick"]
LO, HI = h.quantile(.01), h.quantile(.99)

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 9,
    "axes.edgecolor": "#c9c8c3", "axes.linewidth": .8,
    "axes.labelcolor": MUTED, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "figure.facecolor": "white", "axes.facecolor": "white",
})


def dress(ax, title, sub):
    ax.set_title(title, fontsize=11, color=INK, loc="left", pad=15,
                 fontweight="medium")
    ax.text(0, 1.012, sub, transform=ax.transAxes, fontsize=8,
            color=MUTED, va="bottom", ha="left")
    ax.grid(True, color="#ecebe7", linewidth=.7)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def axis(ax):
    ax.set_xscale("log")
    ax.set_xlim(h.max() * 1.2, h.min() * .8)
    ax.set_xticks([168, 72, 24, 12, 6, 1, .25, .05])
    ax.set_xticklabels(["168", "72", "24", "12", "6", "1", "0,25", "0,05"])
    ax.axvspan(h.max() * 1.2, HI, color="#f2f1ed", zorder=0)
    ax.axvspan(LO, h.min() * .8, color="#f2f1ed", zorder=0)


fig, axes = plt.subplots(2, 1, figsize=(11, 8.4), height_ratios=[2.1, 1],
                         sharex=True)

# ---- (a) beta_1 über den vollen Bereich -----------------------------------
ax = axes[0]
ax.axhline(1, color=GREY, linewidth=.9, linestyle=(0, (4, 3)), zorder=1)
for k, c in zip((6, 10, 20), KC, strict=True):
    s = cur[cur["k"] == k]
    ax.plot(s["hours"], s["beta_1"], color=c, linewidth=1.8,
            label=f"mgcv M_c penalisiert, k = {k}", zorder=3)
ax.plot(cr["hours"], cr["beta_1"], color=CAT2, linewidth=1.8,
        linestyle=(0, (4, 2)), zorder=4,
        label="feste Basis k = 6 (Sandwich/Bootstrap, Hauptabbildung)")
ax.fill_between(cr["hours"], cr["ci_lo"], cr["ci_up"], color=CAT2, alpha=.13,
                linewidth=0, zorder=2, label="95 % CR1 dazu")
axis(ax)
ax.set_ylim(-0.6, 2.6)
dress(ax, "β₁ über den vollen beobachteten Bereich",
      "grau hinterlegt: ausserhalb des 1.–99.-Perzentil-Gitters der "
      "Hauptabbildung (je 1 % der Beobachtungen)")
ax.set_ylabel("β₁")
ax.legend(frameon=False, fontsize=7.8, loc="lower center", labelcolor=MUTED,
          ncol=2, borderaxespad=.4)
ax.annotate("Knick nur bei fester Basis", xy=(45, .83), xytext=(90, .12),
            fontsize=7.8, color=CAT2, ha="center",
            arrowprops=dict(arrowstyle="->", color=CAT2, linewidth=.8))

# ---- (b) Datendichte -------------------------------------------------------
ax = axes[1]
bins = np.exp(np.linspace(np.log(h.min()), np.log(h.max()), 60))
ax.hist(h, bins=bins, color=CAT1, edgecolor="none")
axis(ax)
dress(ax, "Datendichte über die Achse",
      f"{len(frame):,d} Beobachtungen · Bins gleichmäßig in log(Stunden)")
ax.set_xlabel("Stunden vor Anpfiff (log, Anpfiff rechts)")
ax.set_ylabel("Beobachtungen")
ax.text(.02, .93,
        f"> 72 h    {(h > 72).sum():>8,d}  ({(h > 72).mean() * 100:4.2f} %)\n"
        f"> 59,9 h  {(h > HI).sum():>8,d}  ({(h > HI).mean() * 100:4.2f} %)"
        "   Trim\n"
        f"> 48 h    {(h > 48).sum():>8,d}  ({(h > 48).mean() * 100:4.2f} %)\n"
        f"> 24 h    {(h > 24).sum():>8,d}  ({(h > 24).mean() * 100:4.2f} %)",
        transform=ax.transAxes, ha="left", va="top", fontsize=7.6,
        color=MUTED, family="monospace", linespacing=1.5)

fig.tight_layout(pad=1.8, h_pad=2.4)
for ext in ("png", "pdf"):
    fig.savefig(f"{OUT}/main_spec_edge.{ext}", dpi=170, bbox_inches="tight")
print(f"-> {OUT}/main_spec_edge.png / .pdf")
