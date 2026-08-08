#!/usr/bin/env python3
"""Entwurf für die neue Figur 1 (R2-M7, zugleich R3-2).

Links  der RMSE je Bookmaker, aber eingeordnet: jeder Punkt ist mit der
       bookmakerspezifischen Grenze sqrt(E[p(1-p)]) verbunden -- dem RMSE,
       den ein perfekt kalibrierter Prognostiker bei GENAU DIESER
       Preisverteilung erreichen würde. Die Farbe kodiert den medianen
       Posting-Zeitpunkt.
Rechts der direkte Test der Referee-Hypothese: RMSE gegen Posting-Zeitpunkt,
       einmal auf Serienebene (jedes Spiel zählt einmal) und einmal in der
       publizierten panelgewichteten Fassung. Die beiden Geraden zeigen, dass
       die Gewichtung über das Vorzeichen entscheidet.

Bewusste Abweichung vom publizierten Bild: Punkte statt Balken. Die
Unterschiede zwischen den Bookmakern liegen in der zweiten Nachkommastelle,
ein Balkendiagramm bräuchte dafür eine abgeschnittene Achse.

Diagnostisch; der Produktions-Plotcode (`bookmaker_accuracy.py`) bleibt
unberührt.
"""

import json
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pylab  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, Normalize  # noqa: E402
from omegaconf import OmegaConf  # noqa: E402
from scipy import stats  # noqa: E402

sys.path.insert(0, "src")
from pfd.utils.plot_params import PlotParams  # noqa: E402

OUT = "revision/snapshots/rmse_baselines"
FRAME = ("/mnt/c/Users/micha/AppData/Local/Temp/claude/"
         "C--Users-micha-OneDrive-Michi-pfd/"
         "faf3f6fb-65b6-4ea7-a5e5-08b35a6557d8/scratchpad/"
         "pfd_rmse_frame.parquet")
GREY, INK, MUTED = "#8a8984", "#0b0b0b", "#52514e"

pal = json.load(open("accessories/stata_colors.json"))
# Sequentielle Rampe aus der Projektpalette: hell = spaet, dunkel = frueh
CMAP = LinearSegmentedColormap.from_list(
    "pfd_time", [pal[14], pal[9], pal[0]])
ACC = pal[1]

d = pd.read_parquet(FRAME)
d["e2"] = (d["Match"] - d["OpnOdds"]) ** 2
d["p1mp"] = d["OpnOdds"] * (1 - d["OpnOdds"])

g = d.groupby("Bookies")
bm = pd.DataFrame({
    "n_series": g.size(),
    "opn_hrs_med": g["OpnHrs"].median(),
    "rmse_series": g["e2"].mean() ** 0.5,
    "limit": g["p1mp"].mean() ** 0.5,
})
w = d.groupby("Bookies").apply(
    lambda s: np.sqrt(np.average(s["e2"], weights=s["NObs"])),
    include_groups=False)
bm["rmse_panel"] = w
# absteigend: der beste Bookmaker steht oben, weil barh/scatter von unten
# nach oben zeichnen
bm = bm.sort_values("rmse_series", ascending=False)

r_s = stats.pearsonr(bm["opn_hrs_med"], bm["rmse_series"])
rho_s = stats.spearmanr(bm["opn_hrs_med"], bm["rmse_series"])
r_p = stats.pearsonr(bm["opn_hrs_med"], bm["rmse_panel"])
print(f"Serienebene   Pearson {r_s[0]:+.3f} (p {r_s[1]:.3f})   "
      f"Spearman {rho_s[0]:+.3f} (p {rho_s[1]:.3f})")
print(f"panelgewichtet Pearson {r_p[0]:+.3f} (p {r_p[1]:.3f})")

