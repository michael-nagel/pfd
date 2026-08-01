#!/usr/bin/env python3
"""Figure zur Hauptspezifikation: beta_1 mit cluster-robustem Band.

Links die kontinuierliche Schätzung über Stunden vor Anpfiff (M_c, Punkt-
schätzer), Primärband cluster-robust (CR1, Cluster = Matchup), zum Kontrast
das modellbasierte Band dünn gestrichelt. Rechts die publizierte
Perzentil-Baseline auf IDENTISCHER y-Achse -- die x-Achsen sind verschieden
(Stunden vs. Fensterperzentil), die Niveaus damit direkt vergleichbar.
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

OUT = "revision/snapshots/continuous_unbiasedness/main_spec"
GREY, INK, MUTED = "#8a8984", "#0b0b0b", "#52514e"
CAT1, CAT2 = "#2a78d6", "#eb6834"

cr = pd.read_csv(f"{OUT}/cluster_robust_beta1.csv")
mk = pd.read_csv(f"{OUT}/cluster_robust_marks.csv")
cont = pd.read_csv("revision/snapshots/continuous_unbiasedness/"
                   "beta1_continuous_loghours.csv")
base = pd.read_csv("revision/snapshots/C_normalized/beta1_curve.csv")

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


def unity(ax):
    ax.axhline(1, color=GREY, linewidth=.9, linestyle=(0, (4, 3)), zorder=1)


# gemeinsame y-Achse über beide Panels; die Baseline startet bei 2,59 und
# würde die Skala sprengen -> auf den gemeinsamen Bereich begrenzt und im
# Panel vermerkt
lo = min(cr["ci_lo"].min(), cont["ci_lo"].min()) - .05
hi = max(cr["ci_up"].max(), cont["ci_up"].max()) + .05
YL = (lo, hi)

fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.0))

# ---- (a) Stunden vor Anpfiff ----------------------------------------------
ax = axes[0]
unity(ax)
ax.fill_between(cr["hours"], cr["ci_lo"], cr["ci_up"], color=CAT1, alpha=.18,
                linewidth=0, label="95 % cluster-robust (CR1, Matchup)")
ax.plot(cr["hours"], cr["beta_1"] - 1.96 * cr["se_lmer_model"], color=CAT1,
        linewidth=.9, linestyle=(0, (3, 2)), zorder=3,
        label="95 % modellbasiert (M_c)")
ax.plot(cr["hours"], cr["beta_1"] + 1.96 * cr["se_lmer_model"], color=CAT1,
        linewidth=.9, linestyle=(0, (3, 2)), zorder=3)
ax.plot(cr["hours"], cr["beta_1"], color=CAT1, linewidth=2.2, zorder=4,
        label="β₁ (M_c, k = 6)")
# bisheriger Check: k=20-Fassung, die Wellen sind ein Flexibilitätsartefakt
# (siehe ../README.md) -- dünn und blass, damit sie das Band nicht dominiert
ax.plot(cont["hours"], cont["beta_1"], color=CAT2, linewidth=1.0, alpha=.55,
        linestyle=(0, (5, 2)), zorder=2,
        label="bisheriger Check (ohne REs/Kovariaten)")
ax.scatter(mk["hours"], mk["beta_1"], s=18, color=CAT1, zorder=5,
           edgecolor="white", linewidth=.8)
ax.set_xscale("log")
ax.set_xlim(62, .06)                                   # Anpfiff rechts
ax.set_xticks([48, 24, 12, 6, 3, 1, .25, .1])
ax.set_xticklabels(["48", "24", "12", "6", "3", "1", "0,25", "0,1"])
ax.set_ylim(*YL)
dress(ax, "β₁ über Stunden vor Anpfiff",
      "M_c (Bookmaker-RE, ohne Match-Intercept) · Band cluster-robust auf "
      "Matchup-Ebene")
ax.set_xlabel("Stunden vor Anpfiff (log, Anpfiff rechts)")
ax.set_ylabel("β₁")
ax.legend(frameon=False, fontsize=8, loc="lower left", labelcolor=MUTED,
          borderaxespad=.2, bbox_to_anchor=(0, -.02))
ax.text(.97, .95,
        f"SE-Faktor Cluster/Modell   {cr['inflation_vs_lmer'].median():>5.2f}\n"
        f"SE-Faktor Cluster/iid      "
        f"{(cr['se_cluster'] / cr['se_ols']).median():>5.2f}\n"
        f"β₁ beob.gewichtet          {0.9892:>5.3f}",
        transform=ax.transAxes, ha="right", va="top", fontsize=7.6,
        color=MUTED, family="monospace", linespacing=1.5)

# ---- (b) Perzentil-Baseline ------------------------------------------------
ax = axes[1]
unity(ax)
ax.fill_between(base["pctl"], base["beta_1"] - 1.96 * base["std_beta_1"],
                base["beta_1"] + 1.96 * base["std_beta_1"], color=GREY,
                alpha=.16, linewidth=0)
ax.plot(base["pctl"], base["beta_1"], color=GREY, linewidth=2,
        label="Baseline (Perzentilachse, imputiert)", zorder=3)
off = base[base["beta_1"] > YL[1]]
ax.set_xlim(0, 100)
ax.set_ylim(*YL)
dress(ax, "Publizierte Baseline zum Vergleich",
      "Perzentil des Matchup-Fensters · identische y-Achse")
ax.set_xlabel("Perzentil des Matchup-Fensters")
ax.set_ylabel("β₁")
ax.legend(frameon=False, fontsize=8, loc="upper right", labelcolor=MUTED,
          borderaxespad=.2)
if len(off):
    ax.text(.03, .95,
            f"{len(off)} Stützstellen oberhalb der Achse\n"
            f"(max β₁ = {base['beta_1'].max():.2f} bei Perzentil "
            f"{int(base.loc[base['beta_1'].idxmax(), 'pctl'])})",
            transform=ax.transAxes, ha="left", va="top", fontsize=7.6,
            color=MUTED, family="monospace", linespacing=1.5)

fig.tight_layout(pad=1.8, w_pad=3.0)
for ext in ("png", "pdf"):
    fig.savefig(f"{OUT}/main_spec.{ext}", dpi=170, bbox_inches="tight")
print(f"-> {OUT}/main_spec.png / .pdf   y-Achse {YL[0]:.2f} .. {YL[1]:.2f}")
print(f"   Baseline-Stützstellen ausserhalb: {len(off)} von {len(base)}")
