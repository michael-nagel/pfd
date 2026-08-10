#!/usr/bin/env python3
"""Finale Inferenz auf der ns(df=4)-Basis mit vollem Bootstrap (B = 100).

Beantwortet vier Fragen:

  1) Verhaeltnis Bootstrap/Sandwich ueber das Gitter, besonders am rechten
     (anpfiffnahen) Rand.
  2) Wieviele Gitterpunkte schliessen die 1 aus -- mit beiden Baendern,
     punktweise und simultan.
  3) Datendichte am rechten Rand: wieviele Beobachtungen und Serien liegen
     in dem Bereich, in dem die Aussage kippt.
  4) Symmetrischer Trim: das Berichtsfenster ist links bei 48 h gekappt
     (sparsamste 3 %). Was passiert, wenn rechts spiegelbildlich getrimmt
     wird?

Der kritische sup-t-Wert wird aus der jeweiligen Kovarianz gezogen -- fuer
das Bootstrap-Band also aus der Bootstrap-Kovarianz, nicht aus der des
Sandwich.

Rein diagnostisch.
"""

import numpy as np
import pandas as pd

OUT = "revision/snapshots/continuous_unbiasedness/main_spec"
FRAME = "data/interim/pfd_mainspec_frame2.parquet"
MARKS = [24.0, 12.0, 6.0, 3.0, 1.0, 0.25]
HMAX = 48.0
ALPHA = 0.05
NSIM = 200_000

pd.set_option("display.width", 240)
rng = np.random.default_rng(20260810)

ns = pd.read_csv(f"{OUT}/ns4_beta1.csv")
boot = np.vstack([np.load(f"{OUT}/ns4_bootstrap_beta1_part{p}.npy")
                  for p in (0, 1)])
B = len(boot)
hours = ns["hours"].to_numpy()
b1 = ns["beta_1"].to_numpy()
se_sw = ns["se_cluster"].to_numpy()
se_bt = boot.std(axis=0, ddof=1)
print(f"B = {B} Replikate, {boot.shape[1]} Gitterpunkte")


def sup_crit(cov, se, mask):
    """Simultaner kritischer Wert aus N(0, cov), auf dem Fenster `mask`."""
    c = cov[np.ix_(mask, mask)]
    w, v = np.linalg.eigh(c)
    keep = w > w.max() * 1e-10
    root = v[:, keep] * np.sqrt(w[keep])
    draws = rng.standard_normal((NSIM, root.shape[1])) @ root.T
    return float(np.percentile(np.abs(draws / se[mask]).max(axis=1),
                               100 * (1 - ALPHA))), int(keep.sum())


def counts(se, crit, mask):
    """Gitterpunkte, an denen ein Band die 1 ausschliesst (pw und simultan)."""
    pw = ((b1 - 1.959964 * se > 1) | (b1 + 1.959964 * se < 1)) & mask
    si = ((b1 - crit * se > 1) | (b1 + crit * se < 1)) & mask
    return int(pw.sum()), int(si.sum()), si


# ------------------------------------------------- 1) Verhaeltnis der SEs
print("\n" + "=" * 78)
print("1) SE-VERHAELTNIS BOOTSTRAP / SANDWICH")
print("=" * 78)
m48 = hours <= HMAX
ratio = se_bt / se_sw
r = ratio[m48]
print(f"Fenster <= {HMAX:.0f} h:  Median {np.median(r):.3f}   "
      f"Mittel {r.mean():.3f}   Spanne {r.min():.3f}-{r.max():.3f}")
for lab, sel in (("> 12 h", hours > 12),
                 ("1-12 h", (hours <= 12) & (hours > 1)),
                 ("0,4-1 h", (hours <= 1) & (hours > 0.4)),
                 ("<= 0,4 h", hours <= 0.4)):
    q = ratio[sel & m48]
    print(f"  {lab:<9s} n = {len(q):>2d}   Median {np.median(q):.3f}   "
          f"Spanne {q.min():.3f}-{q.max():.3f}")

mk = pd.DataFrame({"hours": hours, "beta_1": b1, "se_sandwich": se_sw,
                   "se_boot": se_bt, "ratio": ratio})
print("\n" + mk.iloc[[int(np.abs(hours - h).argmin()) for h in MARKS]]
      .to_string(index=False, float_format=lambda v: f"{v:8.4f}"))
mk.to_csv(f"{OUT}/ns4_final_se.csv", index=False)

