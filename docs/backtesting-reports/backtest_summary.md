# Backtest Summary

Generated on: **2026-04-19**

## Configuration
- Initial capital: `$10,000.00`
- Start date: `2021-01-01`
- Trading cost: `15.00` bps per side
- Debt interest: `10.00%` annual

## Model Comparison

| Model | Total Return | CAGR | Max Drawdown | Sharpe | Sortino | Calmar | Volatility | Trades | Avg Lev | Max Lev |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| legacy_signal + legacy_allocation(cooldown=3) | +438.63% | +47.95% | -27.32% | 1.271 | 1.898 | 1.755 | 35.85% | 69 | 0.65x | 1.00x |
| legacy_signal + legacy_allocation(cooldown=1) | +439.54% | +48.01% | -29.12% | 1.272 | 1.895 | 1.648 | 35.85% | 78 | 0.64x | 1.00x |
| advanced_signal + legacy_allocation(cooldown=3) | +59.99% | +11.55% | -66.97% | 0.470 | 0.665 | 0.172 | 51.96% | 2 | 1.00x | 1.01x |
| advanced_signal + adaptive_allocation | +101.38% | +17.69% | -28.68% | 0.773 | 1.161 | 0.617 | 25.16% | 809 | 0.50x | 0.73x |
| legacy_signal + confidence_allocation | +437.13% | +47.86% | -28.03% | 1.277 | 1.902 | 1.707 | 35.53% | 94 | 0.63x | 1.06x |

## Buy and Hold (BTC)

| Metric | Value |
| :--- | ---: |
| Total Return | +63.53% |
| CAGR | +12.12% |
| Max Drawdown | -66.89% |
| Sharpe | 0.480 |

## Implementation Decision

| Candidate | Evidence | Decision |
| :--- | :--- | :--- |
| legacy_signal + legacy_allocation(cooldown=3) | Baseline | **KEEP (benchmark)** |
| legacy_signal + legacy_allocation(cooldown=1) | higher_return=yes, lower_drawdown=no, higher_sharpe=yes | **IMPLEMENT WITH GUARDRAILS** |
| advanced_signal + legacy_allocation(cooldown=3) | higher_return=no, lower_drawdown=no, higher_sharpe=no | **DO NOT IMPLEMENT** |
| advanced_signal + adaptive_allocation | higher_return=no, lower_drawdown=no, higher_sharpe=no | **DO NOT IMPLEMENT** |
| legacy_signal + confidence_allocation | higher_return=no, lower_drawdown=no, higher_sharpe=yes | **DO NOT IMPLEMENT** |

## Notes

- This research backtest uses the same feature schema as production but includes transaction costs and debt carry.
- Use these results as a gate before changing production defaults.
- Regime stability details: `docs/backtesting-reports/subperiod_analysis.md`.
- Walk-forward + bootstrap significance: `docs/backtesting-reports/walkforward_analysis.md`.

## Walk-Forward Cross-Check (Purged + Embargo)

Configuration used on 2026-04-19:

- Train window: 540 days
- Test window: 120 days
- Purge: 7 days
- Embargo: 3 days
- Fold step: 60 days
- Folds: 22

| Model | Mean OOS Return | Mean OOS Sharpe | Worst Max DD |
| :--- | ---: | ---: | ---: |
| production_legacy_cooldown1 | +20.31% | 1.342 | -20.09% |
| legacy_cooldown3_baseline | +20.31% | 1.323 | -20.09% |
| legacy_confidence_research | +20.28% | 1.338 | -20.04% |
| advanced_adaptive_research | +9.44% | 1.015 | -22.73% |