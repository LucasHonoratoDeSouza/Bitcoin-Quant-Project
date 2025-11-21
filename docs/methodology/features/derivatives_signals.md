1. Open Interest (OI)

Definition:
OI_t = total number of open long + short futures contracts at time t.

Normalized (z-score):
OI_z = (OI_t - mean(OI)) / std(OI)

Effect:

High OI_z → high leverage → higher liquidation risk.

Low OI_z → clean market → safer trend entries.


2. Long/Short Ratio (LSR)

Definition:
LSR = Longs / Shorts

Effect:

LSR >> 1 → long-side overcrowding → downside liquidation risk.

LSR << 1 → short-side overcrowding → short squeeze potential.

3. Derivatives Basis

Definition:
Basis = (FuturesPrice_t - SpotPrice_t) / SpotPrice_t

Annualized:
BasisAnnualized = Basis * (365 / DaysToExpiry)

Effect:

High positive basis → leveraged optimism → reduces long conviction.

Negative basis → backwardation/stress → possible accumulation zones.