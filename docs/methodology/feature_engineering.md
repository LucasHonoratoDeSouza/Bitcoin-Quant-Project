## Feature Engineering Methodology

This project uses a daily-feature architecture with explicit separation between:

- Slow regime variables (macro + valuation)
- Medium-horizon tactical variables (trend extension + sentiment)
- Execution controls (threshold, cooldown, debt handling)

## Canonical Daily Feature Vector

For each date $t$, the processing layer builds:

- On-chain valuation: MVRV, MVRV Z-Score, RUP, SOPR, Mayer Multiple
- Macro/liquidity: interest rate, CPI YoY, M2 YoY, dollar index change
- Sentiment/derivatives: fear-greed, funding, open interest, long-short ratio
- Market structure: price, EMA(365), extension to EMA, weekly/monthly returns
- Regime flags: cycle phase, bull trend, overheating, correlation context

## Transformations

### 1. Bounded normalization

Each raw feature is clamped to a research-defined support and mapped to $[-1, 1]$.

$$
z = 2\cdot\frac{\text{clip}(x, a, b) - a}{b-a} - 1
$$

If needed, the sign is inverted so that positive means "more bullish".

### 2. Composite blocks

Features are aggregated by economic meaning:

- Valuation block
- Macro/liquidity block
- Regime block
- Tactical block

This supports ablation backtests without rewriting execution logic.

### 3. Data consistency guards

- Missing fields are converted to neutral values (0) at scoring time.
- Score-history rows are de-duplicated by date.
- Portfolio snapshots are de-duplicated by date.

## Research Promotion Policy

A new transformation or feature is production-eligible only if it improves out-of-sample results against baseline under the same cost assumptions.