#!/usr/bin/env python3
"""Abbildung zu Eq. 3, Zwei-Panel-Fassung (ersetzt fig:win_props_re).

Links  der belegte Zusammenhang: Bin-Punkte je Bookmaker plus EINE gepoolte
       Regressionsgerade mit 95-%-Band statt der bisherigen 24 Einzelgeraden.
Rechts die geprüfte Heterogenität: die 24 bookmakerspezifischen Steigungen
       als Caterpillar mit 95-%-Intervallen, dazu der gemeinsame Wald-Test.

Antwortet damit direkt auf R2-C6: die Einzelgeraden im bisherigen Bild legen
Heterogenität nahe, die einem formalen Test nicht standhält.

Diagnostisch; der Produktions-Plotcode (`winning_proportions.py`) bleibt
unberührt.
"""

import json
import sys
import tempfile

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pylab  # noqa: E402
from omegaconf import OmegaConf  # noqa: E402
from scipy import stats  # noqa: E402

sys.path.insert(0, "src")
from pfd.utils.plot_params import PlotParams  # noqa: E402

OUT = "revision/snapshots/eq3_contract_level"
BINS = "revision/snapshots/diagnostics/win_props_input.csv"
FRAME = f"{tempfile.gettempdir()}/pfd_eq3_frame.parquet"
COMPETS = ["Compet_Challenger_Men", "Compet_ITF_Men", "Compet_Misc",
           "Compet_WTA"]
BASE = ["OpnOdds", "DltOpnCls", "TsDur"] + COMPETS
GREY, INK, MUTED = "#8a8984", "#0b0b0b", "#52514e"

# ------------------------------------------ FE-Steigungen neu, mit SEs
d = pd.read_parquet(FRAME)
d = d[d["RtrnOpnCls"].abs() > 0].reset_index(drop=True)
bk = sorted(d["Bookies"].unique())
ref = bk[0]
for b in bk[1:]:
    d[f"B_{b}"] = (d["Bookies"] == b).astype(float)
    d[f"BxD_{b}"] = d[f"B_{b}"] * d["DltOpnCls"]
cols = BASE + [f"B_{b}" for b in bk[1:]] + [f"BxD_{b}" for b in bk[1:]]
X = np.column_stack([np.ones(len(d))] + [d[c].to_numpy(float) for c in cols])
nm = ["(Intercept)"] + cols
y = d["Match"].to_numpy(float)
XtXi = np.linalg.inv(X.T @ X)
b_hat = XtXi @ (X.T @ y)
u = y - X @ b_hat
N, K = X.shape
codes = pd.factorize(d["Matchup"], sort=False)[0]
G = codes.max() + 1
S = np.zeros((G, K))
np.add.at(S, codes, X * u[:, None])
V = (G / (G - 1)) * ((N - 1) / (N - K)) * (XtXi @ (S.T @ S) @ XtXi)

# Steigung je Bookmaker als Linearkombination eta_2 + Interaktion; die SE
# braucht die volle Kovarianz, nicht nur die des Interaktionskontrasts.
i2 = nm.index("DltOpnCls")
rows = []
for b in bk:
    c = np.zeros(K)
    c[i2] = 1.0
    if b != ref:
        c[nm.index(f"BxD_{b}")] = 1.0
    est = float(c @ b_hat)
    se = float(np.sqrt(c @ V @ c))
    ic = (np.nan if b == ref
          else float(np.sqrt(V[nm.index(f"BxD_{b}"), nm.index(f"BxD_{b}")])))
    rows.append({"bookie": b, "slope": est, "se_slope_cl": se,
                 "ci_lo": est - 1.96 * se, "ci_hi": est + 1.96 * se,
                 "se_interaktion_cl": ic,
                 "t_vs_ref": np.nan if b == ref
                 else (est - b_hat[i2]) / ic})
sl = pd.DataFrame(rows).sort_values("slope").reset_index(drop=True)
sl.to_csv(f"{OUT}/bookie_fe_slopes.csv", index=False)

idx = [nm.index(f"BxD_{b}") for b in bk[1:]]
bb = b_hat[idx]
W = float(bb @ np.linalg.solve(V[np.ix_(idx, idx)], bb))
q = len(idx)
p_w = 1 - stats.chi2.cdf(W, q)

# Die gepoolte Steigung ist NICHT b_hat[i2] -- das waere in der
# FE-Parametrisierung die Steigung der Referenzkategorie. Sie stammt aus dem
# Modell OHNE Bookmaker-Terme (S3).
Xp = np.column_stack([np.ones(len(d))] + [d[c].to_numpy(float)
                                          for c in BASE])
nmp = ["(Intercept)"] + BASE
XtXip = np.linalg.inv(Xp.T @ Xp)
bp = XtXip @ (Xp.T @ y)
up = y - Xp @ bp
Sp = np.zeros((G, Xp.shape[1]))
np.add.at(Sp, codes, Xp * up[:, None])
Vp = ((G / (G - 1)) * ((N - 1) / (N - Xp.shape[1]))
      * (XtXip @ (Sp.T @ Sp) @ XtXip))
jp = nmp.index("DltOpnCls")
pooled, se_pooled = float(bp[jp]), float(np.sqrt(Vp[jp, jp]))
print(f"gepoolte Steigung S3 (bedingt auf OpnOdds) {pooled:.4f} "
      f"(SE cluster {se_pooled:.4f})")
