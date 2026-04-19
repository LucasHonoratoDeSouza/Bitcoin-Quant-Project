## Data Sources

## On-Chain (ChainExposed via `chaindl`)

- Relative Unrealized Profit (RUP)
- MVRV
- SOPR
- Mayer Multiple
- MVRV Crosses

## Market Price

- BTC spot/series: CoinGecko and Yahoo Finance (`yfinance`)

## Macro (FRED)

- FEDFUNDS (interest rate)
- CPIAUCSL (inflation)
- M2SL (money supply)
- DTWEXBGS (broad dollar index)

Requires `FRED_API_KEY` in `.env`.

## Derivatives

- Binance Futures API (`BTCUSDT`): open interest, long/short ratio, funding, basis proxy

## Sentiment

- Alternative.me Fear & Greed API

## Correlation Context

- Yahoo Finance (`BTC-USD`, `^GSPC`, `GC=F`) for rolling cross-asset correlation.

## Reliability Notes

- Each fetcher failure is recorded in raw snapshot metadata.
- Missing values are persisted as `null` and handled downstream.
- Strict mode can fail the pipeline if any source is unavailable.