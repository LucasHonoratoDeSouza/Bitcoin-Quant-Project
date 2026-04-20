# Backtest Summary

Generated on: **2026-04-20**

## Configuration
- Initial capital: `$10,000.00`
- Warm-up start date: `2018-01-01`
- Start date: `2021-01-01`
- End date: `2026-04-20`
- Trading cost: `15.00` bps per side
- Debt interest: `10.00%` annual
- Execution policy: `signal_on_close_execute_next_open`
- Advanced calibration cutoff: `2020-12-31`

## Model Comparison

| Model | Total Return | CAGR | Max Drawdown | Sharpe | Sortino | Calmar | Volatility | Trades | Avg Lev | Max Lev |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| legacy_signal + legacy_allocation(cooldown=3) | +743.41% | +49.54% | -30.29% | 1.228 | 1.765 | 1.636 | 38.88% | 102 | 0.61x | 1.00x |
| legacy_signal + legacy_allocation(cooldown=1) | +764.73% | +50.25% | -30.87% | 1.241 | 1.785 | 1.628 | 38.86% | 113 | 0.61x | 1.00x |
| advanced_signal + legacy_allocation(cooldown=3) | +58.35% | +9.06% | -32.47% | 0.590 | 0.826 | 0.279 | 17.20% | 48 | 0.31x | 0.55x |
| advanced_signal + adaptive_allocation | +44.11% | +7.14% | -34.92% | 0.469 | 0.565 | 0.204 | 18.27% | 1113 | 0.25x | 0.63x |
| legacy_signal + confidence_allocation | +539.97% | +41.95% | -24.00% | 1.298 | 1.805 | 1.748 | 30.58% | 346 | 0.45x | 0.93x |

## Buy and Hold (BTC)

| Metric | Value |
| :--- | ---: |
| Total Return | +154.73% |
| CAGR | +19.30% |
| Max Drawdown | -76.63% |
| Sharpe | 0.590 |

## Implementation Decision

| Candidate | Evidence | Decision |
| :--- | :--- | :--- |
| legacy_signal + legacy_allocation(cooldown=3) | Baseline | **KEEP (benchmark)** |
| legacy_signal + legacy_allocation(cooldown=1) | higher_return=yes, lower_drawdown=no, higher_sharpe=yes | **IMPLEMENT WITH GUARDRAILS** |
| advanced_signal + legacy_allocation(cooldown=3) | higher_return=no, lower_drawdown=no, higher_sharpe=no | **DO NOT IMPLEMENT** |
| advanced_signal + adaptive_allocation | higher_return=no, lower_drawdown=no, higher_sharpe=no | **DO NOT IMPLEMENT** |
| legacy_signal + confidence_allocation | higher_return=no, lower_drawdown=yes, higher_sharpe=yes | **IMPLEMENT WITH GUARDRAILS** |

## Notes

- This research backtest uses the same feature schema as production but includes transaction costs and debt carry.
- Use these results as a gate before changing production defaults.
- Regime stability details: `docs/backtesting-reports/subperiod_analysis.md`.
- Walk-forward + bootstrap significance: `docs/backtesting-reports/walkforward_analysis.md`.