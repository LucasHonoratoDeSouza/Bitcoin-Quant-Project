# Bitcoin Quant Project

Systematic Bitcoin allocation pipeline with forward testing first, honest backtesting, and auditable quantitative governance.

## 1) Forward Test Results

<!-- live-stats:start -->
## Forward Testing Snapshot
*Forward testing since Nov 23, 2025. Auto-updated by daily pipeline.*
*Benchmark: Alpha vs BTC = strategy ROI minus BTC buy-and-hold ROI over the same period.*

| Metric | Value | Description |
| :--- | :--- | :--- |
| **Initial Capital** | `$2,000.00` | Starting Equity (Cash + BTC) |
| **Current Equity** | `$1,936.78` | Updated from the latest paper trading snapshot |
| **Alpha vs BTC** | `+7.26%` | Strategy ROI minus BTC buy-and-hold ROI over the same forward-testing window |
| **Net Profit** | `$-63.22` | **-3.16%** |
| **Avg. Monthly Return** | `-0.63%` | Projected (30-day) |
| **Win Rate** | `0.0%` | 1 trades executed |

> **Status**: Active | Drawdown
<!-- live-stats:end -->

## 2) Backtest Results

Backtest version currently in use is the honest configuration:

- signal generated on close of day t
- execution at open of day t+1
- cost-aware accounting (transaction cost + debt carry)
- advanced scorer calibration cutoff before test start (no future leakage)

Latest run metadata:

- generated on: 2026-04-20
- warm-up start: 2018-01-01
- backtest start: 2021-01-01
- backtest end: 2026-04-20
- trading cost: 15 bps per side
- debt interest: 10% annual

### 2.1 Backtest Model Comparison

| Model | Total Return | CAGR | Max Drawdown | Sharpe | Sortino | Calmar | Volatility | Trades | Avg Lev | Max Lev |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| legacy_signal + legacy_allocation(cooldown=3) | +743.41% | +49.54% | -30.29% | 1.228 | 1.765 | 1.636 | 38.88% | 102 | 0.61x | 1.00x |
| legacy_signal + legacy_allocation(cooldown=1) | +764.73% | +50.25% | -30.87% | 1.241 | 1.785 | 1.628 | 38.86% | 113 | 0.61x | 1.00x |
| advanced_signal + legacy_allocation(cooldown=3) | +58.35% | +9.06% | -32.47% | 0.590 | 0.826 | 0.279 | 17.20% | 48 | 0.31x | 0.55x |
| advanced_signal + adaptive_allocation | +44.11% | +7.14% | -34.92% | 0.469 | 0.565 | 0.204 | 18.27% | 1113 | 0.25x | 0.63x |
| legacy_signal + confidence_allocation | +539.97% | +41.95% | -24.00% | 1.298 | 1.805 | 1.748 | 30.58% | 346 | 0.45x | 0.93x |

### 2.2 Buy and Hold Benchmark

| Metric | Value |
| :--- | ---: |
| Total Return | +154.73% |
| CAGR | +19.30% |
| Max Drawdown | -76.63% |
| Sharpe | 0.590 |

References:

- `docs/backtesting-reports/walkforward_analysis.md`
- `docs/backtesting-reports/backtest_summary.md`
- `tests/backtest/model_comparison.csv`
- `tests/backtest/walkforward_results.csv`

## 3) Technical Presentation (English)

This section is the English version of the technical presentation currently maintained in `apresentação.md`.

### 3.1 System Objective

The engine targets long-horizon BTC allocation with:

- long-run BTC and USD capital growth;
- drawdown control via dynamic allocation rules;
- reproducible and auditable decision logic;
- production promotion only with objective out-of-sample evidence.

Main operational metric:

$$
\alpha_{BTC} = ROI_{strategy} - ROI_{buy\&hold}
$$

### 3.2 Functional Architecture

Pipeline layers:

1. Data ingestion: price, on-chain, macro, sentiment, derivatives.
2. Feature processing: normalization, market regime flags.
3. Quant scoring: Long Term (LT) and Medium Term (MT) signals.
4. Signal-to-order translation via allocation engines.
5. Cost-aware execution simulation.
6. Accounting and reporting.
7. Production governance gate from OOS validation.

Core files:

