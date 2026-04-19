## Leverage Policy

Leverage is only allowed in high-conviction bullish states.

## Trigger

- Condition: `LT > 75` and `MT > 50`
- Action: increase target exposure above 1.0 (100%) up to configured cap

## Debt Accounting

When buy notional exceeds cash balance:

1. Borrow the shortfall.
2. Add borrowed amount to debt.
3. Charge daily debt interest.

Debt is repaid automatically when sells generate cash.

## Risk Constraints

- No leverage in bearish/neutral conditions.
- No forced borrowing if signal does not require it.
- Extreme bear regime (`LT < -60`) targets full de-risking to 0% BTC.

## Research Guardrail

Any leverage-policy modification requires backtest comparison including:

- transaction costs
- debt carry
- drawdown impact

Changes that only improve return but materially worsen drawdown are not promoted by default.