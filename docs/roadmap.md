## Quant Roadmap (Research-First)

This roadmap defines how new ideas move from hypothesis to production.

### Phase 1 - Data Reliability (Completed)

- Daily ingestion for price, on-chain, macro, sentiment, and derivatives.
- Processed feature snapshots persisted in `data/processed/`.
- Paper trading + accounting + report generation in place.

### Phase 2 - Scientific Validation (Completed on 2026-04-19)

- Added model-comparison backtest harness with explicit implementation gates.
- Included transaction costs and debt carry in simulation.
- Added baseline vs candidate comparison and objective go/no-go outputs.
- Added regime-by-regime subperiod robustness analysis (Bull, Bear, Recovery, Post-Halving).
- Added purged/embargo walk-forward validation layer for out-of-sample stability checks.

### Phase 3 - Production Hardening (In Progress)

- Keep only strategies that beat baseline out-of-sample.
- Enforce one canonical daily snapshot and score row per date.
- Keep advanced models available in research mode, not default.

### Phase 4 - Quant Expansion (In Progress)

Completed on 2026-04-20:

- Added Heston-style stochastic-volatility scenario with jumps in stochastic validation.
- Added multiple-testing control in stochastic block using White Reality Check-style bootstrap with Holm-Bonferroni correction.
- Added Bayesian credible intervals for outperform probability vs Buy and Hold.
- Added factor attribution output (valuation/macro/trend/regime/uncertainty/momentum/reversion/risk) for alpha/risk decomposition.

Remaining backlog:

- Add explicit HMM latent-state filtering for production-time regime inference.
- Add dedicated GARCH-family volatility forecast layer for online position sizing.
- Extend multiple-testing controls to full walk-forward model families with SPA/White at daily-return level.

### Operating Rule

No feature, signal, or execution rule is promoted to production unless it:

1. Improves at least two of: return, drawdown, Sharpe.
2. Remains robust under transaction-cost assumptions.
3. Is documented and reproducible from code + saved artifacts.
