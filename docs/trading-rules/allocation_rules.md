## Allocation Rules

The allocation layer maps signal state to a target BTC exposure.

## Capital Components

- Cash (USD)
- BTC market value
- Debt (borrowed capital when target exposure exceeds available cash)

Net equity:

$$
\text{Equity}_t = \text{Cash}_t + \text{BTCValue}_t - \text{Debt}_t
$$

Current BTC allocation:

$$
w_t = \frac{\text{BTCValue}_t}{\text{Equity}_t}
$$

## Target Exposure Regime Map

1. Super Bull: up to leveraged target
2. Strong Buy: 100% BTC
3. Extreme Bear: 0% BTC
4. Bear Defense: moonbag floor
5. Accumulate: add proportionally to dip intensity
6. Sell Rally: reduce proportionally to heat intensity
7. Neutral: maintain baseline exposure

## Rebalance Mechanics

Target BTC value:

$$
\text{TargetBTCValue}_t = \text{Equity}_t \cdot w_t^{\*}
$$

Required trade notional:

$$
\Delta_t = \text{TargetBTCValue}_t - \text{BTCValue}_t
$$

Trade is skipped if $|\Delta_t|$ is below dynamic threshold.

## Cooldown

Non-urgent signals must respect cooldown to reduce overtrading.

Production setting after latest gate: `cooldown_days=1`.
