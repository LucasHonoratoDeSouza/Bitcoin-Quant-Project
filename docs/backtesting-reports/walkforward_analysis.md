# Walk-Forward Purged/Embargo Analysis

Generated on: **2026-04-19**

## Configuration
- Start date: `2020-01-01`
- Train window: `540` days
- Test window: `120` days
- Purge gap: `7` days
- Embargo gap: `3` days
- Fold step: `60` days
- Number of folds: `22`

## Fold Schedule

| Fold | Train Window | Purge | Test Window | Embargo | Test Obs |
| :--- | :--- | ---: | :--- | ---: | ---: |
| 1 | 2020-12-30 to 2022-06-22 | 7 | 2022-06-30 to 2022-10-27 | 3 | 120 |
| 2 | 2021-02-28 to 2022-08-21 | 7 | 2022-08-29 to 2022-12-26 | 3 | 120 |
| 3 | 2021-04-29 to 2022-10-20 | 7 | 2022-10-28 to 2023-02-24 | 3 | 120 |
| 4 | 2021-06-28 to 2022-12-19 | 7 | 2022-12-27 to 2023-04-25 | 3 | 120 |
| 5 | 2021-08-27 to 2023-02-17 | 7 | 2023-02-25 to 2023-06-24 | 3 | 120 |
| 6 | 2021-10-26 to 2023-04-18 | 7 | 2023-04-26 to 2023-08-23 | 3 | 120 |
| 7 | 2021-12-25 to 2023-06-17 | 7 | 2023-06-25 to 2023-10-22 | 3 | 120 |
| 8 | 2022-02-23 to 2023-08-16 | 7 | 2023-08-24 to 2023-12-21 | 3 | 120 |
| 9 | 2022-04-24 to 2023-10-15 | 7 | 2023-10-23 to 2024-02-19 | 3 | 120 |
| 10 | 2022-06-23 to 2023-12-14 | 7 | 2023-12-22 to 2024-04-19 | 3 | 120 |
| 11 | 2022-08-22 to 2024-02-12 | 7 | 2024-02-20 to 2024-06-18 | 3 | 120 |
| 12 | 2022-10-21 to 2024-04-12 | 7 | 2024-04-20 to 2024-08-17 | 3 | 120 |
| 13 | 2022-12-20 to 2024-06-11 | 7 | 2024-06-19 to 2024-10-16 | 3 | 120 |
| 14 | 2023-02-18 to 2024-08-10 | 7 | 2024-08-18 to 2024-12-15 | 3 | 120 |
| 15 | 2023-04-19 to 2024-10-09 | 7 | 2024-10-17 to 2025-02-13 | 3 | 120 |
| 16 | 2023-06-18 to 2024-12-08 | 7 | 2024-12-16 to 2025-04-14 | 3 | 120 |
| 17 | 2023-08-17 to 2025-02-06 | 7 | 2025-02-14 to 2025-06-13 | 3 | 120 |
| 18 | 2023-10-16 to 2025-04-07 | 7 | 2025-04-15 to 2025-08-12 | 3 | 120 |
| 19 | 2023-12-15 to 2025-06-06 | 7 | 2025-06-14 to 2025-10-11 | 3 | 120 |
| 20 | 2024-02-13 to 2025-08-05 | 7 | 2025-08-13 to 2025-12-10 | 3 | 120 |
| 21 | 2024-04-13 to 2025-10-04 | 7 | 2025-10-12 to 2026-02-08 | 3 | 120 |
| 22 | 2024-06-12 to 2025-12-03 | 7 | 2025-12-11 to 2026-04-09 | 3 | 120 |

## Out-of-Sample Aggregate

| Model | Folds | Mean Return | Median Return | Mean Sharpe | Worst Max DD | Return > BnH (folds) | Sharpe > BnH (folds) | Lower DD than BnH (folds) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| production_legacy_cooldown1 | 22 | +20.31% | +18.72% | 1.342 | -20.09% | 11/22 | 13/22 | 14/22 |
| legacy_cooldown3_baseline | 22 | +20.31% | +19.04% | 1.323 | -20.09% | 11/22 | 14/22 | 14/22 |
| legacy_confidence_research | 22 | +20.28% | +18.61% | 1.338 | -20.04% | 13/22 | 13/22 | 20/22 |
| advanced_adaptive_research | 22 | +9.44% | +5.33% | 1.015 | -22.73% | 9/22 | 19/22 | 22/22 |

## Walk-Forward Gate Decision

| Candidate | Evidence vs OOS Baseline | Decision |
| :--- | :--- | :--- |
| production_legacy_cooldown1 | higher_or_equal_mean_return=yes, higher_or_equal_mean_sharpe=yes, better_or_equal_worst_drawdown=yes | **IMPLEMENT WITH GUARDRAILS** |
| legacy_cooldown3_baseline | oos baseline | **KEEP (benchmark)** |
| legacy_confidence_research | higher_or_equal_mean_return=yes, higher_or_equal_mean_sharpe=yes, better_or_equal_worst_drawdown=yes | **IMPLEMENT WITH GUARDRAILS** |
| advanced_adaptive_research | higher_or_equal_mean_return=no, higher_or_equal_mean_sharpe=no, better_or_equal_worst_drawdown=no | **DO NOT IMPLEMENT** |

## Bootstrap Significance (OOS Daily Returns)

| Comparison | Obs | Annualized Alpha | Alpha 95% CI | p(alpha<=0) | Delta Sharpe | Delta Sharpe 95% CI | p(delta_sharpe<=0) |
| :--- | ---: | ---: | :--- | ---: | ---: | :--- | ---: |
| production_vs_baseline | 2618 | +0.05% | [-1.51%, +1.55%] | 0.4805 | -0.002 | [-0.046, +0.040] | 0.5322 |
| production_vs_buy_and_hold | 2618 | +13.26% | [-2.59%, +29.82%] | 0.0510 | +0.607 | [+0.283, +0.941] | 0.0010 |
| confidence_vs_production | 2618 | -0.11% | [-0.49%, +0.29%] | 0.7044 | +0.003 | [-0.007, +0.013] | 0.2986 |

## Notes

- This validation is strictly out-of-sample by fold test windows.
- Purge and embargo are temporal guards to reduce leakage across adjacent windows.
- Strategy parameters are fixed; no per-fold re-optimization is performed.