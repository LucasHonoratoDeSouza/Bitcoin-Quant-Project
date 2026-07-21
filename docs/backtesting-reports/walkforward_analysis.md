# Walk-Forward Purged/Embargo Analysis

Generated on: **2026-07-21**

## Configuration
- Start date: `2020-01-01`
- Train window: `540` days
- Test window: `120` days
- Purge gap: `7` days
- Embargo gap: `3` days
- Fold step (selected): `45` days
- Target minimum folds: `28`
- Number of folds: `31`

## Fold Schedule

| Fold | Train Window | Purge | Test Window | Embargo | Test Obs |
| :--- | :--- | ---: | :--- | ---: | ---: |
| 1 | 2021-01-01 to 2022-06-24 | 7 | 2022-07-02 to 2022-10-29 | 3 | 120 |
| 2 | 2021-02-15 to 2022-08-08 | 7 | 2022-08-16 to 2022-12-13 | 3 | 120 |
| 3 | 2021-04-01 to 2022-09-22 | 7 | 2022-09-30 to 2023-01-27 | 3 | 120 |
| 4 | 2021-05-16 to 2022-11-06 | 7 | 2022-11-14 to 2023-03-13 | 3 | 120 |
| 5 | 2021-06-30 to 2022-12-21 | 7 | 2022-12-29 to 2023-04-27 | 3 | 120 |
| 6 | 2021-08-14 to 2023-02-04 | 7 | 2023-02-12 to 2023-06-11 | 3 | 120 |
| 7 | 2021-09-28 to 2023-03-21 | 7 | 2023-03-29 to 2023-07-26 | 3 | 120 |
| 8 | 2021-11-12 to 2023-05-05 | 7 | 2023-05-13 to 2023-09-09 | 3 | 120 |
| 9 | 2021-12-27 to 2023-06-19 | 7 | 2023-06-27 to 2023-10-24 | 3 | 120 |
| 10 | 2022-02-10 to 2023-08-03 | 7 | 2023-08-11 to 2023-12-08 | 3 | 120 |
| 11 | 2022-03-27 to 2023-09-17 | 7 | 2023-09-25 to 2024-01-22 | 3 | 120 |
| 12 | 2022-05-11 to 2023-11-01 | 7 | 2023-11-09 to 2024-03-07 | 3 | 120 |
| 13 | 2022-06-25 to 2023-12-16 | 7 | 2023-12-24 to 2024-04-21 | 3 | 120 |
| 14 | 2022-08-09 to 2024-01-30 | 7 | 2024-02-07 to 2024-06-05 | 3 | 120 |
| 15 | 2022-09-23 to 2024-03-15 | 7 | 2024-03-23 to 2024-07-20 | 3 | 120 |
| 16 | 2022-11-07 to 2024-04-29 | 7 | 2024-05-07 to 2024-09-03 | 3 | 120 |
| 17 | 2022-12-22 to 2024-06-13 | 7 | 2024-06-21 to 2024-10-18 | 3 | 120 |
| 18 | 2023-02-05 to 2024-07-28 | 7 | 2024-08-05 to 2024-12-02 | 3 | 120 |
| 19 | 2023-03-22 to 2024-09-11 | 7 | 2024-09-19 to 2025-01-16 | 3 | 120 |
| 20 | 2023-05-06 to 2024-10-26 | 7 | 2024-11-03 to 2025-03-02 | 3 | 120 |
| 21 | 2023-06-20 to 2024-12-10 | 7 | 2024-12-18 to 2025-04-16 | 3 | 120 |
| 22 | 2023-08-04 to 2025-01-24 | 7 | 2025-02-01 to 2025-05-31 | 3 | 120 |
| 23 | 2023-09-18 to 2025-03-10 | 7 | 2025-03-18 to 2025-07-15 | 3 | 120 |
| 24 | 2023-11-02 to 2025-04-24 | 7 | 2025-05-02 to 2025-08-29 | 3 | 120 |
| 25 | 2023-12-17 to 2025-06-08 | 7 | 2025-06-16 to 2025-10-13 | 3 | 120 |
| 26 | 2024-01-31 to 2025-07-23 | 7 | 2025-07-31 to 2025-11-27 | 3 | 120 |
| 27 | 2024-03-16 to 2025-09-06 | 7 | 2025-09-14 to 2026-01-11 | 3 | 120 |
| 28 | 2024-04-30 to 2025-10-21 | 7 | 2025-10-29 to 2026-02-25 | 3 | 120 |
| 29 | 2024-06-14 to 2025-12-05 | 7 | 2025-12-13 to 2026-04-11 | 3 | 120 |
| 30 | 2024-07-29 to 2026-01-19 | 7 | 2026-01-27 to 2026-05-26 | 3 | 120 |
| 31 | 2024-09-12 to 2026-03-05 | 7 | 2026-03-13 to 2026-07-10 | 3 | 120 |

