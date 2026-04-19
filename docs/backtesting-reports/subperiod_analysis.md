# Subperiod Stability Analysis

Generated on: **2026-04-19**

This report evaluates model behavior across different BTC market regimes.

## Bull 2021 (2021-01-01 to 2021-11-10)

| Model | Total Return | CAGR | Max Drawdown | Sharpe | Trades |
| :--- | ---: | ---: | ---: | ---: | ---: |
| buy_and_hold | +121.27% | +152.48% | -53.06% | 1.529 | 0 |
| production_legacy_cooldown1 | +65.61% | +80.09% | -30.90% | 1.366 | 32 |
| legacy_cooldown3_baseline | +60.86% | +74.08% | -30.61% | 1.300 | 28 |
| advanced_adaptive_research | +62.16% | +75.73% | -30.76% | 1.477 | 212 |
| legacy_confidence_research | +66.27% | +80.93% | -30.52% | 1.375 | 37 |

## Bear 2021-2022 (2021-11-11 to 2022-11-21)

| Model | Total Return | CAGR | Max Drawdown | Sharpe | Trades |
| :--- | ---: | ---: | ---: | ---: | ---: |
| buy_and_hold | -75.69% | -74.76% | -75.89% | -1.759 | 0 |
| production_legacy_cooldown1 | -29.99% | -29.32% | -30.03% | -1.689 | 25 |
| legacy_cooldown3_baseline | -27.80% | -27.17% | -27.84% | -1.567 | 23 |
| advanced_adaptive_research | -39.55% | -38.73% | -39.77% | -1.850 | 189 |
| legacy_confidence_research | -28.74% | -28.10% | -28.78% | -1.679 | 32 |

## Recovery 2022-2024 (2022-11-22 to 2024-04-19)

| Model | Total Return | CAGR | Max Drawdown | Sharpe | Trades |
| :--- | ---: | ---: | ---: | ---: | ---: |
| buy_and_hold | +294.35% | +164.94% | -20.06% | 2.306 | 0 |
| production_legacy_cooldown1 | +286.79% | +161.32% | -20.06% | 2.278 | 6 |
| legacy_cooldown3_baseline | +282.84% | +159.42% | -20.06% | 2.269 | 6 |
| advanced_adaptive_research | +110.72% | +69.77% | -12.92% | 2.247 | 254 |
| legacy_confidence_research | +283.87% | +159.92% | -19.94% | 2.278 | 7 |

## Post-Halving 2024-2026 (2024-04-20 to 2026-04-19)

| Model | Total Return | CAGR | Max Drawdown | Sharpe | Trades |
| :--- | ---: | ---: | ---: | ---: | ---: |
| buy_and_hold | +16.51% | +7.96% | -49.74% | 0.397 | 0 |
| production_legacy_cooldown1 | +81.97% | +35.01% | -18.01% | 1.107 | 58 |
| legacy_cooldown3_baseline | +78.19% | +33.59% | -17.97% | 1.070 | 52 |
| advanced_adaptive_research | +27.19% | +12.82% | -26.04% | 0.588 | 399 |
| legacy_confidence_research | +81.15% | +34.70% | -17.93% | 1.103 | 69 |

## Robustness Summary

- Production model beat Buy & Hold in **return** on 2/4 subperiods.
- Production model beat Buy & Hold in **Sharpe** on 2/4 subperiods.
- Production model had **lower drawdown** on 3/4 subperiods.