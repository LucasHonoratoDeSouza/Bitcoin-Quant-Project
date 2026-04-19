## Risk Limits

## Portfolio-Level Limits

1. Dynamic trade threshold
- Prevents micro-rebalances and unnecessary turnover.

2. Cooldown window
- Blocks frequent regime-flip trades when signal urgency is low.

3. Bear-market floors and exits
- Moonbag floor in defensive state.
- Full exit in extreme-bear state.

4. Debt control
- Borrowing only under specific high-conviction conditions.
- Automatic debt repayment on subsequent sells.

## Monitoring Metrics

The following metrics are tracked in backtest and should be monitored in paper trading:

- Total return
- CAGR
- Max drawdown
- Sharpe and Sortino
- Turnover and number of trades
- Average and maximum leverage

## Promotion Rule

A candidate strategy must improve at least two of these dimensions versus baseline:

1. Return
2. Drawdown
3. Sharpe

Otherwise, it remains in research mode.