#!/usr/bin/env python3
"""Neufassung von Figure 1 im Paper-Stil (R2-M7, zugleich R3-2).

Links  RMSE je Bookmaker wie in der publizierten Abbildung -- Balken,
       alphabetisch, gleiche Achsenbeschriftung -- aber auf SERIENEBENE und
       mit dem medianen Posting-Zeitpunkt als Farbe. Die punktierte Linie ist
       die Grenze sqrt(E[p(1-p)]), also der RMSE, den ein perfekt
       kalibrierter Prognostiker bei dieser Preisverteilung erreichen wuerde.
Rechts derselbe RMSE gegen den medianen Posting-Zeitpunkt ueber die 24
       Bookmaker -- der direkte Test der Referee-Hypothese.

Serienebene heisst: jede Match-Bookmaker-Kombination zaehlt einmal. Die
publizierte Fassung rechnet auf dem Panel (`bookmaker_accuracy.py:62`), womit
jede Serie mit ihrer Zahl an Preisupdates gewichtet eingeht; diese Gewichtung
ist mit dem Posting-Zeitpunkt korreliert (-0,73) und kippt das Vorzeichen des
Zusammenhangs. Begruendung im README.

Diagnostisch; der Produktions-Plotcode bleibt unberuehrt. Der Frame stammt
aus `_rmse_baselines.py`.
"""

import json
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pylab  # noqa: E402
import seaborn as sns  # noqa: E402
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

# ------------------------------------------------------------ Kennzahlen
d = pd.read_parquet(FRAME)
d["e2"] = (d["Match"] - d["OpnOdds"]) ** 2
d["p1mp"] = d["OpnOdds"] * (1 - d["OpnOdds"])

g = d.groupby("Bookies")
bm = pd.DataFrame({
    "n_series": g.size(),
    "opn_hrs_med": g["OpnHrs"].median(),
    "rmse": g["e2"].mean() ** 0.5,
}).sort_index()                      # alphabetisch wie die publizierte Figur

limit = float(np.sqrt(d["p1mp"].mean()))
r_p = stats.pearsonr(bm["opn_hrs_med"], bm["rmse"])
r_s = stats.spearmanr(bm["opn_hrs_med"], bm["rmse"])
print(f"Serien {len(d):,d}   Bookmaker {len(bm)}")
print(f"RMSE Serienebene: {bm['rmse'].min():.4f} - {bm['rmse'].max():.4f}")
print(f"Posting-Zeitpunkt: {bm['opn_hrs_med'].min():.2f} - "
      f"{bm['opn_hrs_med'].max():.2f} h vor Anpfiff")
print(f"Grenze sqrt(E[p(1-p)]) auf dieser Stichprobe: {limit:.4f}")
print(f"Pearson {r_p[0]:+.4f} (p {r_p[1]:.4f})   "
      f"Spearman {r_s[0]:+.4f} (p {r_s[1]:.4f})")

# ----------------------------------------------------- Stil der Pipeline
cfg = OmegaConf.load("src/pfd/conf/config.yaml")
pal = (json.load(open(f"accessories/{cfg.files.clr_plt}"))
       + json.load(open(f"accessories/{cfg.files.clr_plt_ext}")))
sns.set_theme(palette=pal, style="ticks")
pp = PlotParams(cfg=cfg)
pylab.rcParams.update(pp.set_rc_params(kind="fig_big", fig_size=(6.4, 3.4)))
LBL = pp.axes_labelsize * 0.5
TCK = pp.xtick_labelsize * 0.5
YLIM = [0.44, 0.47]

# Sequentielle Rampe aus der Projektpalette: hell = spaet, dunkel = frueh
cmap = LinearSegmentedColormap.from_list("pfd_time", [pal[14], pal[9], pal[0]])
norm = Normalize(bm["opn_hrs_med"].min(), bm["opn_hrs_med"].max())
clr = [cmap(norm(v)) for v in bm["opn_hrs_med"]]

fig, ax = plt.subplots(ncols=2, gridspec_kw={"width_ratios": [1.9, 1]})

# ------------------------------------------------- links: RMSE je Bookmaker
x = np.arange(len(bm))
ax[0].bar(x, bm["rmse"], color=clr, width=0.8)
ax[0].axhline(limit, linestyle="dotted", color="black", zorder=3)
ax[0].annotate(r"$\sqrt{E[p(1-p)]}$", xy=(-0.4, limit), xytext=(0, 2),
               textcoords="offset points", ha="left", va="bottom",
               fontsize=TCK)
ax[0].set(ylabel="Root Mean Squared Error", ylim=YLIM,
          xlim=[-0.8, len(bm) - 0.2])
ax[0].set_xticks(x, bm.index, rotation=90)

sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
cb = fig.colorbar(sm, ax=ax[0], orientation="horizontal", location="top",
                  fraction=0.05, pad=0.03)
cb.set_label("Median hours before match start", fontsize=LBL)
cb.ax.tick_params(labelsize=TCK)

# ------------------------------------------- rechts: RMSE gegen Posting Time
xs = bm["opn_hrs_med"].to_numpy(float)
gx = np.linspace(xs.min() - 1, xs.max() + 1, 50)
ax[1].plot(gx, np.polyval(np.polyfit(xs, bm["rmse"], 1), gx), color=pal[1],
           zorder=2)
ax[1].scatter(xs, bm["rmse"], color=clr, edgecolor="white", linewidth=0.4,
              zorder=3)
# gleiche y-Skala wie links, damit beide Panels dieselbe Groesse zeigen
ax[1].set(xlabel="Median hours before match start",
          ylabel="Root Mean Squared Error", ylim=YLIM)
ax[1].annotate(f"Pearson  {r_p[0]:+.3f}\nSpearman {r_s[0]:+.3f}",
               xy=(0.04, 0.96), xycoords="axes fraction", ha="left",
               va="top", fontsize=TCK, family="monospace")

fig.tight_layout(pad=0.6, w_pad=1.6)
for ext in ("png", "pdf"):
    fig.savefig(f"{OUT}/fig_rmse_posting.{ext}", format=ext, dpi=600,
                bbox_inches="tight")
print(f"-> {OUT}/fig_rmse_posting.png / .pdf")
