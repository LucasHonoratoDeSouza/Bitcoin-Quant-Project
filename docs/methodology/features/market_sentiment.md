## Market Sentiment

Market sentiment captures crowd risk appetite and positioning extremes.

## Current Production Proxy

The production stack currently uses Fear & Greed as the main sentiment observable.

- High values: elevated optimism, often associated with crowded long positioning.
- Low values: fear/capitulation context, useful for accumulation logic when other factors align.

## Research Extensions

Future sentiment expansion can include:

- news polarity embeddings
- social sentiment dispersion
- options skew / implied-volatility term structure

## Trading Interpretation

Sentiment is used as a **conditioning variable**, not a standalone trigger.

- Extreme greed usually reduces marginal long conviction.
- Extreme fear can improve risk/reward only when macro/valuation are supportive.