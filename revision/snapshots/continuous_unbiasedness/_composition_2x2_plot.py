#!/usr/bin/env python3
"""Abbildung zum 2x2 Imputation vs. Komposition (2 Panels)."""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

OUT = "revision/snapshots/continuous_unbiasedness"

# zwei Kategorien (Methode) x zwei Helligkeiten (Serienmenge)
BASE_ALL, BASE_FO = "#1c5cab", "#86b6ef"
CONT_ALL, CONT_FO = "#a8410f", "#f0956b"
GREY, INK, MUTED = "#8a8984", "#0b0b0b", "#52514e"

cur = pd.read_csv(f"{OUT}/beta1_2x2_composition_curves.csv")
tab = pd.read_csv(f"{OUT}/compare_2x2_composition.csv")
m = dict(zip("ABCD", tab["beta_1_mean_common"], strict=True))

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 9,
    "axes.edgecolor": "#c9c8c3", "axes.linewidth": .8,
    "axes.labelcolor": MUTED, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "figure.facecolor": "white", "axes.facecolor": "white",
})

fig, axes = plt.subplots(1, 2, figsize=(12.5, 5))


def dress(ax, title, sub):
    ax.set_title(title, fontsize=11, color=INK, loc="left", pad=15,
                 fontweight="medium")
    ax.text(0, 1.012, sub, transform=ax.transAxes, fontsize=8, color=MUTED,
            va="bottom", ha="left")
    ax.grid(True, color="#ecebe7", linewidth=.7)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# ---- (a) die vier Kurven ---------------------------------------------------
ax = axes[0]
spec = [("A", BASE_ALL, "-", "A  Baseline/imputiert, alle Serien"),
        ("B", BASE_FO, "-", "B  Baseline/imputiert, nur vollst. beob."),
        ("C", CONT_ALL, "--", "C  kontinuierlich/echt, alle Serien"),
        ("D", CONT_FO, "--", "D  kontinuierlich/echt, nur vollst. beob.")]
for k, c, ls, lab in spec:
    ax.plot(cur["pctl"], cur[k], color=c, linestyle=ls, linewidth=1.9,
            label=f"{lab}   (Mittel {m[k]:.3f})")
ax.axhline(1, color=GREY, linewidth=.9, linestyle=(0, (4, 3)), zorder=1)
ax.set_xlabel("Position im Matchup-Fenster (Perzentil)")
ax.set_ylabel(r"$\beta_1$")
ax.legend(frameon=False, fontsize=8, loc="upper right")
dress(ax, "Alle vier Zellen des 2×2",
      "gemeinsamer Träger: Perzentile 2, 4, …, 98")

# ---- (b) Zerlegung ---------------------------------------------------------
ax = axes[1]
ax.axis("off")
comp_base, comp_cont = m["A"] - m["B"], m["C"] - m["D"]
meth_all, meth_fo = m["A"] - m["C"], m["B"] - m["D"]
inter = comp_base - comp_cont

xs, ys = [0.30, 0.68], [0.68, 0.40]
for (k, x, y) in [("A", xs[0], ys[0]), ("B", xs[1], ys[0]),
                  ("C", xs[0], ys[1]), ("D", xs[1], ys[1])]:
    col = BASE_ALL if k in "AB" else CONT_ALL
    ax.text(x, y, f"{m[k]:.3f}", ha="center", va="center", fontsize=22,
            color=col, fontweight="medium")
    ax.text(x, y - 0.075, k, ha="center", va="center", fontsize=9, color=MUTED)

ax.text(xs[0], ys[0] + 0.20, "alle Serien", ha="center", fontsize=9.5,
        color=INK)
ax.text(xs[1], ys[0] + 0.20, "nur vollständig beobachtete", ha="center",
        fontsize=9.5, color=INK)
ax.text(0.02, ys[0], "Baseline\nimputiert", ha="left", va="center",
        fontsize=9.5, color=BASE_ALL)
ax.text(0.02, ys[1], "kontinuierlich\necht", ha="left", va="center",
        fontsize=9.5, color=CONT_ALL)

# horizontale Pfeile = Komposition, vertikale = Methode/Imputation
for y, val in [(ys[0], comp_base), (ys[1], comp_cont)]:
    ax.annotate("", xy=(xs[1] - 0.09, y), xytext=(xs[0] + 0.09, y),
                arrowprops=dict(arrowstyle="->", color=GREY, lw=1.1))
    ax.text((xs[0] + xs[1]) / 2, y + 0.035, f"{val:+.3f}", ha="center",
            fontsize=9, color=MUTED)
for x, val in [(xs[0], meth_all), (xs[1], meth_fo)]:
    ax.annotate("", xy=(x, ys[1] + 0.10), xytext=(x, ys[0] - 0.10),
                arrowprops=dict(arrowstyle="->", color=GREY, lw=1.1))
    ax.text(x + 0.055, (ys[0] + ys[1]) / 2, f"{val:+.3f}", ha="left",
            fontsize=9, color=MUTED)

ax.text(0.02, 0.17,
        f"Komposition echt (C−D)            {comp_cont:+.3f}\n"
        f"Komposition imputiert (A−B)       {comp_base:+.3f}"
        f"   ({comp_base / comp_cont * 100:.0f} % davon erhalten)\n"
        f"Methode ohne Imputation (B−D)     {meth_fo:+.3f}"
        f"   ({meth_fo / meth_all * 100:.0f} % der Lücke)\n"
        f"Interaktion = Imputation          {inter:+.3f}"
        f"   ({inter / meth_all * 100:.0f} % der Lücke)",
        fontsize=8.5, color=MUTED, family="monospace", va="top")
dress(ax, "Zerlegung des Niveauversatzes",
      "waagerecht = Komposition, senkrecht = Methode/Imputation")

fig.tight_layout(pad=1.6)
for ext in ("png", "pdf"):
    fig.savefig(f"{OUT}/composition_2x2.{ext}", dpi=200,
                bbox_inches="tight", facecolor="white")
print(f"geschrieben: {OUT}/composition_2x2.{{png,pdf}}")
