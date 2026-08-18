# Unterschiede zur publizierten Version

- **Stufe:** `live`
- **Referenz:** `revision/snapshots/A_baseline` (publizierter Stand; NICHT der Tag `pre-revision-baseline`, zwischen beiden liegen drei Commits Code-Drift)
- **Erzeugt:** 2026-08-18 11:54 UTC von `revision/compare_to_published.py`

## 1) values (42 Schlüssel vergleichbar, 0 von dieser Stufe nicht erzeugt)

| key | publiziert | aktuell | Delta | rel. |
|---|---:|---:|---:|---:|
| `iqr_rtrns` | 0.1237 | 0.1207 | -0.003 | -2.43 % |
| `gamma_med_nuts` | 0.0494 | 0.0036 | -0.0458 | -92.71 % |
| `gamma_lower_nuts` | 0.0324 | 0 | -0.0324 | -100.00 % |
| `gamma_upper_nuts` | 0.0624 | 0.0075 | -0.0549 | -87.98 % |
| `avg_gamma_gmm` | 0.0332 | 0.0035 | -0.0297 | -89.46 % |
| `min_gamma_gmm` | 0.0029 | -0.0004 | -0.0033 | -113.79 % |
| `max_gamma_gmm` | 0.0741 | 0.0088 | -0.0653 | -88.12 % |
| `idxmax_gamma_gmm` | Dafabet | 10Bet | — | — |
| `idxmin_gamma_gmm` | GGBET | Pinnacle | — | — |
| `adf_stat` | -5.35 | -7.47 | -2.12 | -39.63 % |
| `adf_p` | 0.0002 | 0 | -0.0002 | -100.00 % |
| `corr_gamma_loss` | -0.2414 | -0.3199 | -0.0785 | -32.52 % |
| `bootstr_std` | 0.0258 | 0.0307 | +0.0049 | +18.99 % |
| `bootstr_up` | 0.7918 | 0.8808 | +0.089 | +11.24 % |
| `bootstr_low` | 0.6908 | 0.7604 | +0.0696 | +10.08 % |
| `gamma_fav` | 0.0608 | 0.0085 | -0.0523 | -86.02 % |
| `gamma_udd` | 0.0215 | 0.0011 | -0.0204 | -94.88 % |
| `gamma_pro` | 0.0389 | 0.0075 | -0.0314 | -80.72 % |
| `gamma_amat` | 0.0354 | 0.0018 | -0.0336 | -94.92 % |

**19 von 42 geändert, 23 unverändert (nicht aufgelistet).**

## 2) Tabellen 3-7

### Tabelle 3 — Predictability of Close-to-End Returns (`res_gpm`)

- **37 von 60 Zellen geändert**