# gepoolte Bezugspunkte fuer die Annotation
y = d["Match"].to_numpy(float)
p = d["OpnOdds"].to_numpy(float)
brier = float(np.mean((p - y) ** 2))
limit = float(np.mean(p * (1 - p)))
print(f"gepoolt: RMSE {np.sqrt(brier):.4f}   Grenze {np.sqrt(limit):.4f}   "
      f"BSS {1 - brier / 0.25:.4f}")

# ------------------------------------------------------------------ Plot
cfg = OmegaConf.create({"plotting": {
    "base_size": 16, "leg_mkr_size": 1, "line_width": 1, "mkr_size": 8,
    "ax_line_width": 0.8, "xtick_maj_width": 0.8, "ytick_maj_width": 0.8,
    "xtick_maj_size": 3.5, "ytick_maj_size": 3.5,
    "font_family": "sans-serif"}})
pp = PlotParams(cfg=cfg)
pylab.rcParams.update(pp.set_rc_params(kind="fig_big", fig_size=(13.5, 6.4)))
plt.rcParams.update({"font.size": 9, "axes.labelsize": 10,
                     "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
                     "axes.titlesize": 11, "figure.facecolor": "white",
                     "axes.facecolor": "white", "axes.edgecolor": "#c9c8c3",
                     "text.color": INK, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED})

fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.4),
                         gridspec_kw={"width_ratios": [1.15, 1]})
norm = Normalize(bm["opn_hrs_med"].min(), bm["opn_hrs_med"].max())


def dress(ax, title, sub):
    ax.set_title(title, fontsize=11, color=INK, loc="left", pad=16,
                 fontweight="medium")
    ax.text(0, 1.015, sub, transform=ax.transAxes, fontsize=8, color=MUTED,
            va="bottom", ha="left")
    ax.grid(True, color="#ecebe7", linewidth=.7)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# ---- links: RMSE je Bookmaker, eingeordnet -------------------------------
ax = axes[0]
ypos = np.arange(len(bm))
for i, (_, r) in enumerate(bm.iterrows()):
    ax.plot([r["rmse_series"], r["limit"]], [i, i], color="#d5d3cd",
            linewidth=1.4, zorder=2, solid_capstyle="round")
ax.scatter(bm["limit"], ypos, marker="|", s=110, color=MUTED, zorder=4,
           linewidth=1.2, label=r"Grenze $\sqrt{E[p(1-p)]}$ je Bookmaker")
ax.scatter(bm["rmse_series"], ypos, s=58, zorder=5, edgecolor="white",
           linewidth=.7, color=[CMAP(norm(v)) for v in bm["opn_hrs_med"]],
           label="beobachteter RMSE (Opening)")
ax.set_yticks(ypos)
ax.set_yticklabels(bm.index, fontsize=8)
ax.set_ylim(-0.9, len(bm) + 4.6)
ax.set_xlim(0.4435, 0.4705)
ax.set_xlabel("Root Mean Squared Error (Opening)")
dress(ax, "Genauigkeit der Eröffnungspreise, eingeordnet",
      "Serienebene, jedes Spiel zählt einmal · Farbe = medianer "
      "Posting-Zeitpunkt")
ax.legend(frameon=False, fontsize=8.2, loc="lower left", labelcolor=MUTED,
          borderaxespad=.5, handletextpad=.3, scatterpoints=1)
lab = lambda t, v: f"{t:<24s}{v}"  # noqa: E731
ax.text(.985, .985,
        "\n".join([lab("uninformiert (p = 0,5)", "RMSE  0,500"),
                   lab("gepoolt beobachtet",
                       f"RMSE  {np.sqrt(brier):.3f}".replace(".", ",")),
                   lab("Grenze E[p(1-p)]",
                       f"RMSE  {np.sqrt(limit):.3f}".replace(".", ",")),
                   lab("Brier Skill Score",
                       f"{f'{1 - brier / 0.25:.3f}'.replace('.', ','):>11s}")]),
        transform=ax.transAxes, ha="right", va="top", fontsize=8.2,
        color=INK, family="monospace", linespacing=1.55,
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#f4f3ef",
                  edgecolor="#dedcd6", linewidth=.8))

