# Walk-Forward Purged/Embargo Analysis

Generated on: **2026-04-22**

## Configuration
- Start date: `2020-01-01`
- Train window: `540` days
- Test window: `120` days
- Purge gap: `7` days
- Embargo gap: `3` days
- Fold step (selected): `45` days
- Target minimum folds: `28`
- Number of folds: `29`

## Fold Schedule

| Fold | Train Window | Purge | Test Window | Embargo | Test Obs |
| :--- | :--- | ---: | :--- | ---: | ---: |
| 1 | 2020-12-30 to 2022-06-22 | 7 | 2022-06-30 to 2022-10-27 | 3 | 120 |
| 2 | 2021-02-13 to 2022-08-06 | 7 | 2022-08-14 to 2022-12-11 | 3 | 120 |
| 3 | 2021-03-30 to 2022-09-20 | 7 | 2022-09-28 to 2023-01-25 | 3 | 120 |
| 4 | 2021-05-14 to 2022-11-04 | 7 | 2022-11-12 to 2023-03-11 | 3 | 120 |
| 5 | 2021-06-28 to 2022-12-19 | 7 | 2022-12-27 to 2023-04-25 | 3 | 120 |
| 6 | 2021-08-12 to 2023-02-02 | 7 | 2023-02-10 to 2023-06-09 | 3 | 120 |
| 7 | 2021-09-26 to 2023-03-19 | 7 | 2023-03-27 to 2023-07-24 | 3 | 120 |
| 8 | 2021-11-10 to 2023-05-03 | 7 | 2023-05-11 to 2023-09-07 | 3 | 120 |
| 9 | 2021-12-25 to 2023-06-17 | 7 | 2023-06-25 to 2023-10-22 | 3 | 120 |
| 10 | 2022-02-08 to 2023-08-01 | 7 | 2023-08-09 to 2023-12-06 | 3 | 120 |
| 11 | 2022-03-25 to 2023-09-15 | 7 | 2023-09-23 to 2024-01-20 | 3 | 120 |
| 12 | 2022-05-09 to 2023-10-30 | 7 | 2023-11-07 to 2024-03-05 | 3 | 120 |
| 13 | 2022-06-23 to 2023-12-14 | 7 | 2023-12-22 to 2024-04-19 | 3 | 120 |
| 14 | 2022-08-07 to 2024-01-28 | 7 | 2024-02-05 to 2024-06-03 | 3 | 120 |
| 15 | 2022-09-21 to 2024-03-13 | 7 | 2024-03-21 to 2024-07-18 | 3 | 120 |
| 16 | 2022-11-05 to 2024-04-27 | 7 | 2024-05-05 to 2024-09-01 | 3 | 120 |
| 17 | 2022-12-20 to 2024-06-11 | 7 | 2024-06-19 to 2024-10-16 | 3 | 120 |
| 18 | 2023-02-03 to 2024-07-26 | 7 | 2024-08-03 to 2024-11-30 | 3 | 120 |
| 19 | 2023-03-20 to 2024-09-09 | 7 | 2024-09-17 to 2025-01-14 | 3 | 120 |
| 20 | 2023-05-04 to 2024-10-24 | 7 | 2024-11-01 to 2025-02-28 | 3 | 120 |
| 21 | 2023-06-18 to 2024-12-08 | 7 | 2024-12-16 to 2025-04-14 | 3 | 120 |
| 22 | 2023-08-02 to 2025-01-22 | 7 | 2025-01-30 to 2025-05-29 | 3 | 120 |
| 23 | 2023-09-16 to 2025-03-08 | 7 | 2025-03-16 to 2025-07-13 | 3 | 120 |
| 24 | 2023-10-31 to 2025-04-22 | 7 | 2025-04-30 to 2025-08-27 | 3 | 120 |
| 25 | 2023-12-15 to 2025-06-06 | 7 | 2025-06-14 to 2025-10-11 | 3 | 120 |
| 26 | 2024-01-29 to 2025-07-21 | 7 | 2025-07-29 to 2025-11-25 | 3 | 120 |
| 27 | 2024-03-14 to 2025-09-04 | 7 | 2025-09-12 to 2026-01-09 | 3 | 120 |
| 28 | 2024-04-28 to 2025-10-19 | 7 | 2025-10-27 to 2026-02-23 | 3 | 120 |
| 29 | 2024-06-12 to 2025-12-03 | 7 | 2025-12-11 to 2026-04-09 | 3 | 120 |