- `src/strategy/score.py`
- `src/strategy/legacy_score.py`
- `src/strategy/process_data.py`
- `src/execution/portfolio_manager.py`
- `src/execution/confidence_portfolio_manager.py`
- `src/execution/advanced_portfolio_manager.py`
- `src/execution/accounting.py`
- `src/execution/production_gate.py`
- `src/main_paper_trading.py`

### 3.3 Daily Production Flow

Execution sequence:

1. `download`
2. `process`
3. `paper`

The paper trading run:

- resolves active model from `data/signals/production_gate.json`;
- instantiates scorer and allocation engine;
- computes LT/MT and decides `BUY`, `SELL`, or no action;
- applies accounting with debt carry and updates reports.

Safe fallback if gate file is missing/invalid:

- `production_legacy_cooldown1`

### 3.4 Quantitative Signal Block

#### 3.4.1 QuantScorer(mode="quant")

Main mathematical components:

1. Robust normalization with historical median/MAD.
2. Evidence blocks (valuation, macro, trend, volatility) weighted by data reliability.
3. Bayesian-style regime posterior (cycle prior + likelihood from blocks).
4. Explicit uncertainty penalty before final edge scoring.

Robust feature normalization:

$$
z_i^{rob} = \frac{x_i - median_i}{1.4826 \cdot MAD_i}
$$

Regime posterior:

$$
p_{bull} = \sigma\left(logit_{prior}(cycle) + logit_{likelihood}(valuation, macro, trend, flags)\right)
$$

Uncertainty penalty:

$$
U = 0.45\,H(p_{bull}) + 0.35\,dispersion(signals) + 0.20\,(1-coverage)
$$

Final LT score:

$$
Score_{LT} = 100 \cdot \tanh\left(1.55 \cdot (Edge - 0.35U - 0.20\,VolPressure)\right)
$$

Final MT score:

$$
Score_{MT} = 100 \cdot clip\left(Base_{MT} \cdot (0.60 + 0.50\,Confidence), -1, 1\right)
$$

#### 3.4.2 LegacyQuantScorer Baseline

The legacy baseline remains available for A/B comparison and promotion governance.

General form:

$$
Score_{LT} = 100 \cdot (w_1 \cdot OnChain + w_2 \cdot Cycle + w_3 \cdot Macro)
$$

$$
Score_{MT} = 100 \cdot (v_1 \cdot Trend + v_2 \cdot Sentiment + v_3 \cdot Extension + v_4 \cdot Seasonality)
$$

### 3.5 Allocation Engines

#### 3.5.1 PortfolioManager

Converts LT/MT into target allocation with hysteresis and cooldown controls.

Main behaviors:

- super-bull: can scale up to 2x leverage;
- strong-buy: 100% BTC target;
- defensive-bear: 10% moonbag floor;
- extreme-bear: full exit.

#### 3.5.2 ConfidencePortfolioManager

Research allocation engine with:

- confidence-weighted LT/MT blending;
- regime-dependent risk budget;
- adaptive threshold and cooldown by confidence.

Simplified notation:

$$
Target_{adj} = Current + \gamma(Confidence, RiskBudget) \cdot (Target_{raw} \cdot RiskBudget - Current)
$$

### 3.6 Simulator and Accounting

`PortfolioSimulator` models:

- transaction costs in bps;
- debt financing with daily carry;
- trade-to-equity accounting impacts;
- daily equity path and risk metrics.

Reported metrics include:

- total return, CAGR, max drawdown;
- Sharpe, Sortino, Calmar;
- annualized volatility;
- turnover, trades/year, average and max leverage.

### 3.7 Production Promotion Governance

Promotion is objective-driven via:

- purged+embargo walk-forward validation;
- minimum fold coverage;
- bootstrap significance checks on OOS daily returns;
- gate artifact at `data/signals/production_gate.json`.

### 3.8 Stochastic Validation Layer

Main module:

- `tests/backtest/stochastic_calculus_validation.py`

#### 3.8.1 Stochastic Model

Regime-switching jump-diffusion:

$$
dS_t = \mu_{r_t} S_t dt + \sigma_{r_t} S_t dW_t + S_t (e^{J_t} - 1) dN_t
$$

with:

- Markov regime process $r_t$;
- Brownian diffusion $W_t$;
- Poisson jump arrivals $N_t$;
- Gaussian jump sizes $J_t$.

#### 3.8.2 End-to-End Monte Carlo Validation

