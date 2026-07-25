# Stage A reference snapshot

Frozen state of every quantity that stages B/C/D are compared against.

## Provenance

- HEAD at snapshot time: `4cc781d` (`4cc781dd84bf2a391520446a726e0f4aa3e10a96`)
- tag `pre-revision-baseline`: `1067d77`
- `git diff pre-revision-baseline HEAD -- reports data`:
  (empty -- committed artifacts are byte-identical to the baseline tag)

The only source change since the tag is the look-ahead fix in
`src/pfd/helpers/impute_missings.py` (commit a2b694e), which has **not** been
propagated into any artifact yet. Stage A therefore equals
`pre-revision-baseline`, and the Stage B delta isolates the match fix.

## Contents

| file | what |
|---|---|
| `values.csv` | all 42 keys from `reports/values/values.dat` |
| `table3_res_gpm.{csv,tex}` | Table 3 - predictability of close-to-end returns |
| `table4_res_rfa.{csv,tex}` | Table 4 - relative forecast accuracy, pooled |
| `table5_res_wp.{csv,tex}` | Table 5 - winning rates by price-change interval |
| `table6_res_wp_re.{csv,tex}` | Table 6 - winning rates vs. price change |
| `table7_res_rfa_tot.{csv,tex}` | Table 7 - relative forecast accuracy by bookmaker |
| `gmm.csv` | GMM gamma statistics available today |
| `rmse_by_bookie.csv` | the 24 numbers behind `rmse.pdf` |
| `signific_time_idx.csv` | percentiles behind the beta_1 path in `unbiased_reg.pdf` |
| `figures/` | byte copies of the four core figures + sha256 |

## Known gaps in this snapshot

1. **Per-segment GMM gammas do not exist.** `estimate_gmm_learning_rate()`
   keeps only mean/min/max/argmin/argmax of the bookmaker-specific gammas;
   the 24 individual gamma/std/J-stat/p-value tuples are drawn into
   `gmm_params.pdf` and then discarded. Segment-level comparison against
   Stage A is therefore impossible without re-running the baseline code.
   From Stage B on, the runner persists them as `gmm_by_bookie.csv`.
2. **The beta_1 path is only stored in reduced form.** Only the percentiles at
   which beta_1 is statistically indistinguishable from 1 are saved, not the
   50 (beta_1, SE) pairs. Stage B onwards persists the full curve.
3. **Figures can only be compared as bytes here**, not numerically, except
   for `rmse.pdf` and (partially) `unbiased_reg.pdf`.