## Out-of-Sample Aggregate

| Model | Folds | Mean Return | Median Return | Mean Sharpe | Worst Max DD | Return > BnH (folds) | Sharpe > BnH (folds) | Lower DD than BnH (folds) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| production_legacy_cooldown1 | 29 | +20.42% | +13.03% | 1.303 | -20.09% | 19/29 | 17/29 | 17/29 |
| legacy_cooldown3_baseline | 29 | +19.95% | +13.66% | 1.255 | -20.09% | 19/29 | 15/29 | 18/29 |
| legacy_confidence_research | 29 | +15.95% | +11.11% | 1.333 | -17.83% | 15/29 | 22/29 | 29/29 |
| advanced_adaptive_research | 29 | +3.92% | +3.33% | 1.306 | -20.23% | 14/29 | 24/29 | 29/29 |

## Walk-Forward Gate Decision

| Candidate | Evidence vs OOS Baseline | Decision |
| :--- | :--- | :--- |
| production_legacy_cooldown1 | higher_or_equal_mean_return=yes, higher_or_equal_mean_sharpe=yes, better_or_equal_worst_drawdown=yes | **IMPLEMENT WITH GUARDRAILS** |
| legacy_cooldown3_baseline | oos baseline | **KEEP (benchmark)** |
| legacy_confidence_research | higher_or_equal_mean_return=no, higher_or_equal_mean_sharpe=yes, better_or_equal_worst_drawdown=yes | **IMPLEMENT WITH GUARDRAILS** |
| advanced_adaptive_research | higher_or_equal_mean_return=no, higher_or_equal_mean_sharpe=yes, better_or_equal_worst_drawdown=no | **DO NOT IMPLEMENT** |

## Bootstrap Significance (OOS Daily Returns)

Method: `block`

| Comparison | Obs | Annualized Alpha | Alpha 95% CI | p(alpha<=0) | Delta Sharpe | Delta Sharpe 95% CI | p(delta_sharpe<=0) |
| :--- | ---: | ---: | :--- | ---: | ---: | :--- | ---: |
| production_vs_baseline | 3451 | +1.23% | [-0.21%, +2.91%] | 0.0483 | +0.027 | [-0.008, +0.068] | 0.0696 |
| production_vs_buy_and_hold | 3451 | +13.84% | [+1.28%, +27.20%] | 0.0153 | +0.603 | [+0.328, +0.895] | 0.0003 |
| legacy_confidence_research_vs_production | 3451 | -11.90% | [-19.42%, -5.18%] | 0.9993 | +0.021 | [-0.103, +0.139] | 0.3722 |
| legacy_confidence_research_vs_buy_and_hold | 3451 | +1.94% | [-14.48%, +18.92%] | 0.4159 | +0.624 | [+0.303, +0.966] | 0.0003 |
| advanced_adaptive_research_vs_production | 3451 | -46.35% | [-65.06%, -28.48%] | 1.0000 | -0.750 | [-1.240, -0.286] | 1.0000 |
| advanced_adaptive_research_vs_buy_and_hold | 3451 | -32.51% | [-55.62%, -10.55%] | 0.9963 | -0.147 | [-0.510, +0.221] | 0.7754 |

## Objective Production Gate

- Incumbent: `production_legacy_cooldown1`
- Selected live model: `production_legacy_cooldown1`
- Promotion allowed: `no`
- Selection rationale: No challenger met objective out-of-sample promotion criteria.
- Gate artifact: `data/signals/production_gate.json`

| Candidate | Delta Return vs Incumbent | Delta Sharpe | Delta Worst DD | p(alpha<=0) vs Incumbent | p(delta_sharpe<=0) vs Incumbent | p(delta_sharpe<=0) vs BnH | Decision |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| legacy_confidence_research | -4.47% | +0.030 | +2.26% | 0.9993 | 0.3722 | 0.0003 | **DO NOT PROMOTE** |
| advanced_adaptive_research | -16.50% | +0.003 | -0.14% | 1.0000 | 1.0000 | 0.7754 | **DO NOT PROMOTE** |

## Notes

- This validation is strictly out-of-sample by fold test windows.
- Purge and embargo are temporal guards to reduce leakage across adjacent windows.
- Strategy parameters are fixed; no per-fold re-optimization is performed.
- Production candidate promotion is now derived from objective OOS gate outputs.