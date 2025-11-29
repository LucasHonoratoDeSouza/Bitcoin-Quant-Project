# Quantitative Research Plan: Adaptive Z-Score Strategy

## Objective
Move from static thresholding (Curve Fitting) to adaptive statistical normalization (Z-Scores) validated by Walk-Forward Analysis.

## Phase 1: Z-Score Implementation
Instead of `if MVRV < 1.0`, we will use `if Z-Score(MVRV) < -2.0`.
This allows the strategy to adapt to changing market regimes where "cheap" might mean different absolute values over time.

### Metrics to Normalize
1. **MVRV Z-Score**: (Current MVRV - Rolling Mean MVRV) / Rolling Std Dev
2. **Price vs EMA Z-Score**: Deviation of price from long-term trend
3. **Volume Z-Score**: Detecting anomalous volume spikes

## Phase 2: Walk-Forward Validation
We will not test on the whole dataset at once. We will use a sliding window:
- **Train (Optimize):** 2 Years
- **Test (Validate):** 6 Months
- **Slide:** Move forward 6 months and repeat.

### Windows
1. Train: 2016-2018 -> Test: 2018 H1
2. Train: 2016.5-2018.5 -> Test: 2018 H2
...and so on.

## Output
A comparison report showing:
- Static Strategy Metrics (Sharpe, Drawdown, Return)
- Adaptive Z-Score Strategy Metrics
- Robustness Score (how consistent was the performance across walk-forward windows)