sm = plt.cm.ScalarMappable(cmap=CMAP, norm=norm)
cb = fig.colorbar(sm, ax=ax, pad=.02, fraction=.035, aspect=32)
cb.set_label("Stunden vor Anpfiff (Median)", fontsize=8.2, color=MUTED)
cb.ax.tick_params(labelsize=7.5, color=MUTED, labelcolor=MUTED)
cb.outline.set_visible(False)

# ---- rechts: der direkte Test --------------------------------------------
ax = axes[1]
x = bm["opn_hrs_med"].to_numpy(float)
gx = np.linspace(x.min() - .8, x.max() + .8, 50)

# derselbe Bookmaker in beiden Fassungen, durch eine Linie verbunden
for _, r in bm.iterrows():
    ax.plot([r["opn_hrs_med"]] * 2, [r["rmse_series"], r["rmse_panel"]],
            color="#eae8e2", linewidth=.9, zorder=1)

bp = np.polyfit(x, bm["rmse_panel"], 1)
ax.scatter(x, bm["rmse_panel"], s=24, facecolor="white", edgecolor=GREY,
           linewidth=.9, zorder=3)
ax.plot(gx, np.polyval(bp, gx), color=GREY, linewidth=1.1,
        linestyle=(0, (4, 3)), zorder=2,
        label=f"panelgewichtet, wie publiziert   r = {r_p[0]:+.2f}")

bs = np.polyfit(x, bm["rmse_series"], 1)
ax.plot(gx, np.polyval(bs, gx), color=ACC, linewidth=1.6, zorder=4,
        label=f"Serienebene   r = {r_s[0]:+.2f}")
ax.scatter(x, bm["rmse_series"], s=52, zorder=5, edgecolor="white",
           linewidth=.7, color=[CMAP(norm(v)) for v in x])

for nm, dx, dy in (("Pinnacle", 6, -11), ("BetInAsia", -6, -12),
                   ("10Bet", 7, 2), ("Betfair", -9, -3),
                   ("Dafabet", 7, -2)):
    r = bm.loc[nm]
    ax.annotate(nm, (r["opn_hrs_med"], r["rmse_series"]),
                textcoords="offset points", xytext=(dx, dy), fontsize=7.6,
                color=MUTED, ha="right" if dx < 0 else "left")

ax.set_xlabel("Medianer Posting-Zeitpunkt (Stunden vor Anpfiff)")
ax.set_ylabel("Root Mean Squared Error (Opening)")
ax.set_ylim(0.4448, 0.4735)
dress(ax, "Postet früher wirklich schlechter?",
      "24 Bookmaker der Schätzstichprobe · die Referee-Hypothese sagt eine "
      "steigende Gerade")
ax.legend(frameon=False, fontsize=8.2, loc="lower right", labelcolor=MUTED,
          borderaxespad=.4)
ax.text(.03, .985,
        f"Serienebene    r   = {r_s[0]:+.2f}  (p {r_s[1]:.3f})\n"
        f"               rho = {rho_s[0]:+.2f}  (p {rho_s[1]:.3f})\n"
        f"Marge heraus   r   = +0,33  (p 0,128)\n"
        f"innerhalb desselben Matchups  p < 0,001",
        transform=ax.transAxes, ha="left", va="top", fontsize=8.2,
        color=INK, family="monospace", linespacing=1.55,
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#f4f3ef",
                  edgecolor="#dedcd6", linewidth=.8))

fig.tight_layout(pad=1.8, w_pad=2.4)
for ext in ("png", "pdf"):
    fig.savefig(f"{OUT}/rmse_posting_time.{ext}", dpi=170,
                bbox_inches="tight")
print(f"-> {OUT}/rmse_posting_time.png / .pdf")
