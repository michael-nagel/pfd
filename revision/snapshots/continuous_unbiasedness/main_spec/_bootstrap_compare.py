#!/usr/bin/env python3
"""Bootstrap-SEs gegen den CR1-Sandwich (M_c, Cluster = Matchup).

Der Sandwich korrigiert nur mit dem Skalar G/(G-1) * (N-1)/(N-K) und sieht die
starke Unbalanciertheit der Cluster nicht (1 bis 24 Bookmaker je Matchup,
Median 7). Der Cluster-Bootstrap (`_cluster_bootstrap.py`, B = 100) ist davon
unabhängig.
"""

import numpy as np
import pandas as pd

OUT = "revision/snapshots/continuous_unbiasedness/main_spec"
MARKS = [24.0, 12.0, 6.0, 3.0, 1.0, 0.25]

cr = pd.read_csv(f"{OUT}/cluster_robust_beta1.csv")
boot = np.vstack([np.load(f"{OUT}/bootstrap_beta1_part{p}.npy")
                  for p in (0, 1)])
B = len(boot)
print(f"Bootstrap: B = {B} Replikate, Gitter {boot.shape[1]} Punkte\n")

res = pd.DataFrame({
    "hours": cr["hours"],
    "beta_1": cr["beta_1"],
    "se_cluster": cr["se_cluster"],
    "se_boot": boot.std(axis=0, ddof=1),
    "se_lmer_model": cr["se_lmer_model"],
    "boot_mean": boot.mean(axis=0),
    "boot_p025": np.percentile(boot, 2.5, axis=0),
    "boot_p975": np.percentile(boot, 97.5, axis=0),
})
res["ratio_boot_cluster"] = res["se_boot"] / res["se_cluster"]
res["bias"] = res["boot_mean"] - res["beta_1"]
res.to_csv(f"{OUT}/bootstrap_vs_sandwich.csv", index=False)

r = res["ratio_boot_cluster"]
print("SE-Verhältnis Bootstrap / CR1-Sandwich:")
print(f"  Median {r.median():.3f}   Mittel {r.mean():.3f}   "
      f"Spanne {r.min():.3f}-{r.max():.3f}")
print(f"  Punkte mit |Verhältnis - 1| > 0,15: "
      f"{int((r - 1).abs().gt(.15).sum())} von {len(r)}")
print("\nBootstrap-Bias (Mittel der Replikate - Punktschätzer):")
print(f"  Median {res['bias'].median():+.4f}   max |Bias| "
      f"{res['bias'].abs().max():.4f}")

idx = [int(np.argmin(np.abs(res["hours"] - h))) for h in MARKS]
mk = res.iloc[idx][["hours", "beta_1", "se_cluster", "se_boot",
                    "se_lmer_model", "ratio_boot_cluster", "boot_p025",
                    "boot_p975"]]
print("\nAn den Stundenmarken:")
print(mk.to_string(index=False, float_format=lambda v: f"{v:,.4f}"))
mk.to_csv(f"{OUT}/bootstrap_vs_sandwich_marks.csv", index=False)

print(f"\ngeschrieben: {OUT}/bootstrap_vs_sandwich{{,_marks}}.csv")
