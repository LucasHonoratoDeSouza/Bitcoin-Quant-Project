## Derivatives Signals

Derivatives features are used primarily as crowding and liquidation-risk indicators.

## 1. Open Interest (OI)

$$
OI_t = \text{Total open futures contracts at time } t
$$

- High OI after strong upside often implies crowded leverage.
- Low OI implies cleaner positioning and lower cascade risk.

## 2. Long/Short Ratio (LSR)

$$
LSR_t = \frac{\text{Long accounts}}{\text{Short accounts}}
$$

- High LSR can indicate one-sided longs and liquidation vulnerability.
- Low LSR can indicate squeeze potential if price reverses upward.

## 3. Funding Rate and Basis

Funding rate and futures basis are used as overheat diagnostics:

$$
\text{Basis}_t = \frac{F_t - S_t}{S_t}
$$

- Very positive funding/basis: leverage-heavy bullish crowding.
- Negative basis: stress regime, potentially attractive only with supportive valuation.

## Data Quality Note

Derivatives APIs can intermittently return null fields. The pipeline stores missing values explicitly so risk logic can default to neutral/defensive behavior rather than silently failing.