## Out-of-Sample Aggregate

| Model | Folds | Mean Return | Median Return | Mean Sharpe | Worst Max DD | Return > BnH (folds) | Sharpe > BnH (folds) | Lower DD than BnH (folds) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| production_legacy_cooldown1 | 31 | +10.34% | +3.42% | 1.104 | -18.70% | 15/31 | 15/31 | 27/31 |
| legacy_cooldown3_baseline | 31 | +9.80% | +3.52% | 1.063 | -18.70% | 13/31 | 15/31 | 28/31 |
| legacy_confidence_research | 31 | +6.36% | +3.00% | 1.149 | -14.97% | 11/31 | 22/31 | 31/31 |
| advanced_adaptive_research | 31 | +0.76% | +0.00% | 0.401 | -10.12% | 10/31 | 13/31 | 31/31 |

## Walk-Forward Gate Decision

| Candidate | Evidence vs OOS Baseline | Decision |
| :--- | :--- | :--- |
| production_legacy_cooldown1 | higher_or_equal_mean_return=yes, higher_or_equal_mean_sharpe=yes, better_or_equal_worst_drawdown=yes | **IMPLEMENT WITH GUARDRAILS** |
| legacy_cooldown3_baseline | oos baseline | **KEEP (benchmark)** |
| legacy_confidence_research | higher_or_equal_mean_return=no, higher_or_equal_mean_sharpe=yes, better_or_equal_worst_drawdown=yes | **IMPLEMENT WITH GUARDRAILS** |
| advanced_adaptive_research | higher_or_equal_mean_return=no, higher_or_equal_mean_sharpe=no, better_or_equal_worst_drawdown=yes | **DO NOT IMPLEMENT** |

## Bootstrap Significance (OOS Daily Returns)

Method: `block`

| Comparison | Obs | Annualized Alpha | Alpha 95% CI | p(alpha<=0) | Delta Sharpe | Delta Sharpe 95% CI | p(delta_sharpe<=0) |
| :--- | ---: | ---: | :--- | ---: | ---: | :--- | ---: |
| production_vs_baseline | 3689 | +1.31% | [+0.14%, +2.72%] | 0.0123 | +0.045 | [-0.003, +0.101] | 0.0340 |
| production_vs_buy_and_hold | 3689 | -20.09% | [-38.62%, -2.60%] | 0.9850 | +0.233 | [-0.127, +0.560] | 0.1016 |
| legacy_confidence_research_vs_production | 3689 | -10.42% | [-17.97%, -3.14%] | 0.9980 | +0.018 | [-0.173, +0.222] | 0.4112 |
| legacy_confidence_research_vs_buy_and_hold | 3689 | -30.50% | [-52.13%, -8.53%] | 0.9970 | +0.251 | [-0.117, +0.594] | 0.0890 |
| advanced_adaptive_research_vs_production | 3689 | -27.01% | [-42.35%, -12.49%] | 1.0000 | -0.939 | [-1.606, -0.284] | 0.9967 |
| advanced_adaptive_research_vs_buy_and_hold | 3689 | -47.10% | [-75.33%, -19.18%] | 0.9993 | -0.705 | [-1.358, -0.067] | 0.9823 |

## Objective Production Gate

- Incumbent: `production_legacy_cooldown1`
- Selected live model: `production_legacy_cooldown1`
- Promotion allowed: `no`
- Selection rationale: No challenger met objective out-of-sample promotion criteria.
- Gate artifact: `data/signals/production_gate.json`

| Candidate | Delta Return vs Incumbent | Delta Sharpe | Delta Worst DD | p(alpha<=0) vs Incumbent | p(delta_sharpe<=0) vs Incumbent | p(delta_sharpe<=0) vs BnH | Decision |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| legacy_confidence_research | -3.98% | +0.045 | +3.73% | 0.9980 | 0.4112 | 0.0890 | **DO NOT PROMOTE** |
| advanced_adaptive_research | -9.58% | -0.703 | +8.58% | 1.0000 | 0.9967 | 0.9823 | **DO NOT PROMOTE** |

## Notes

- This validation is strictly out-of-sample by fold test windows.
- Purge and embargo are temporal guards to reduce leakage across adjacent windows.
- Strategy parameters are fixed; no per-fold re-optimization is performed.
- Production candidate promotion is now derived from objective OOS gate outputs.