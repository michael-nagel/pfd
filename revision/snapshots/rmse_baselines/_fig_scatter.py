#!/usr/bin/env python3
"""Abbildung B: RMSE gegen Posting Time über die 24 Bookmaker (R2-M7/R3-2).

Der direkte Test der Referee-Hypothese „später postende Bookmaker sehen
besser aus". Beide Größen auf Serienebene, jeder Punkt mit dem
Bookmaker-Namen beschriftet.

Die Beschriftung setzt kein `adjustText` ein, sondern probiert je Punkt eine
feste Kandidatenliste von Versätzen durch und nimmt den ersten, der weder ein
schon gesetztes Label noch einen Punkt überdeckt. Das ist deterministisch —
dieselbe Abbildung kommt bei jedem Lauf identisch heraus — und spart eine
Abhängigkeit.

Diagnostisch; der Produktions-Plotcode bleibt unberührt. Der Frame stammt aus
`_rmse_baselines.py`.
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
from matplotlib.transforms import Bbox  # noqa: E402
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

g = d.groupby("Bookies")
bm = pd.DataFrame({
    "opn_hrs_med": g["OpnHrs"].median(),
    "rmse": g["e2"].mean() ** 0.5,
}).sort_index()

x = bm["opn_hrs_med"].to_numpy(float)
y = bm["rmse"].to_numpy(float)
r_p = stats.pearsonr(x, y)
r_s = stats.spearmanr(x, y)
print(f"Bookmaker {len(bm)}")
print(f"Pearson {r_p[0]:+.4f} (p {r_p[1]:.4f})   "
      f"Spearman {r_s[0]:+.4f} (p {r_s[1]:.4f})")

# ----------------------------------------------------- Stil der Pipeline
cfg = OmegaConf.load("src/pfd/conf/config.yaml")
pal = (json.load(open(f"accessories/{cfg.files.clr_plt}"))
       + json.load(open(f"accessories/{cfg.files.clr_plt_ext}")))
sns.set_theme(palette=pal, style="ticks")
pp = PlotParams(cfg=cfg)
pylab.rcParams.update(pp.set_rc_params(kind="fig_big", fig_size=(6.4, 4.4)))
TCK = pp.xtick_labelsize * 0.5

fig, ax = plt.subplots()
gx = np.linspace(x.min() - 1.5, x.max() + 1.5, 50)
ax.plot(gx, np.polyval(np.polyfit(x, y, 1), gx), color=pal[1], zorder=2)
ax.scatter(x, y, color=pal[0], edgecolor="white", linewidth=0.5, zorder=3)
ax.set(xlabel="Median hours before match start",
       ylabel="Root Mean Squared Error")
ax.margins(0.12)
note = ax.annotate(f"Pearson  {r_p[0]:+.3f}\nSpearman {r_s[0]:+.3f}",
                   xy=(0.97, 0.04), xycoords="axes fraction", ha="right",
                   va="bottom", fontsize=TCK, family="monospace")

# ------------------------------------------------ Beschriftung der Punkte
# Kandidatenversätze in Punkten, von nah nach fern; je Punkt wird der erste
# überschneidungsfreie genommen. Ab `LEAD` Punkten Abstand bekommt das Label
# eine Verbindungslinie, sonst wäre die Zuordnung nicht mehr eindeutig.
DIRS = [(1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1), (0, 1), (0, -1)]
SCALES = (4, 7, 11, 16, 22, 30)
LEAD = 9

fig.canvas.draw()
rend = fig.canvas.get_renderer()
# Punkte und die Korrelationsannotation sind belegt
taken = [Bbox.from_bounds(*ax.transData.transform((xi, yi)) - 3.5, 7, 7)
         for xi, yi in zip(x, y, strict=True)]
taken.append(note.get_window_extent(rend).expanded(1.1, 1.2))

# Gedrängte Punkte zuerst: sie haben die wenigsten freien Plätze, isolierte
# finden ohnehin einen.
pos = np.column_stack([ax.transData.transform(p) for p in zip(x, y,
                                                              strict=True)]).T
dist = np.hypot(pos[:, None, 0] - pos[None, :, 0],
                pos[:, None, 1] - pos[None, :, 1])
np.fill_diagonal(dist, np.inf)
order = np.argsort(dist.min(axis=1))

used = []
for i in order:
    name, xi, yi = bm.index[i], x[i], y[i]
    placed = None
    for s in SCALES:
        for dx, dy in DIRS:
            t = ax.annotate(
                name, xy=(xi, yi), xytext=(dx * s, dy * s),
                textcoords="offset points", fontsize=TCK, color="black",
                ha="left" if dx > 0 else "right" if dx < 0 else "center",
                va="bottom" if dy > 0 else "top" if dy < 0 else "center",
                arrowprops=(dict(arrowstyle="-", linewidth=0.6,
                                 color="#52514e", shrinkA=1, shrinkB=3)
                            if s >= LEAD else None))
            bb = t.get_window_extent(rend).expanded(1.06, 1.18)
            if (ax.bbox.contains(*bb.min) and ax.bbox.contains(*bb.max)
                    and not any(bb.overlaps(o) for o in taken)):
                placed = bb
                used.append(s)
                break
            t.remove()
        if placed is not None:
            break
    if placed is None:
        raise RuntimeError(f"kein kollisionsfreier Platz fuer {name}")
    taken.append(placed)

print("  Versatz je Label (Punkte): "
      + ", ".join(f"{s}: {used.count(s)}x" for s in SCALES if s in used)
      + f"   -> {sum(s >= LEAD for s in used)} Verbindungslinien")

fig.tight_layout(pad=0.6)
for ext in ("png", "pdf"):
    fig.savefig(f"{OUT}/rmse_vs_posting_scatter.{ext}", format=ext, dpi=600,
                bbox_inches="tight")
print(f"-> {OUT}/rmse_vs_posting_scatter.png / .pdf")