print(f"Referenzkategorie {ref}: {b_hat[i2]:.4f}  (NICHT die gepoolte)")
print(f"Wald über {q} Interaktionen: chi2({q}) = {W:.2f}   p = {p_w:.4f}")
print(f"Steigungen {sl['slope'].min():.4f} - {sl['slope'].max():.4f}")

# ------------------------------------------------- Bin-Daten (links)
bins = pd.read_csv(BINS)
bins = bins[bins["Bookies"] != "All"].copy()
xb = bins["AvgChange"].to_numpy(float)
yb = bins["Proportions"].to_numpy(float)
# nach Fallzahl gewichtet -- ungewichtet ueberbetont duenn besetzte Randbins
# (43 Matches gegen mehrere Tausend)
wb = bins["NumMatches"].to_numpy(float)
Xb = np.column_stack([np.ones(len(xb)), xb])
Wb = Xb * wb[:, None]
XtXib = np.linalg.inv(Xb.T @ Wb)
bb2 = XtXib @ (Wb.T @ yb)
ub = yb - Xb @ bb2
s2 = (wb * ub**2).sum() / (wb.sum() - 2)
Vb = s2 * XtXib
# Nur fuer die Akten, NICHT geplottet: seit der Umstellung auf die
# Kontraktebene (R2-C1) ist die Bin-Regression nicht mehr die Spezifikation.
# Zwei Steigungen in einer Abbildung waeren irrefuehrend -- links steht die
# Beschreibung, rechts die Inferenz.
print(f"Bin-Gerade (nach NumMatches gewichtet, nur zum Vergleich, nicht "
      f"geplottet): Intercept {bb2[0]:.4f}  Steigung {bb2[1]:.4f}  "
      f"(n = {len(xb)} Bin-Punkte)")

# --------------------------------------------------------------- Plot
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

pal = (json.load(open("accessories/stata_colors.json"))
       + json.load(open("accessories/stata_colors_ext.json")))
cmap = {b: pal[i % len(pal)] for i, b in enumerate(bk)}

fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.4),
                         gridspec_kw={"width_ratios": [1.25, 1]})


def dress(ax, title, sub):
    ax.set_title(title, fontsize=11, color=INK, loc="left", pad=16,
                 fontweight="medium")
    ax.text(0, 1.015, sub, transform=ax.transAxes, fontsize=8, color=MUTED,
            va="bottom", ha="left")
    ax.grid(True, color="#ecebe7", linewidth=.7)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# ---- links: Zusammenhang -------------------------------------------------
ax = axes[0]
ax.axhline(0.5, color=GREY, linewidth=.9, linestyle=(0, (4, 3)), zorder=1)
ax.axvline(0.0, color=GREY, linewidth=.9, linestyle=(0, (4, 3)), zorder=1)
for b in bk:
    s = bins[bins["Bookies"] == b]
    ax.scatter(s["AvgChange"], s["Proportions"], s=22, color=cmap[b],
               alpha=.75, linewidth=0, zorder=3)
dress(ax, "Gewinnrate und Preisänderung (deskriptiv)",
      f"{len(xb)} Bin-Punkte aus {len(bk)} Bookmakern · keine Schätzung — "
      "die Steigung wird auf Kontraktebene bestimmt, siehe rechts")
ax.set_xlabel("Average Price Change Magnitude")
ax.set_ylabel("Winning Rate")

# ---- rechts: Caterpillar -------------------------------------------------
ax = axes[1]
ypos = np.arange(len(sl))
ax.axvline(pooled, color=INK, linewidth=1.1, linestyle=(0, (4, 3)), zorder=2,
           label=f"gepoolt {pooled:.3f}")
for i, r in sl.iterrows():
    ax.plot([r["ci_lo"], r["ci_hi"]], [i, i], color=cmap[r["bookie"]],
            linewidth=1.6, alpha=.85, zorder=3, solid_capstyle="round")
    ax.scatter(r["slope"], i, s=26, color=cmap[r["bookie"]], zorder=4,
               edgecolor="white", linewidth=.7)
ax.set_yticks(ypos)
ax.set_yticklabels(sl["bookie"], fontsize=8)
ax.set_ylim(-0.8, len(sl) + 2.2)          # Kopfraum für die Wald-Annotation
dress(ax, "Bookmakerspezifische Steigungen",
      "Kontraktebene, bedingt auf OpnOdds · Fixed Effects · 95 % "
      "cluster-robust (Matchup)")
ax.set_xlabel("Steigung auf DltOpnCls")
ax.legend(frameon=False, fontsize=8.5, loc="lower right", labelcolor=MUTED,
          borderaxespad=.4)
ax.text(.03, .965,
        f"gemeinsamer Wald-Test\nchi2({q}) = {W:.2f}   p = {p_w:.3f}\n"
        f"keine Heterogenität nachweisbar",
        transform=ax.transAxes, ha="left", va="top", fontsize=8.2,
        color=INK, family="monospace", linespacing=1.55,
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#f4f3ef",
                  edgecolor="#dedcd6", linewidth=.8))

fig.tight_layout(pad=1.8, w_pad=2.6)
for ext in ("png", "pdf"):
    fig.savefig(f"{OUT}/eq3_two_panel.{ext}", dpi=170, bbox_inches="tight")
print(f"-> {OUT}/eq3_two_panel.png / .pdf")
