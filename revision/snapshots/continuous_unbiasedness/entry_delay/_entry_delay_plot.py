#!/usr/bin/env python3
"""Figure for the entry-delay control (4 panels)."""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

OUT = "revision/snapshots/continuous_unbiasedness/entry_delay"

# ordinal ramp, one hue light->dark (validated: monotone L, gaps >= .06,
# light end 2.06:1 on the light surface)
QC = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
GREY, INK, MUTED = "#8a8984", "#0b0b0b", "#52514e"
CAT1, CAT2 = "#2a78d6", "#eb6834"

ser = pd.read_csv(f"{OUT}/delay_per_series.csv")
if "Q" not in ser:  # same deterministic cut as entry_delay.py
    ser["Q"] = pd.qcut(ser["DelayH"], 4, labels=False, duplicates="drop")
qs = {q: pd.read_csv(f"{OUT}/beta1_delay_Q{q}.csv") for q in (1, 2, 3, 4)}
full = pd.read_csv(f"{OUT}/beta1_delay_full.csv")
fobs = pd.read_csv(f"{OUT}/beta1_fully_observed.csv")
inter = pd.read_csv(f"{OUT}/beta1_interaction.csv")
base = pd.read_csv("revision/snapshots/C_normalized/beta1_curve.csv")

qmed = ser.groupby("Q")["DelayH"].median()
qmax = ser.groupby("Q")["DelayH"].max()
qlab = {q: f"Q{q}  Median {qmed[q - 1]:.2f} h" for q in (1, 2, 3, 4)}

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 9,
    "axes.edgecolor": "#c9c8c3", "axes.linewidth": .8,
    "axes.labelcolor": MUTED, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "figure.facecolor": "white", "axes.facecolor": "white",
})

fig, axes = plt.subplots(2, 2, figsize=(12.5, 9))


def dress(ax, title, sub):
    ax.set_title(title, fontsize=11, color=INK, loc="left", pad=15,
                 fontweight="medium")
    ax.text(0, 1.012, sub, transform=ax.transAxes, fontsize=8,
            color=MUTED, va="bottom", ha="left")
    ax.grid(True, color="#ecebe7", linewidth=.7)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def unity(ax):
    ax.axhline(1, color=GREY, linewidth=.9, linestyle=(0, (4, 3)), zorder=1)


# ---- (a) delay distribution ------------------------------------------------
ax = axes[0, 0]
shown = ser["DelayH"][ser["DelayH"] <= 24]
ax.hist(shown, bins=np.linspace(0, 24, 97), color=CAT1, edgecolor="none")
top = ax.get_ylim()[1]
for i in range(3):
    ax.axvline(qmax[i], color=GREY, linewidth=.9, linestyle=(0, (3, 3)))
    ax.annotate(f"Q{i + 1}|Q{i + 2}", xy=(qmax[i], top * (.80 - .11 * i)),
                xytext=(5, 0), textcoords="offset points", fontsize=7.5,
                color=MUTED, ha="left", va="center")
dress(ax, "Eintrittsverspätung je Serie",
      "Stunden nach dem matchweiten Marktstart")
ax.set_xlabel("Verspätung (h)")
ax.set_ylabel("Serien")
ax.text(.97, .95,
        f"n          {len(ser):>8,d}\n"
        f"exakt 0    {(ser['DelayH'] == 0).mean() * 100:>7.1f} %\n"
        f"Median     {ser['DelayH'].median():>7.2f} h\n"
        f"Mittel     {ser['DelayH'].mean():>7.2f} h\n"
        f"99. Pctl   {ser['DelayH'].quantile(.99):>7.1f} h\n"
        f"Max        {ser['DelayH'].max():>7.1f} h\n"
        f"> 24 h     {(ser['DelayH'] > 24).mean() * 100:>7.1f} % (n. gezeigt)",
        transform=ax.transAxes, ha="right", va="top", fontsize=7.6,
        color=MUTED, family="monospace", linespacing=1.5)

# ---- (b) stratified curves -------------------------------------------------
ax = axes[0, 1]
unity(ax)
ax.plot(base["pctl"], base["beta_1"], color=GREY, linewidth=1.4,
        linestyle=(0, (5, 2)), label="Baseline (imputiert)", zorder=2)
for q in (1, 2, 3, 4):
    o = qs[q]
    ax.fill_between(o["pctl"], o["beta_1"] - 1.96 * o["se"],
                    o["beta_1"] + 1.96 * o["se"], color=QC[q - 1], alpha=.16,
                    linewidth=0)
    ax.plot(o["pctl"], o["beta_1"], color=QC[q - 1], linewidth=2,
            label=qlab[q], zorder=3)
dress(ax, "β₁ je Quartil der Eintrittsverspätung",
      "getrennte Fits · echte Beobachtungen · Matchup-Perzentilachse · k=6")
ax.set_xlabel("Perzentil des Matchup-Fensters")
ax.set_ylabel("β₁")
ax.legend(frameon=False, fontsize=8, loc="upper right", labelcolor=MUTED,
          borderaxespad=.2)

# ---- (c) interaction model -------------------------------------------------
ax = axes[1, 0]
unity(ax)
for q, dd in enumerate(sorted(inter["D"].unique())):
    s = inter[np.isclose(inter["D"], dd)]
    ax.plot(s["pctl"], s["beta_1"], color=QC[q], linewidth=2,
            label=f"Q{q + 1}  {np.expm1(dd):.2f} h", zorder=3)
dress(ax, "Interaktionsmodell β₁(Zeit, log Verspätung)",
      "EIN Fit: te(X,D) + te(X,D)·Exog · an den Quartilsmedianen ausgewertet")
ax.set_xlabel("Perzentil des Matchup-Fensters")
ax.set_ylabel("β₁")
ax.legend(frameon=False, fontsize=8, loc="lower left", labelcolor=MUTED,
          title="Verspätung", title_fontsize=8, borderaxespad=.2)

# ---- (d) composition control ----------------------------------------------
ax = axes[1, 1]
unity(ax)
ax.plot(base["pctl"], base["beta_1"], color=GREY, linewidth=1.4,
        linestyle=(0, (5, 2)), label="Baseline (imputiert, alle Serien)")
for o, c, lab in ((full, CAT1, f"alle {len(ser):,d} Serien (echt)"),
                  (fobs, CAT2, "nur 24.568 vollständig beobachtete")):
    ax.fill_between(o["pctl"], o["beta_1"] - 1.96 * o["se"],
                    o["beta_1"] + 1.96 * o["se"], color=c, alpha=.16,
                    linewidth=0)
    ax.plot(o["pctl"], o["beta_1"], color=c, linewidth=2, label=lab, zorder=3)
dress(ax, "Kompositions-Kontrolle",
      "gleiche Spezifikation · andere Serienmenge (alle mit Verspätung 0)")
ax.set_xlabel("Perzentil des Matchup-Fensters")
ax.set_ylabel("β₁")
ax.legend(frameon=False, fontsize=8, loc="upper right", labelcolor=MUTED,
          borderaxespad=.2)
ax.text(.03, .05,
        f"Δ mittleres β₁   {fobs['beta_1'].mean() - full['beta_1'].mean():+.3f}",
        transform=ax.transAxes, ha="left", va="bottom", fontsize=8.5,
        color=INK, family="monospace")

fig.tight_layout(pad=1.8, h_pad=3.4, w_pad=3.0)
for ext in ("png", "pdf"):
    fig.savefig(f"{OUT}/entry_delay.{ext}", dpi=170, bbox_inches="tight")
print(f"-> {OUT}/entry_delay.png / .pdf")
