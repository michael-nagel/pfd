#!/usr/bin/env python3
"""Abbildung A: RMSE und Posting Time je Bookmaker (R2-M7, zugleich R3-2).

Gruppierte Balken je Bookmaker, alphabetisch wie die publizierte Figur 1,
aber auf SERIENEBENE (jede Match-Bookmaker-Kombination zaehlt einmal). Neben
der Prognosegenauigkeit steht der mediane Posting-Zeitpunkt auf einer zweiten
y-Achse rechts.

Die Grenze sqrt(E[p(1-p)]) wird bewusst NICHT eingezeichnet; sie steht als
Einordnung im Papertext zur Verfuegung (siehe README und `baselines.csv`).

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
from omegaconf import OmegaConf  # noqa: E402

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

g = d.groupby("Bookies")
bm = pd.DataFrame({
    "opn_hrs_med": g["OpnHrs"].median(),
    "rmse": g["e2"].mean() ** 0.5,
}).sort_index()                      # alphabetisch wie die publizierte Figur

print(f"Serien {len(d):,d}   Bookmaker {len(bm)}")
print(f"RMSE {bm['rmse'].min():.4f} - {bm['rmse'].max():.4f}")
print(f"Posting Time {bm['opn_hrs_med'].min():.2f} - "
      f"{bm['opn_hrs_med'].max():.2f} h")

# ----------------------------------------------------- Stil der Pipeline
cfg = OmegaConf.load("src/pfd/conf/config.yaml")
pal = (json.load(open(f"accessories/{cfg.files.clr_plt}"))
       + json.load(open(f"accessories/{cfg.files.clr_plt_ext}")))
sns.set_theme(palette=pal, style="ticks")
pp = PlotParams(cfg=cfg)
pylab.rcParams.update(pp.set_rc_params(kind="fig_big", fig_size=(6.4, 3.0)))
LBL = pp.axes_labelsize * 0.5
TCK = pp.xtick_labelsize * 0.5

x = np.arange(len(bm))
fig, ax = plt.subplots()
ax2 = ax.twinx()

b1 = ax.bar(x - 0.21, bm["rmse"], width=0.42, color=pal[0],
            label="RMSE (left axis)")
b2 = ax2.bar(x + 0.21, bm["opn_hrs_med"], width=0.42, color=pal[1],
             label="Median posting time (right axis)")

ax.set(ylabel="Root Mean Squared Error", ylim=[0.44, 0.47],
       xlim=[-0.8, len(bm) - 0.2])
ax.set_xticks(x, bm.index, rotation=90)
ax2.set_ylabel("Median hours before match start", fontsize=LBL)
ax2.set_ylim(bottom=0)
ax2.tick_params(labelsize=TCK)
# Boxrahmen wie in der publizierten Figur; twinx blendet Spines aus
for a in (ax, ax2):
    for s in a.spines.values():
        s.set_visible(True)

ax.legend(handles=[b1, b2], loc="lower center", bbox_to_anchor=(0.5, 1.0),
          ncol=2, frameon=False, fontsize=TCK, borderaxespad=0.2)

fig.tight_layout(pad=0.6)
for ext in ("png", "pdf"):
    fig.savefig(f"{OUT}/rmse_posting_bars.{ext}", format=ext, dpi=600,
                bbox_inches="tight")
print(f"-> {OUT}/rmse_posting_bars.png / .pdf")
