## Core Strategy Rules (Production)

As of 2026-04-19, production runs with:

- Scorer mode: `legacy`
- Allocation engine: `PortfolioManager`
- Cooldown: `1 day`

This configuration passed the latest model-comparison gate.

## Signal Dimensions

The strategy consumes two normalized signals in $[-100, 100]$:

- Long-term score (LT): valuation/macro/cycle bias
- Medium-term score (MT): tactical/trend pullback bias

## Core Actions

1. Super Bull
- Condition: `LT > 75` and `MT > 50`
- Action: increase target exposure above 100% (up to leverage cap)

2. Strong Buy
- Condition: `LT > 40` and `MT > 0`
- Action: target 100% BTC allocation

3. Extreme Bear
- Condition: `LT < -60`
- Action: move to 0% BTC

4. Bear Market Defense
- Condition: `-60 <= LT < -40`
- Action: hold moonbag floor (~10%)

5. Accumulation
- Condition: `LT > 20` and `MT < -20`
- Action: dynamic add based on dip intensity

6. Sell Rally
- Condition: `LT < 20` and `MT > 20`
- Action: trim based on MT heat, respecting floor

7. Neutral Baseline
- Condition: none of the above
- Action: maintain at least baseline BTC allocation

## Execution Filters

- Trade threshold: skip small rebalances below dynamic threshold.
- Cooldown: non-urgent signals obey cooldown window.
- Debt and repayment are tracked in accounting at execution time.

## Research Modes (Not Default)

- `advanced`: probabilistic regime-aware scoring
- `blend`: weighted mix of legacy and advanced scores

These modes remain available but are not promoted until they beat baseline out-of-sample.