# ------------------------------------------- 2) Wieviele schliessen 1 aus
print("\n" + "=" * 78)
print("2) GITTERPUNKTE, DIE DIE 1 AUSSCHLIESSEN")
print("=" * 78)
cov_bt = np.cov(boot, rowvar=False)
crit_bt, rank_bt = sup_crit(cov_bt, se_bt, m48)
print(f"Bootstrap-Kovarianz: Rang {rank_bt}, sup-t = {crit_bt:.3f}")
CRIT_SW = 2.666                        # aus `_ns_main.py`, Sandwich-Kovarianz
print(f"Sandwich (aus _ns_main.py): sup-t = {CRIT_SW:.3f}")

rows = []
for lab, se, crit in (("Sandwich", se_sw, CRIT_SW),
                      ("Bootstrap", se_bt, crit_bt)):
    pw, si, si_mask = counts(se, crit, m48)
    rows.append({"Band": lab, "punktweise": pw, "simultan": si,
                 "von": int(m48.sum())})
    if si:
        print(f"  {lab}: simultan ausgeschlossen zwischen "
              f"{hours[si_mask].min():.3f} und {hours[si_mask].max():.3f} h")
t = pd.DataFrame(rows)
print("\n" + t.to_string(index=False))
t.to_csv(f"{OUT}/ns4_final_counts.csv", index=False)

# --------------------------------------------------- 3) Datendichte rechts
print("\n" + "=" * 78)
print("3) DATENDICHTE AM RECHTEN RAND")
print("=" * 78)
df = pd.read_parquet(FRAME)
h = df["HoursToKick"].to_numpy()
n_tot, s_tot = len(df), df["GroupId"].nunique()
print(f"gesamt: {n_tot:,d} Beobachtungen, {s_tot:,d} Serien")
for lo, up in ((0.0, 0.1), (0.1, 0.25), (0.25, 0.4), (0.4, 1.0), (1.0, 3.0)):
    sel = (h > lo) & (h <= up)
    print(f"  {lo:5.2f}-{up:5.2f} h: {sel.sum():>8,d} Beob. "
          f"({sel.sum() / n_tot * 100:5.2f} %), "
          f"{df.loc[sel, 'GroupId'].nunique():>7,d} Serien "
          f"({df.loc[sel, 'GroupId'].nunique() / s_tot * 100:5.2f} %)")

# ------------------------------------------------- 4) Symmetrischer Trim
print("\n" + "=" * 78)
print("4) SYMMETRISCHER TRIM")
print("=" * 78)
left_share = (h > HMAX).mean()
print(f"Der linke Trim bei {HMAX:.0f} h schneidet die obersten "
      f"{left_share * 100:.2f} % der Beobachtungen ab.")
h_right = float(np.quantile(h, left_share))
print(f"Spiegelbildlich rechts: {left_share * 100:.2f}-%-Quantile = "
      f"{h_right:.3f} h ({h_right * 60:.0f} min vor Anpfiff).")

rows = []
for lab, hmin in (("kein Trim rechts", hours.min()),
                  (f"symmetrisch ({h_right:.2f} h)", h_right),
                  ("0,25 h", 0.25), ("0,5 h", 0.5)):
    msk = m48 & (hours >= hmin)
    cb, _ = sup_crit(cov_bt, se_bt, msk)
    pw, si, si_mask = counts(se_bt, cb, msk)
    share = ((h >= hmin) & (h <= HMAX)).mean()
    rows.append({"Trim rechts": lab, "Gitterpunkte": int(msk.sum()),
                 "sup_t": cb, "punktweise": pw, "simultan": si,
                 "Datenanteil": share})
tt = pd.DataFrame(rows)
print("\n" + tt.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
tt.to_csv(f"{OUT}/ns4_final_trim.csv", index=False)

# Endgueltige Kurve mit Bootstrap-Band, volles Fenster
final = pd.DataFrame({
    "hours": hours, "beta_1": b1, "se_boot": se_bt, "se_sandwich": se_sw,
    "pw_lo": b1 - 1.959964 * se_bt, "pw_up": b1 + 1.959964 * se_bt,
    "sim_lo": b1 - crit_bt * se_bt, "sim_up": b1 + crit_bt * se_bt,
})
final.to_csv(f"{OUT}/ns4_final_band.csv", index=False)
print("\nDateien: ns4_final_se.csv, ns4_final_counts.csv, "
      "ns4_final_trim.csv, ns4_final_band.csv")