For each path:

1. reconstruct synthetic feature tensors;
2. recompute scores;
3. rerun allocation engines;
4. collect return and risk distributions by model.

#### 3.8.3 Generated Visual Outputs

- `reports/stochastic/figures/stochastic_fan_chart.html`
- `reports/stochastic/figures/stochastic_heston_fan_chart.html`
- `reports/stochastic/figures/stochastic_surface_3d.html`
- `reports/stochastic/figures/stochastic_scatter_3d.html`
- `reports/stochastic/figures/regime_transition_heatmap.html`
- `docs/backtesting-reports/stochastic_validation.md`

#### 3.8.4 Quantitative Summary (Latest)

Regime jump scenario (220 paths):

| Model | Mean Return | VaR 95% | CVaR 95% | Mean Max DD | P(Beat BnH) |
| :--- | ---: | ---: | ---: | ---: | ---: |
| production_legacy_cooldown1 | +2.87% | -19.39% | -25.47% | -11.94% | 56.82% |
| legacy_cooldown3_baseline | +2.96% | -16.24% | -22.57% | -11.33% | 55.91% |
| legacy_confidence_research | +1.53% | -8.56% | -11.31% | -6.18% | 53.18% |
| advanced_adaptive_research | +2.10% | -13.95% | -20.36% | -9.25% | 54.09% |

Heston jump scenario (140 paths):

| Model | Mean Return | VaR 95% | CVaR 95% | Mean Max DD | P(Beat BnH) | Bayesian 95% CI |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| production_legacy_cooldown1 | +4.23% | -22.21% | -27.66% | -11.47% | 47.14% | [39.03%, 55.40%] |
| legacy_cooldown3_baseline | +4.52% | -22.40% | -25.57% | -11.01% | 45.00% | [37.02%, 53.35%] |
| legacy_confidence_research | +2.33% | -10.30% | -12.82% | -5.91% | 41.43% | [33.61%, 49.74%] |
| advanced_adaptive_research | +2.43% | -21.37% | -27.92% | -9.24% | 46.43% | [38.38%, 54.64%] |

#### 3.8.5 Multiple-Testing Control

The stochastic layer includes White Reality Check-style bootstrap tests and Holm correction.

Latest interpretation:

- no model rejected $H_0: \alpha \le 0$ at 5% after Holm correction.

#### 3.8.6 Factor Attribution

Cross-sectional attribution includes:

- valuation, macro, trend, regime,
- uncertainty, momentum, reversion, risk.

Latest highlight for `advanced_adaptive_research`:

- top risk contributor in both scenarios: `reversion_mean`
- second contributor: `trend_mean`

### 3.9 Quantitative Interpretation Guide

Practical reading rules:

1. High mean return with very negative CVaR means heavy left-tail risk.
2. $P(Beat\ BnH) > 50\%$ indicates probabilistic dominance, not certainty.
3. 3D surfaces reveal sensitivity to drift and volatility assumptions.
4. 3D scatter identifies favorable vs hostile risk-regime clusters.

### 3.10 Limitations and Cautions

- Synthetic feature reconstruction preserves macro structure, not full market microstructure.
- Gaussian jumps still understate real extreme-tail behavior.
- Stochastic evidence complements, but does not replace, strict OOS and live forward testing.

### 3.11 Quantitative Roadmap

Completed in this iteration:

1. Heston-style stochastic-volatility scenario with jumps. [OK]
2. Multiple-testing control (White RC + Holm). [OK]
3. Bayesian credible intervals for outperform probability. [OK]
4. Factor attribution by score component. [OK]

Next steps:

1. explicit HMM latent-state inference layer;
2. dedicated GARCH volatility forecast layer;
3. full SPA/White family expansion in daily walk-forward governance.

### 3.12 Reproduction Commands

```bash
make backtest
make backtest-subperiod
make backtest-walkforward
make backtest-robustness
make backtest-stochastic
```

Direct stochastic run:

```bash
python tests/backtest/stochastic_calculus_validation.py
```

### 3.13 Conclusion

The current system combines:

- robust quantitative inference,
- statistical governance for production promotion,
- honest historical OOS validation,
- and multi-regime stochastic stress testing with advanced visualization.

This turns the strategy from heuristic rules into a disciplined, auditable, and reproducible quantitative process.
