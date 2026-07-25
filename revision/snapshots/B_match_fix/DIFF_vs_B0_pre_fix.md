# B_match_fix vs. B0_pre_fix

## values (20 keys compared, 0 baseline keys not produced by this stage)

| key | B0_pre_fix | B_match_fix | delta |
|---|---|---|---|
| bm_quantile | 25.0 | 25.0 | - |
| ts_dur_from | 12 | 12 | - |
| ts_dur_till | 72 | 72 | - |
| iqr_rtrns | 0.1237 | 0.1237 | - |
| n_obs | 2952877 | 2952877 | - |
| n_groups | 585938 | 585938 | - |
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
| bootstr_std | 0.0249 | 0.0249 | - |
| bootstr_up | 0.7902 | 0.7902 | - |
| bootstr_low | 0.6925 | 0.6925 | - |

**0 of 20 values changed.**

## Table 3 - Predictability of Close to End Returns (`res_gpm`)

- identical (10 rows x 6 cols)

## Table 4 - Relative Forecast Accuracy of Opening and Closing Prices (`res_rfa`)

- identical (10 rows x 6 cols)

## Table 5 - Winning Rates at Different Price Change Magnitudes (`res_wp`)

- identical (12 rows x 6 cols)

## Table 6 - Winning Rates vs. Price Change Magnitudes (`res_wp_re`)

- identical (6 rows x 6 cols)

## Table 7 - Relative Forecast Accuracy by Bookmaker (`res_rfa_tot`)

- identical (25 rows x 7 cols)

## RMSE per bookmaker (behind `rmse.pdf`)

- 24 rows x 1 columns compared

| column | max |delta| | mean |delta| | n changed |
|---|---|---|---|
| rmse | 0 | 0 | 0 |

## GMM gamma per bookmaker (CUE)

- 24 rows x 4 columns compared

| column | max |delta| | mean |delta| | n changed |
|---|---|---|---|
| gamma | 8.86719e-05 | 1.29293e-05 | 5 |
| std_gamma | 3.34689e-06 | 9.79499e-07 | 24 |
| J_stat | 0.0739223 | 0.0194134 | 24 |
| p_value | 0.00611593 | 0.00128512 | 24 |

## beta_1 path (unbiasedness regressions)

- 50 rows x 5 columns compared

| column | max |delta| | mean |delta| | n changed |
|---|---|---|---|
| beta_1 | 0.194578 | 0.0431508 | 50 |
| std_beta_1 | 0.118856 | 0.00443484 | 49 |
| beta_0 | 0.000462816 | 5.53573e-05 | 50 |
| std_beta_0 | 0.0953073 | 0.00527694 | 50 |
| rmse | 0.000132415 | 1.4644e-05 | 50 |

## Percentiles where beta_1 is indistinguishable from 1

- B0_pre_fix: 31 percentiles
- B_match_fix: 28 percentiles
- only in B0_pre_fix: [4, 6, 8, 10, 12, 30, 32, 34, 36, 38]
- only in B_match_fix: [72, 74, 76, 84, 86, 92, 94]
