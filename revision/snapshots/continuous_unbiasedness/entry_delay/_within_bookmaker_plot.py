#!/usr/bin/env python3
"""Abbildung zum Within-Bookmaker-Test (Komposition, GAM-Stufen, Splits)."""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

OUT = "revision/snapshots/continuous_unbiasedness/entry_delay"

QC = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]     # Q1..Q4, hell -> dunkel
RAMP = ["#c7dcf7", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]  # q10..q90
EARLY, LATE = "#2a78d6", "#eb6834"
GREY, INK, MUTED = "#8a8984", "#0b0b0b", "#52514e"

ct = pd.read_csv(f"{OUT}/bookie_delay_crosstab.csv", index_col=0)
mods = pd.read_csv(f"{OUT}/beta1_within_bookmaker_models.csv")
cur = pd.read_csv(f"{OUT}/beta1_within_bookmaker_curves.csv")
spl = pd.read_csv(f"{OUT}/beta1_within_bookmaker_split.csv")

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 9,
    "axes.edgecolor": "#c9c8c3", "axes.linewidth": .8,
    "axes.labelcolor": MUTED, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "figure.facecolor": "white", "axes.facecolor": "white",
})

fig = plt.figure(figsize=(15, 9.5))
gs = fig.add_gridspec(2, 15, height_ratios=[1.15, 1], hspace=.42, wspace=1.9)


def dress(ax, title, sub):
    ax.set_title(title, fontsize=10.5, color=INK, loc="left", pad=14,
                 fontweight="medium")
    ax.text(0, 1.014, sub, transform=ax.transAxes, fontsize=7.8, color=MUTED,
            va="bottom", ha="left")
    ax.grid(True, color="#ecebe7", linewidth=.7)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def unity(ax):
    ax.axhline(1, color=GREY, linewidth=.9, linestyle=(0, (4, 3)), zorder=1)


# ---- (a) Bookmaker x Quartil, gestapelt ------------------------------------
ax = fig.add_subplot(gs[0, 0:5])
o = ct.sort_values("Median_h")
y = np.arange(len(o))
left = np.zeros(len(o))
for i, q in enumerate(["Q1", "Q2", "Q3", "Q4"]):
    ax.barh(y, o[q], left=left, color=QC[i], height=.78,
            label=f"{q}", edgecolor="white", linewidth=.5)
    left += o[q].to_numpy()
ax.axvline(0.25, color="white", linewidth=.8, zorder=3)
ax.axvline(0.50, color="white", linewidth=.8, zorder=3)
ax.axvline(0.75, color="white", linewidth=.8, zorder=3)
ax.set_yticks(y)
ax.set_yticklabels([f"{b}  ({m:.2f} h)" for b, m in
                    zip(o.index, o["Median_h"], strict=True)], fontsize=7.2)
ax.set_xlim(0, 1)
ax.set_xlabel("Anteil der Serien je Verspätungsquartil")
ax.legend(frameon=False, fontsize=7.5, ncol=4, loc="lower center",
          bbox_to_anchor=(.5, -.22))
ax.grid(False)
dress(ax, "Bookmaker × Verspätungsquartil",
      "sortiert nach eigener Median-Verspätung; weiße Linien = 25/50/75 %")
ax.set_title("Bookmaker × Verspätungsquartil", fontsize=10.5, color=INK,
             loc="left", pad=14, fontweight="medium")

# ---- (b)/(c) GAM-Stufen ----------------------------------------------------
names = list(mods["model"].unique())
for j, name in enumerate(names[:2]):
    ax = fig.add_subplot(gs[0, 5 + j * 5:10 + j * 5])
    m = mods[mods["model"] == name]
    lv = sorted(m["level"].unique())
    for i, v in enumerate(lv):
        s = m[m["level"] == v].sort_values("pctl")
        lab = (f"{np.expm1(v):.2f} h" if "raw LD" in name
               else f"{v:+.2f} log")
        ax.plot(s["pctl"], s["beta_1"], color=RAMP[i], linewidth=1.8,
                label=f"q{[10, 25, 50, 75, 90][i]}  {lab}")
    unity(ax)
    ax.set_xlabel("Position im Matchup-Fenster (Perzentil)")
    ax.set_ylabel(r"$\beta_1$")
    ax.set_ylim(0.35, 1.75)
    ax.legend(frameon=False, fontsize=7.3, title="Verspätung",
              title_fontsize=7.3, loc="lower left")
    sub = ("gepoolt: Verspätung roh, kein Bookmaker-Effekt"
           if "gepoolt" in name else
           "Bookmaker-FE + Exog:B, Verspätung within zentriert")
    dress(ax, name.split(" (")[0], sub)

# ---- (d) je Bookmaker: früh vs. spät --------------------------------------
top = spl.nlargest(5, "sd_logDelay")
for j, (_, r) in enumerate(top.iterrows()):
    ax = fig.add_subplot(gs[1, j * 3:(j + 1) * 3])
    lo, hi = np.inf, -np.inf
    for half, col in (("early", EARLY), ("late", LATE)):
        sel = (cur["B"] == r["B"]) & (cur["half"] == half)
        s = cur[sel].sort_values("pctl")
        ax.plot(s["pctl"], s["beta_1"], color=col, linewidth=1.8,
                label="früh" if half == "early" else "spät")
        ax.fill_between(s["pctl"], s["beta_1"] - 1.96 * s["se"],
                        s["beta_1"] + 1.96 * s["se"], color=col, alpha=.13,
                        linewidth=0)
        lo, hi = min(lo, s["beta_1"].min()), max(hi, s["beta_1"].max())
    unity(ax)
    # auf die Kurven skalieren; die KI-Bänder dürfen anschneiden
    pad = max(.12, (hi - lo) * .12)
    ax.set_ylim(min(lo - pad, .9), max(hi + pad, 1.1))
    ax.set_xlabel("Perzentil")
    if j == 0:
        ax.set_ylabel(r"$\beta_1$")
        ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    dress(ax, r["B"], f"Median {r['median_delay_h']:.2f} h   "
                      f"Δ Mittel {r['d_mean']:+.3f}")

fig.suptitle("Within-Bookmaker-Test des Verspätungseffekts", x=.007, y=.995,
             ha="left", fontsize=12.5, color=INK, fontweight="medium")
for ext in ("png", "pdf"):
    fig.savefig(f"{OUT}/within_bookmaker.{ext}", dpi=200, bbox_inches="tight",
                facecolor="white")
print(f"geschrieben: {OUT}/within_bookmaker.{{png,pdf}}")