| Zeile | Spalte | publiziert | aktuell | Delta |
|---|---|---:|---:|---:|
| Intercept | Coef. | -0.05 | 0.005 | +0.055 |
| Intercept | Std.Err. | 0.006 | 0.007 | +0.001 |
| Intercept | z | -7.989 | 0.751 | +8.74 |
| Intercept | P> \|z\| | 0 | 0.453 | +0.453 |
| Intercept | [0.025 | -0.063 | -0.008 | +0.055 |
| Intercept | 0.975] | -0.038 | 0.018 | +0.056 |
| RtrnOpnCls | Coef. | 0.023 | 0.028 | +0.005 |
| RtrnOpnCls | Std.Err. | 0.019 | 0.022 | +0.003 |
| RtrnOpnCls | z | 1.188 | 1.276 | +0.088 |
| RtrnOpnCls | P> \|z\| | 0.235 | 0.202 | -0.033 |
| RtrnOpnCls | 0.975] | 0.061 | 0.07 | +0.009 |
| TsDur | Coef. | -0.006 | -0.007 | -0.001 |
| TsDur | z | -1.831 | -2.224 | -0.393 |
| TsDur | P> \|z\| | 0.067 | 0.026 | -0.041 |
| TsDur | [0.025 | -0.012 | -0.013 | -0.001 |
| TsDur | 0.975] | 0 | -0.001 | -0.001 |
| Compet_Challenger_Men | Coef. | -0.024 | -0.012 | +0.012 |
| Compet_Challenger_Men | z | -3.126 | -1.517 | +1.609 |
| Compet_Challenger_Men | P> \|z\| | 0.002 | 0.129 | +0.127 |
| Compet_Challenger_Men | [0.025 | -0.039 | -0.028 | +0.011 |
| Compet_Challenger_Men | 0.975] | -0.009 | 0.004 | +0.013 |
| Compet_ITF_Men | Coef. | -0.072 | -0.058 | +0.014 |
| Compet_ITF_Men | Std.Err. | 0.008 | 0.009 | +0.001 |
| Compet_ITF_Men | z | -8.82 | -6.67 | +2.15 |
| Compet_ITF_Men | [0.025 | -0.088 | -0.075 | +0.013 |
| Compet_ITF_Men | 0.975] | -0.056 | -0.041 | +0.015 |
| Compet_Misc | Coef. | 0.005 | 0.03 | +0.025 |
| Compet_Misc | Std.Err. | 0.047 | 0.05 | +0.003 |
| Compet_Misc | z | 0.104 | 0.603 | +0.499 |
| Compet_Misc | P> \|z\| | 0.917 | 0.546 | -0.371 |
| Compet_Misc | [0.025 | -0.088 | -0.068 | +0.02 |
| Compet_Misc | 0.975] | 0.097 | 0.128 | +0.031 |
| Compet_WTA | Std.Err. | 0.009 | 0.01 | +0.001 |
| Compet_WTA | z | -5.106 | -4.889 | +0.217 |
| Compet_WTA | [0.025 | -0.064 | -0.066 | -0.002 |
| Compet_WTA | 0.975] | -0.029 | -0.028 | +0.001 |
| RtrnOpnCls Var | Std.Err. | — | 0.005 | — |

### Tabelle 4 — Relative Forecast Accuracy of Opening/Closing Prices (`res_rfa`)

- **15 von 60 Zellen geändert**

