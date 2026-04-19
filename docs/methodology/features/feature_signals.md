## Feature Signals

This document summarizes the economic meaning of the project features.

## On-Chain Valuation

1. RUP (Relative Unrealized Profit)
- Proxy for unrealized profit pressure in the network.
- High RUP suggests euphoria/distribution risk.
- Low RUP suggests accumulation potential.

2. MVRV
- $\text{MVRV} = \frac{\text{Market Cap}}{\text{Realized Cap}}$
- High levels imply overvaluation risk.
- Low levels imply valuation support for long-horizon entries.

3. MVRV Z-Score
- Standardizes MVRV relative to long-term distribution.
- Used as a regime-aware valuation anchor in scoring.

4. SOPR
- $\text{SOPR} = \frac{\text{Value at Spend}}{\text{Value at Creation}}$
- Below 1 historically aligns with capitulation environments.

5. Mayer Multiple
- $\text{MM} = \frac{P_t}{\text{MA}_{200}(P)}$
- Tracks overextension versus long-term trend.

## Price Structure

6. EMA Context
- Compare spot to EMA(365).
- Positive slope + price above EMA supports trend continuation.
- Large positive extension increases pullback risk.

7. Extension to EMA
- $\frac{P_t - \text{EMA}_{365}}{\text{EMA}_{365}}$
- Used for tactical mean-reversion and trend-exhaustion checks.

## Macro Liquidity

8. Interest Rate (FEDFUNDS)
- Rising rates usually tighten liquidity conditions.

9. M2 YoY
- Higher M2 growth tends to support risk assets.

10. Inflation YoY (CPI)
- Inflation + policy dynamics help classify macro risk regime.

11. Dollar Strength (DXY broad index)
- Strengthening dollar usually pressures global liquidity-sensitive assets.

## Practical Note

Features are not traded individually; they are transformed and aggregated inside scoring blocks and validated via model-comparison backtests.