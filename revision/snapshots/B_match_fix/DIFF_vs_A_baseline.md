# B_match_fix vs. A_baseline

## values (20 keys compared, 22 baseline keys not produced by this stage)

| key | A_baseline | B_match_fix | delta |
|---|---|---|---|
| bm_quantile | 25 | 25.0 | - |
| ts_dur_from | 12 | 12 | - |
| ts_dur_till | 72 | 72 | - |
| iqr_rtrns | 0.1237 | 0.1237 | - |
| n_obs | 2,952,877 | 2952877 | - |
| n_groups | 585,938 | 585938 | - |
| is_amateur | 0.6328 | 0.6328 | - |
| is_pro | 0.3672 | 0.3672 | - |
| frac_missings | 0.0784 | 0.0784 | - |
| n_per | 51 | 51 | - |
| avg_gamma_gmm | 0.0332 | 0.0332 | - |
| min_gamma_gmm | 0.0029 | 0.0029 | - |
| max_gamma_gmm | 0.0741 | 0.0741 | - |
| idxmax_gamma_gmm | Dafabet | Dafabet | - |
| idxmin_gamma_gmm | GGBET | GGBET | - |
| adf_stat | -5.35 | -5.35 | - |
| adf_p | 0.0002 | 0.0002 | - |
| bootstr_std | 0.0258 | 0.0249 | -0.0009 |
| bootstr_up | 0.7918 | 0.7902 | -0.0016 |
| bootstr_low | 0.6908 | 0.6925 | +0.0017 |

**3 of 20 values changed.**

Not produced by B_match_fix (Bayesian block off): `crawl_start`, `crawl_end`, `crawl_dur`, `n_bm_tot`, `n_matches_tot`, `gamma_med_nuts`, `gamma_lower_nuts`, `gamma_upper_nuts`, `corr_gamma_loss`, `ts_dur_med`, `n_chains`, `n_draws`, `n_tune`, `n_cores`, `targ_acpt`, `hdi`, `vi_n_iter`, `vi_n_draws`, `gamma_fav`, `gamma_udd`, `gamma_pro`, `gamma_amat`

## Table 3 - Predictability of Close to End Returns (`res_gpm`)

- identical (10 rows x 6 cols)

## Table 4 - Relative Forecast Accuracy of Opening and Closing Prices (`res_rfa`)

- identical (10 rows x 6 cols)

## Table 5 - Winning Rates at Different Price Change Magnitudes (`res_wp`)

- identical (12 rows x 6 cols)

## Table 6 - Winning Rates vs. Price Change Magnitudes (`res_wp_re`)

- 3 of 36 cells changed:

| row | column | A_baseline | B_match_fix | delta |
|---|---|---|---|---|
| AvgChange | Std.Err. | 0.026 | 0.025 | -0.001 |
| AvgChange | [0.025 | 0.691 | 0.692 | +0.001 |
| AvgChange | 0.975] | 0.792 | 0.79 | -0.002 |

## Table 7 - Relative Forecast Accuracy by Bookmaker (`res_rfa_tot`)

- identical (25 rows x 7 cols)

## RMSE per bookmaker (behind `rmse.pdf`)

- 24 rows x 1 columns compared

| column | max |delta| | mean |delta| | n changed |
|---|---|---|---|
| rmse | 8.88178e-16 | 5.08852e-16 | 0 |

## GMM gamma per bookmaker (CUE)

- not comparable: present only in ['B_match_fix']

## beta_1 path (unbiasedness regressions)

- not comparable: present only in ['B_match_fix']

## Percentiles where beta_1 is indistinguishable from 1

- A_baseline: 31 percentiles
- B_match_fix: 28 percentiles
- only in A_baseline: [4, 6, 8, 10, 12, 30, 32, 34, 36, 38]
- only in B_match_fix: [72, 74, 76, 84, 86, 92, 94]