| Zeile | Spalte | publiziert | aktuell | Delta |
|---|---|---:|---:|---:|
| Intercept | Std.Err. | 0 | 0.001 | +0.001 |
| Intercept | z | 5.376 | 3.839 | -1.537 |
| Intercept | [0.025 | 0.002 | 0.001 | -0.001 |
| Intercept | 0.975] | 0.003 | 0.004 | +0.001 |
| Exog | z | -7.062 | -6.288 | +0.774 |
| TsDur | z | 4.015 | 3.812 | -0.203 |
| Compet_Challenger_Men | z | 4.385 | 4.007 | -0.378 |
| Compet_Challenger_Men | 0.975] | 0.003 | 0.002 | -0.001 |
| Compet_ITF_Men | z | 7.719 | 6.737 | -0.982 |
| Compet_ITF_Men | [0.025 | 0.003 | 0.002 | -0.001 |
| Compet_Misc | Std.Err. | 0.003 | 0.002 | -0.001 |
| Compet_Misc | z | -3.32 | -3.325 | -0.005 |
| Compet_Misc | [0.025 | -0.013 | -0.012 | +0.001 |
| Compet_WTA | z | 6.168 | 5.913 | -0.255 |
| Compet_WTA | 0.975] | 0.004 | 0.003 | -0.001 |

### Tabelle 5 — Winning Rates at Different Price-Change Magnitudes (`res_wp`)

- **58 von 72 Zellen geändert**

| Zeile | Spalte | publiziert | aktuell | Delta |
|---|---|---:|---:|---:|
| $]-1, -0.15]$ | Avg. Change | -0.192 | -0.1955 | -0.0035 |
| $]-1, -0.15]$ | Avg. Moves | 13 | 13.2 | +0.2 |
| $]-1, -0.15]$ | No. Matches | 1,484 | 969 | -515 |
| $]-1, -0.15]$ | Winning Rate | 0.3369 | 0.3292 | -0.0077 |
| $]-1, -0.15]$ | Z-statistic | -13.3 | -11.3 | +2 |
| $]-0.15, -0.12]$ | Avg. Change | -0.1322 | -0.1327 | -0.0005 |
| $]-0.15, -0.12]$ | Avg. Moves | 11.6 | 12.2 | +0.6 |
| $]-0.15, -0.12]$ | No. Matches | 2,165 | 1,722 | -443 |
| $]-0.15, -0.12]$ | Winning Rate | 0.4125 | 0.4048 | -0.0077 |
| $]-0.15, -0.12]$ | Z-statistic | -8.27 | -8.05 | +0.22 |
| $]-0.12, -0.09]$ | Avg. Change | -0.1028 | -0.1029 | -0.0001 |
| $]-0.12, -0.09]$ | Avg. Moves | 10.8 | 11.2 | +0.4 |
| $]-0.12, -0.09]$ | No. Matches | 5,089 | 4,218 | -871 |
| $]-0.12, -0.09]$ | Winning Rate | 0.4429 | 0.4222 | -0.0207 |
| $]-0.12, -0.09]$ | Z-statistic | -8.2 | -10.2 | -2 |
| $]-0.09, -0.06]$ | Avg. Moves | 9.43 | 9.63 | +0.2 |
| $]-0.09, -0.06]$ | No. Matches | 11,422 | 10,470 | -952 |
| $]-0.09, -0.06]$ | Winning Rate | 0.452 | 0.4521 | +0.0001 |
| $]-0.09, -0.06]$ | Z-statistic | -10.3 | -9.84 | +0.46 |
| $]-0.06, -0.03]$ | Avg. Change | -0.0434 | -0.0432 | +0.0002 |
| $]-0.06, -0.03]$ | Avg. Moves | 8.31 | 8.51 | +0.2 |
| $]-0.06, -0.03]$ | No. Matches | 24,443 | 23,866 | -577 |
| $]-0.06, -0.03]$ | Winning Rate | 0.478 | 0.4708 | -0.0072 |
| $]-0.06, -0.03]$ | Z-statistic | -6.88 | -9.03 | -2.15 |
| $]-0.03, 0[$ | Avg. Change | -0.0153 | -0.0144 | +0.0009 |
| $]-0.03, 0[$ | Avg. Moves | 6.87 | 6.91 | +0.04 |
| $]-0.03, 0[$ | No. Matches | 41,330 | 44,224 | +2,894 |
| $]-0.03, 0[$ | Winning Rate | 0.4853 | 0.4892 | +0.0039 |
| $]-0.03, 0[$ | Z-statistic | -5.99 | -4.53 | +1.46 |
| $]0, 0.03[$ | Avg. Change | 0.0152 | 0.0144 | -0.0008 |
| $]0, 0.03[$ | Avg. Moves | 6.89 | 6.87 | -0.02 |
| $]0, 0.03[$ | No. Matches | 40,595 | 45,421 | +4,826 |
| $]0, 0.03[$ | Winning Rate | 0.5279 | 0.5331 | +0.0052 |
| $]0, 0.03[$ | Z-statistic | 11.2 | 14.1 | +2.9 |
| $[0.03, 0.06[$ | Avg. Change | 0.0434 | 0.0432 | -0.0002 |
| $[0.03, 0.06[$ | Avg. Moves | 8.37 | 8.47 | +0.1 |
| $[0.03, 0.06[$ | No. Matches | 23,742 | 24,283 | +541 |
| $[0.03, 0.06[$ | Winning Rate | 0.5462 | 0.5499 | +0.0037 |
| $[0.03, 0.06[$ | Z-statistic | 14.3 | 15.6 | +1.3 |
| $[0.06, 0.09[$ | Avg. Change | 0.0727 | 0.0726 | -0.0001 |
| $[0.06, 0.09[$ | Avg. Moves | 9.63 | 9.86 | +0.23 |
| $[0.06, 0.09[$ | No. Matches | 11,062 | 10,588 | -474 |
| $[0.06, 0.09[$ | Winning Rate | 0.5629 | 0.5652 | +0.0023 |
| $[0.06, 0.09[$ | Z-statistic | 13.3 | 13.5 | +0.2 |
| $[0.09, 0.12[$ | Avg. Moves | 10.7 | 11 | +0.3 |
| $[0.09, 0.12[$ | No. Matches | 4,644 | 4,040 | -604 |
| $[0.09, 0.12[$ | Winning Rate | 0.5896 | 0.5911 | +0.0015 |
| $[0.09, 0.12[$ | Z-statistic | 12.4 | 11.8 | -0.6 |
| $[0.12, 0.15[$ | Avg. Change | 0.133 | 0.1324 | -0.0006 |
| $[0.12, 0.15[$ | Avg. Moves | 11.5 | 11.6 | +0.1 |
| $[0.12, 0.15[$ | No. Matches | 2,044 | 1,710 | -334 |
| $[0.12, 0.15[$ | Winning Rate | 0.5866 | 0.5848 | -0.0018 |
| $[0.12, 0.15[$ | Z-statistic | 7.95 | 7.11 | -0.84 |
| $[0.15, 1[$ | Avg. Change | 0.1927 | 0.1912 | -0.0015 |
| $[0.15, 1[$ | Avg. Moves | 13.1 | 13.4 | +0.3 |
| $[0.15, 1[$ | No. Matches | 1,554 | 1,152 | -402 |
| $[0.15, 1[$ | Winning Rate | 0.6345 | 0.6519 | +0.0174 |
| $[0.15, 1[$ | Z-statistic | 11 | 10.8 | -0.2 |

### Tabelle 6 — Winning Rates vs. Price-Change Magnitudes (`res_wp_re`)

- **14 von 36 Zellen geändert**

| Zeile | Spalte | publiziert | aktuell | Delta |
|---|---|---:|---:|---:|
| Intercept | Coef. | 0.505 | 0.504 | -0.001 |
| Intercept | Std.Err. | 0.003 | 0.004 | +0.001 |
| Intercept | z | 159.179 | 140.7 | -18.479 |
| Intercept | [0.025 | 0.499 | 0.497 | -0.002 |
| AvgChange | Coef. | 0.741 | 0.821 | +0.08 |
| AvgChange | Std.Err. | 0.026 | 0.031 | +0.005 |
| AvgChange | z | 28.106 | 17.399 | -10.707 |
| AvgChange | [0.025 | 0.691 | 0.76 | +0.069 |
| AvgChange | 0.975] | 0.792 | 0.881 | +0.089 |
| NumMatches | z | 0.478 | 0.682 | +0.204 |
| NumMatches | P> \|z\| | 0.632 | 0.495 | -0.137 |
| Bookies x AvgChange Cov | Coef. | -0 | -0.001 | -0.001 |
| AvgChange Var | Coef. | 0.006 | 0.043 | +0.037 |
| AvgChange Var | Std.Err. | 0.06 | 0.273 | +0.213 |

### Tabelle 7 — Relative Forecast Accuracy by Bookmaker (`res_rfa_tot`)

- **151 von 175 Zellen geändert**

| Zeile | Spalte | publiziert | aktuell | Delta |
|---|---|---:|---:|---:|
| 10Bet | N | 5,129 | 5,461 | +332 |
| 10Bet | RMSE(e_0) | 0.4499 | 0.4477 | -0.0022 |
| 10Bet | RMSE(e_T) | 0.4466 | 0.4451 | -0.0015 |
| 10Bet | beta_0 | 0.0009 | 0.0017 | +0.0008 |
| 10Bet | beta_1 | 0.002 | -0.0009 | -0.0029 |
| 10Bet | p(beta_0) | 0.5732 | 0.235 | -0.3382 |
| 10Bet | p(beta_1) | 0.004 | 0.1248 | +0.1208 |
| 10x10bet | N | 10,238 | 10,256 | +18 |
| 10x10bet | RMSE(e_0) | 0.4557 | 0.4549 | -0.0008 |
| 10x10bet | RMSE(e_T) | 0.4529 | 0.4521 | -0.0008 |
| 10x10bet | beta_0 | 0.0035 | 0.0032 | -0.0003 |
| 10x10bet | beta_1 | -0.0042 | -0.004 | +0.0002 |
| 10x10bet | p(beta_0) | 0.0103 | 0.011 | +0.0007 |
| 1xBet | N | 12,515 | 12,805 | +290 |
| 1xBet | RMSE(e_0) | 0.4501 | 0.447 | -0.0031 |
| 1xBet | RMSE(e_T) | 0.4462 | 0.4434 | -0.0028 |
| 1xBet | beta_0 | 0.0038 | 0.0049 | +0.0011 |
| 1xBet | beta_1 | -0.0064 | -0.0065 | -0.0001 |
| 1xBet | p(beta_0) | 0.015 | 0.0004 | -0.0146 |
| 888sport | N | 4,792 | 4,893 | +101 |
| 888sport | RMSE(e_0) | 0.4605 | 0.4597 | -0.0008 |
| 888sport | RMSE(e_T) | 0.4579 | 0.457 | -0.0009 |
| 888sport | beta_1 | -0.0067 | -0.0061 | +0.0006 |
| 888sport | p(beta_0) | 0.275 | 0.2365 | -0.0385 |
| Alphabet | N | 10,647 | 10,666 | +19 |
| Alphabet | RMSE(e_0) | 0.4562 | 0.455 | -0.0012 |
| Alphabet | RMSE(e_T) | 0.4537 | 0.4525 | -0.0012 |
| Alphabet | beta_0 | 0.0034 | 0.0032 | -0.0002 |
| Alphabet | beta_1 | -0.0044 | -0.0041 | +0.0003 |
| Alphabet | p(beta_0) | 0.0098 | 0.0082 | -0.0016 |
| BetInAsia | N | 6,124 | 6,359 | +235 |
| BetInAsia | RMSE(e_0) | 0.4645 | 0.4633 | -0.0012 |
| BetInAsia | RMSE(e_T) | 0.463 | 0.4622 | -0.0008 |
| BetInAsia | beta_0 | 0.0013 | 0.0015 | +0.0002 |
| BetInAsia | beta_1 | 0.0002 | -0.0017 | -0.0019 |
| BetInAsia | p(beta_0) | 0.3838 | 0.2636 | -0.1202 |
| BetInAsia | p(beta_1) | 0.7426 | 0.0007 | -0.7419 |
| BetVictor | N | 4,789 | 4,910 | +121 |
| BetVictor | RMSE(e_0) | 0.4645 | 0.4635 | -0.001 |
| BetVictor | RMSE(e_T) | 0.4632 | 0.4622 | -0.001 |
| BetVictor | beta_0 | 0.0025 | 0.0021 | -0.0004 |
| BetVictor | beta_1 | -0.005 | -0.0046 | +0.0004 |
| BetVictor | p(beta_0) | 0.1028 | 0.1462 | +0.0434 |
| Betfair | N | 3,093 | 3,268 | +175 |
| Betfair | RMSE(e_0) | 0.4589 | 0.4568 | -0.0021 |
| Betfair | RMSE(e_T) | 0.4574 | 0.4554 | -0.002 |
| Betfair | beta_0 | -0.0008 | -0.0009 | -0.0001 |
| Betfair | beta_1 | -0.0011 | -0.0012 | -0.0001 |
| Betfair | p(beta_0) | 0.6493 | 0.5648 | -0.0845 |
| Betfair | p(beta_1) | 0.204 | 0.1155 | -0.0885 |
| Betfred | N | 4,083 | 4,085 | +2 |
| Betfred | RMSE(e_0) | 0.4597 | 0.4589 | -0.0008 |
| Betfred | RMSE(e_T) | 0.4549 | 0.454 | -0.0009 |
| Betfred | beta_0 | 0.0048 | 0.0049 | +0.0001 |
| Betfred | beta_1 | -0.0069 | -0.0066 | +0.0003 |
| Betfred | p(beta_0) | 0.0064 | 0.0033 | -0.0031 |
| Betsafe | N | 4,078 | 4,131 | +53 |
| Betsafe | RMSE(e_0) | 0.4607 | 0.46 | -0.0007 |
| Betsafe | RMSE(e_T) | 0.458 | 0.4573 | -0.0007 |
| Betsafe | beta_0 | 0.0032 | 0.003 | -0.0002 |
| Betsafe | beta_1 | -0.0047 | -0.0044 | +0.0003 |
| Betsafe | p(beta_0) | 0.0348 | 0.034 | -0.0008 |
| Betsson | N | 4,072 | 4,145 | +73 |
| Betsson | RMSE(e_0) | 0.4607 | 0.46 | -0.0007 |
| Betsson | RMSE(e_T) | 0.4581 | 0.4574 | -0.0007 |
| Betsson | beta_0 | 0.0034 | 0.0031 | -0.0003 |
| Betsson | beta_1 | -0.0048 | -0.0044 | +0.0004 |
| Betsson | p(beta_0) | 0.0319 | 0.0326 | +0.0007 |
| Betway | N | 6,787 | 7,063 | +276 |
| Betway | RMSE(e_0) | 0.4599 | 0.4583 | -0.0016 |
| Betway | RMSE(e_T) | 0.4563 | 0.4551 | -0.0012 |
| Betway | beta_0 | 0.0022 | 0.0021 | -0.0001 |
| Betway | beta_1 | -0.0035 | -0.0052 | -0.0017 |
| Betway | p(beta_0) | 0.1449 | 0.135 | -0.0099 |
| ComeOn | N | 7,375 | 7,702 | +327 |
| ComeOn | RMSE(e_0) | 0.452 | 0.4504 | -0.0016 |
| ComeOn | RMSE(e_T) | 0.449 | 0.448 | -0.001 |
| ComeOn | beta_0 | -0.0006 | 0.0013 | +0.0019 |
| ComeOn | beta_1 | 0.0016 | -0.0004 | -0.002 |
| ComeOn | p(beta_0) | 0.6688 | 0.3056 | -0.3632 |
| ComeOn | p(beta_1) | 0.0055 | 0.4429 | +0.4374 |
| Curebet | N | 6,775 | 6,785 | +10 |
| Curebet | RMSE(e_0) | 0.4552 | 0.454 | -0.0012 |
| Curebet | RMSE(e_T) | 0.452 | 0.4508 | -0.0012 |
| Curebet | beta_0 | 0.0041 | 0.0039 | -0.0002 |
| Curebet | beta_1 | -0.0043 | -0.0038 | +0.0005 |
| Curebet | p(beta_0) | 0.0074 | 0.0058 | -0.0016 |
| Dafabet | N | 3,372 | 3,400 | +28 |
| Dafabet | RMSE(e_0) | 0.4547 | 0.454 | -0.0007 |
| Dafabet | RMSE(e_T) | 0.4526 | 0.4521 | -0.0005 |
| Dafabet | beta_0 | 0.0048 | 0.0045 | -0.0003 |
| Dafabet | p(beta_0) | 0.005 | 0.0045 | -0.0005 |
| GGBET | N | 10,940 | 11,286 | +346 |
| GGBET | RMSE(e_0) | 0.4492 | 0.4462 | -0.003 |
| GGBET | RMSE(e_T) | 0.4466 | 0.4437 | -0.0029 |
| GGBET | beta_0 | 0.001 | 0.0015 | +0.0005 |
| GGBET | beta_1 | -0.0044 | -0.0041 | +0.0003 |
| GGBET | p(beta_0) | 0.4614 | 0.2338 | -0.2276 |
| Interwetten | N | 4,928 | 4,974 | +46 |
| Interwetten | RMSE(e_0) | 0.459 | 0.4557 | -0.0033 |
| Interwetten | RMSE(e_T) | 0.4546 | 0.4514 | -0.0032 |
| Interwetten | beta_1 | -0.0051 | -0.0052 | -0.0001 |
| Interwetten | p(beta_0) | 0.1275 | 0.0983 | -0.0292 |
| Lasbet | N | 10,550 | 10,570 | +20 |
| Lasbet | RMSE(e_0) | 0.456 | 0.4547 | -0.0013 |
| Lasbet | RMSE(e_T) | 0.4534 | 0.4522 | -0.0012 |
| Lasbet | beta_0 | 0.0031 | 0.0029 | -0.0002 |
| Lasbet | beta_1 | -0.0045 | -0.0042 | +0.0003 |
| Lasbet | p(beta_0) | 0.0194 | 0.0166 | -0.0028 |
| Marathonbet | N | 11,496 | 11,638 | +142 |
| Marathonbet | RMSE(e_0) | 0.4511 | 0.4491 | -0.002 |
| Marathonbet | RMSE(e_T) | 0.4479 | 0.4459 | -0.002 |
| Marathonbet | beta_0 | 0.0055 | 0.0052 | -0.0003 |
| Marathonbet | beta_1 | -0.007 | -0.0065 | +0.0005 |
| NordicBet | N | 4,077 | 4,140 | +63 |
| NordicBet | RMSE(e_0) | 0.4617 | 0.4612 | -0.0005 |
| NordicBet | RMSE(e_T) | 0.4591 | 0.4586 | -0.0005 |
| NordicBet | beta_0 | 0.0036 | 0.0032 | -0.0004 |
| NordicBet | beta_1 | -0.0048 | -0.0045 | +0.0003 |
| NordicBet | p(beta_0) | 0.0206 | 0.0249 | +0.0043 |
| Pinnacle | N | 8,357 | 8,639 | +282 |
| Pinnacle | RMSE(e_0) | 0.4656 | 0.4646 | -0.001 |
| Pinnacle | RMSE(e_T) | 0.464 | 0.4634 | -0.0006 |
| Pinnacle | beta_0 | 0.0011 | 0.0014 | +0.0003 |
| Pinnacle | beta_1 | 0.0009 | -0.001 | -0.0019 |
| Pinnacle | p(beta_0) | 0.3362 | 0.1949 | -0.1413 |
| Pinnacle | p(beta_1) | 0.0639 | 0.0144 | -0.0495 |
| Suprabets | N | 10,425 | 10,450 | +25 |
| Suprabets | RMSE(e_0) | 0.4565 | 0.4552 | -0.0013 |
| Suprabets | RMSE(e_T) | 0.4537 | 0.4524 | -0.0013 |
| Suprabets | beta_0 | 0.0025 | 0.0024 | -0.0001 |
| Suprabets | beta_1 | -0.0041 | -0.0039 | +0.0002 |
| Suprabets | p(beta_0) | 0.0558 | 0.0527 | -0.0031 |
| VOBET | N | 10,711 | 10,731 | +20 |
| VOBET | RMSE(e_0) | 0.4553 | 0.4541 | -0.0012 |
| VOBET | RMSE(e_T) | 0.4529 | 0.4516 | -0.0013 |
| VOBET | beta_0 | 0.0029 | 0.0028 | -0.0001 |
| VOBET | beta_1 | -0.0043 | -0.004 | +0.0003 |
| VOBET | p(beta_0) | 0.0267 | 0.0233 | -0.0034 |
| Vulkan Bet | N | 4,221 | 4,306 | +85 |
| Vulkan Bet | RMSE(e_0) | 0.4508 | 0.4487 | -0.0021 |
| Vulkan Bet | RMSE(e_T) | 0.4494 | 0.4473 | -0.0021 |
| Vulkan Bet | beta_0 | -0.0014 | -0.0007 | +0.0007 |
| Vulkan Bet | p(beta_0) | 0.2786 | 0.5602 | +0.2816 |
| Vulkan Bet | p(beta_1) | 0.0093 | 0.0038 | -0.0055 |
| All | N | 169,574 | 172,663 | +3,089 |
| All | RMSE(e_0) | 0.4561 | 0.4546 | -0.0015 |
| All | RMSE(e_T) | 0.4534 | 0.4519 | -0.0015 |
| All | beta_0 | 0.0025 | 0.0026 | +0.0001 |
| All | beta_1 | -0.0036 | -0.0039 | -0.0003 |
| All | p(beta_0) | 0 | 0.0001 | +0.0001 |

## 3) GMM

- keine `gmm_by_bookie.csv` in dieser Stufe

> **gamma je Bookmaker ist gegen A_baseline nicht vergleichbar.** Der publizierte Lauf hat nur Mittelwert/Min/Max/Argmin/Argmax behalten, die 24 Einzelwerte wurden nach dem Zeichnen verworfen (`A_baseline/MANIFEST.md`, Lücke 1).

## 4) beta_1-Pfad

> **Der volle Pfad ist gegen A_baseline nicht vergleichbar.** Der publizierte Lauf hat nur die Perzentile gespeichert, an denen beta_1 von 1 ununterscheidbar ist, nicht die (beta_1, SE)-Paare (`A_baseline/MANIFEST.md`, Lücke 2). max/mittleres |Delta| sind daher nur zwischen zwei Stufen mit `beta1_curve.csv` bestimmbar.

- keine `beta1_curve.csv` in dieser Stufe

## 5) Perzentile, an denen beta_1 von 1 ununterscheidbar ist

- nicht auf beiden Seiten vorhanden

## 6) RMSE je Bookmaker

- nicht auf beiden Seiten vorhanden

