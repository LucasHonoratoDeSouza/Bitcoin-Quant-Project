# Bitcoin Quant Project

Systematic Bitcoin allocation pipeline with daily forward testing, cost-aware research backtests, and auditable accounting.

## Forward Testing First

This repository is operated with forward testing as the primary source of truth.

- Objective: maximize long-horizon BTC yield through systematic allocation.
- Current mode: paper trading with real daily data flow.
- Benchmark: Alpha vs BTC (strategy ROI minus BTC buy-and-hold ROI over the same period).

The section below is updated automatically by the daily pipeline.

<!-- live-stats:start -->
## Forward Testing Snapshot
*Forward testing since Nov 23, 2025. Auto-updated by daily pipeline.*
*Benchmark: Alpha vs BTC = strategy ROI minus BTC buy-and-hold ROI over the same period.*

| Metric | Value | Description |
| :--- | :--- | :--- |
| **Initial Capital** | `$2,000.00` | Starting Equity (Cash + BTC) |
| **Current Equity** | `$1,921.96` | Updated from the latest paper trading snapshot |
| **Alpha vs BTC** | `+8.59%` | Strategy ROI minus BTC buy-and-hold ROI over the same forward-testing window |
| **Net Profit** | `$-78.04` | **-3.90%** |
| **Avg. Monthly Return** | `-0.81%` | Projected (30-day) |
| **Win Rate** | `0.0%` | 0 trades executed |

> **Status**: Active | Drawdown
<!-- live-stats:end -->

## Current Production Configuration

As of 2026-04-19:

- Scoring mode: `QuantScorer(mode="legacy")`
- Allocation engine: `PortfolioManager`
- Cooldown: `1 day`
- Rationale: passed primary model gate under cost-aware out-of-sample comparison

Implementation reference:

- `legacy_signal + legacy_allocation(cooldown=1)` -> implement with guardrails

## Validation Stack

Forward testing is primary. Backtests are used as secondary evidence for model promotion.

### 1. Cost-Aware Model Comparison

- Includes transaction costs and debt carry.
- Latest primary result summary:
  - Buy and Hold total return: +63.53%
  - Production total return: +439.54%
  - Buy and Hold max drawdown: -66.89%
  - Production max drawdown: -29.12%

Detailed report: `docs/backtesting-reports/backtest_summary.md`

### 2. Regime Robustness

Subperiods tested: Bull 2021, Bear 2021-2022, Recovery 2022-2024, Post-Halving 2024-2026.

Latest summary:

- Production beat Buy and Hold in return on 2/4 regimes.
- Production beat Buy and Hold in Sharpe on 2/4 regimes.
- Production had lower drawdown on 3/4 regimes.

Detailed report: `docs/backtesting-reports/subperiod_analysis.md`

### 3. Walk-Forward (Purged + Embargo)

Latest configuration:

- Train window: 540 days
- Test window: 120 days
- Purge gap: 7 days
- Embargo gap: 3 days
- Fold step: 60 days
- Folds: 22

Latest out-of-sample aggregate:

| Model | Mean OOS Return | Mean OOS Sharpe | Worst Max DD | Return > BnH Folds | Decision |
| :--- | ---: | ---: | ---: | ---: | :--- |
| `production_legacy_cooldown1` | +20.31% | 1.342 | -20.09% | 11/22 | implement with guardrails |
| `legacy_cooldown3_baseline` | +20.31% | 1.323 | -20.09% | 11/22 | keep baseline |
| `legacy_confidence_research` | +20.28% | 1.338 | -20.04% | 13/22 | secondary candidate |
| `advanced_adaptive_research` | +9.44% | 1.015 | -22.73% | 9/22 | do not implement |

Bootstrap significance (3,000 resamples on OOS daily returns):

| Comparison | Annualized Alpha | Alpha 95% CI | p(alpha <= 0) | Delta Sharpe | Delta Sharpe 95% CI | p(delta_sharpe <= 0) |
| :--- | ---: | :--- | ---: | ---: | :--- | ---: |
| Production vs Baseline | +0.05% | [-1.51%, +1.55%] | 0.4805 | -0.002 | [-0.046, +0.040] | 0.5322 |
| Production vs Buy and Hold | +13.26% | [-2.59%, +29.82%] | 0.0510 | +0.607 | [+0.283, +0.941] | 0.0010 |
| Confidence vs Production | -0.11% | [-0.49%, +0.29%] | 0.7044 | +0.003 | [-0.007, +0.013] | 0.2986 |

Detailed report: `docs/backtesting-reports/walkforward_analysis.md`

## Runbook

### Local commands

```bash
make install
make status
make run
make paper
make dashboard
make backtest
make backtest-subperiod
make backtest-walkforward
make backtest-all
make test
```

### CLI shortcuts

```bash
python main.py status --json
python main.py download --strict
python main.py process
python main.py paper
python main.py full --strict
python main.py dashboard --port 5000
python tests/backtest/compare_models.py
python tests/backtest/subperiod_analysis.py
python tests/backtest/walkforward_analysis.py
```

### Required secret

Create `.env` from `.env.example` and set:

```bash
FRED_API_KEY=your_fred_api_key_here
```

## Daily Automation (GitHub Actions)

Two workflows are included:

- CI: syntax checks, unit tests, and health checks on push and pull request.
- Daily pipeline: runs download -> process -> paper, uploads artifacts, and commits generated outputs.

The daily workflow updates:

- `README.md` live forward-testing block
- `latest_report.md`
- `reports/daily/*`
- `data/raw/*`, `data/processed/*`, `data/signals/*`, `data/accounting/*`

To enable the daily workflow:

- Add `FRED_API_KEY` under repository secrets, or
- Add `FRED_API_KEY` to a GitHub Environment and set `WORKFLOW_ENVIRONMENT` repository variable.

## Roadmap

Near-term priorities:

1. Increase out-of-sample fold coverage and statistical power.
2. Improve confidence-based allocation and retest against production baseline.
3. Expand robustness checks for execution costs and regime transitions.
4. Keep production changes gated by objective out-of-sample criteria.
