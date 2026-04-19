# 🏦 Bitcoin Quant Project
### Institutional-Grade Algorithmic Trading System

> **"Discipline of a Robot, Intelligence of a Quant."**

---

## 🚀 Value Proposition
Investing in Bitcoin is volatile. Emotional decisions—buying the top due to FOMO or selling the bottom due to panic—are the #1 destroyer of capital.

This project solves that problem by replacing **emotion** with **math**.

We have built a sophisticated **Quantitative Engine** that analyzes the market from every angle (On-Chain Data, Macroeconomics, Derivatives, Sentiment) to make objective, high-probability capital allocation decisions.

> **🎯 Investment Horizon**: **Medium to Long Term**.
> This system is designed for **Wealth Accumulation**, not high-frequency day trading. It aims to catch major market cycles (months to years) while protecting capital during multi-year bear markets.

## 🧠 Core Technology

### 1. The Analytical Engine (QuantScorer)
Every day, the system ingests millions of data points to answer one question: **"What is the risk/reward ratio today?"**
*   **On-Chain Analysis**: Are long-term holders selling? Is the network growing?
*   **Macroeconomics**: Interest rates, Inflation (CPI), Dollar Strength (DXY).
*   **Market Sentiment**: Fear & Greed, Volatility.
*   **Derivatives**: Funding Rates, Open Interest.

> **Production Mode (2026-04-19)**: `QuantScorer(mode="legacy")` remains the default because it outperformed research candidates in the latest cost-aware out-of-sample comparison.

### 2. The Risk Manager (Portfolio Manager)
The engine doesn't just say "Buy" or "Sell". It manages **Risk**.
*   **Accumulation**: Slowly buying when the market is undervalued.
*   **Sniper Mode (Scalp)**: Taking quick profits during short-term rallies.
*   **Capital Preservation**: Moving to Cash (USD) when risk is extreme.
*   **Smart Leverage**: Only borrowing (up to 2x) when conditions are "Perfect" (>80/100 Score).

> **Execution Tuning (2026-04-19)**: cooldown reduced to 1 day after backtest gate (`legacy_signal + legacy_allocation(cooldown=1)`).

### 3. The Ledger (Auditable Accounting)
Transparency is key. The system maintains a permanent, immutable record of every decision.
*   **Daily Reports**: Detailed snapshots of Equity, ROI, and Alpha.
*   **Order Book**: A CSV log of every trade executed.
*   **Paper Trading**: A simulation mode to validate performance before risking real capital.

---

## ⚙️ Operating The Project

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
/home/lucas/Bitcoin-Quant-Project/.venv/bin/python tests/backtest/compare_models.py
/home/lucas/Bitcoin-Quant-Project/.venv/bin/python tests/backtest/subperiod_analysis.py
/home/lucas/Bitcoin-Quant-Project/.venv/bin/python tests/backtest/walkforward_analysis.py
```

### Required secret

Create a `.env` file from `.env.example` and set:

```bash
FRED_API_KEY=your_fred_api_key_here
```

---

<!-- live-stats:start -->
## Live Paper Trading
*Forward testing since Nov 23, 2025.*
*Key benchmark: **Alpha vs BTC** shows whether the strategy is beating simple Bitcoin buy-and-hold over the same period.*

| Metric | Value | Description |
| :--- | :--- | :--- |
| **Initial Capital** | `$2,000.00` | Starting Equity (Cash + BTC) |
| **Current Equity** | `$1,921.96` | Updated from the latest paper trading snapshot |
| **Alpha vs BTC** | `+8.59%` | Strategy ROI minus BTC buy-and-hold ROI over the same forward-testing window |
| **Net Profit** | `$-78.04` | **-3.90%** |
| **Avg. Monthly Return** | `-0.81%` | Projected (30-day) |
| **Win Rate** | `0.0%` | 0 Trades Executed |

> **Status**: 🔴 **Active** & **Drawdown** (Capital Preserved).
<!-- live-stats:end -->

*The system is currently in "Forward Testing" mode to validate the Backtest results in real-time market conditions.*

---

## 📊 Backtest Performance (Updated 2026-04-19)
*Cost-aware model comparison with transaction costs and debt carry.*

### The Numbers

| Metric | Buy & Hold | Quant Strategy | Outcome |
| :--- | :--- | :--- | :--- |
| **Total Return** | +63.53% | **+439.54%** | **+376.01%** 🚀 |
| **CAGR** | +12.12% | **+48.01%** | **+35.89%** |
| **Max Drawdown** | -66.89% | **-29.12%** | **+37.77%** 🛡️ |
| **Sharpe Ratio** | 0.480 | **1.272** | **+0.792** |
| **Test Period** | Jan 2021 - Apr 2026 | 5+ Years | **Multi-Regime** |

### Model Gate Decision (What Was Implemented)

| Candidate | Decision |
| :--- | :--- |
| `legacy_signal + legacy_allocation(cooldown=1)` | **IMPLEMENT WITH GUARDRAILS** |
| `legacy_signal + confidence_allocation` | **DO NOT IMPLEMENT** (primary gate) |
| `advanced_signal + legacy_allocation(cooldown=3)` | **DO NOT IMPLEMENT** |
| `advanced_signal + adaptive_allocation` | **DO NOT IMPLEMENT** |

Detailed report: `docs/backtesting-reports/backtest_summary.md`

### Subperiod Robustness (2026-04-19)

| Regime | Buy & Hold Return | Production Return | Buy & Hold Max DD | Production Max DD |
| :--- | ---: | ---: | ---: | ---: |
| Bull 2021 | +121.27% | +65.61% | -53.06% | **-30.90%** |
| Bear 2021-2022 | -75.69% | **-29.99%** | -75.89% | **-30.03%** |
| Recovery 2022-2024 | **+294.35%** | +286.79% | -20.06% | -20.06% |
| Post-Halving 2024-2026 | +16.51% | **+81.97%** | -49.74% | **-18.01%** |

Robustness takeaways:

- Production model beat Buy & Hold in return on **2/4** regimes.
- Production model beat Buy & Hold in Sharpe on **2/4** regimes.
- Production model had lower drawdown on **3/4** regimes.

Detailed robustness report: `docs/backtesting-reports/subperiod_analysis.md`

### Walk-Forward Validation (Purged + Embargo, 2026-04-19)

Configuration:

- Train window: 540 days
- Test window: 120 days
- Purge gap: 7 days
- Embargo gap: 3 days
- Fold step: 60 days
- Folds: 22

| Model | Mean OOS Return | Mean OOS Sharpe | Worst Max DD | Return > BnH Folds | Decision |
| :--- | ---: | ---: | ---: | ---: | :--- |
| `production_legacy_cooldown1` | **+20.31%** | **1.342** | -20.09% | 11/22 | **IMPLEMENT WITH GUARDRAILS** |
| `legacy_cooldown3_baseline` | +20.31% | 1.323 | -20.09% | 11/22 | KEEP (benchmark) |
| `legacy_confidence_research` | +20.28% | 1.338 | **-20.04%** | 13/22 | **IMPLEMENT WITH GUARDRAILS** (secondary gate) |
| `advanced_adaptive_research` | +9.44% | 1.015 | -22.73% | 9/22 | DO NOT IMPLEMENT |

Interpretation:

- Production (`cooldown=1`) and confidence allocation stayed statistically tied on OOS mean return.
- Confidence allocation improved drawdown profile across folds (lower DD vs Buy & Hold in 20/22 folds).
- Advanced adaptive remained below baseline on return and Sharpe.

Bootstrap significance on OOS daily returns (3,000 resamples):

| Comparison | Annualized Alpha | Alpha 95% CI | p(alpha <= 0) | Delta Sharpe | Delta Sharpe 95% CI | p(delta_sharpe <= 0) |
| :--- | ---: | :--- | ---: | ---: | :--- | ---: |
| Production vs Baseline | +0.05% | [-1.51%, +1.55%] | 0.4805 | -0.002 | [-0.046, +0.040] | 0.5322 |
| Production vs Buy & Hold | +13.26% | [-2.59%, +29.82%] | 0.0510 | +0.607 | [+0.283, +0.941] | 0.0010 |
| Confidence vs Production | -0.11% | [-0.49%, +0.29%] | 0.7044 | +0.003 | [-0.007, +0.013] | 0.2986 |

Statistical takeaway:

- Production remains strongly superior to Buy & Hold in risk-adjusted terms (Delta Sharpe bootstrap p=0.0010).
- Production and confidence allocation are statistically tied so far; confidence is retained as active research candidate.

Detailed walk-forward report: `docs/backtesting-reports/walkforward_analysis.md`

---

## 🗺️ Roadmap: The Future of Trading

### Phase 1: Foundation (Completed) ✅
*   [x] Data Ingestion Pipeline.
*   [x] Quantitative Scoring Engine.
*   [x] Portfolio Management & Risk Rules.
*   [x] Paper Trading Ecosystem.

### Phase 2: Intelligence (In Progress) 🚧
*   [ ] **LLM Integration (The "AI Consultant")**: Integrating Large Language Models (like GPT-5/Gemini).
*   [ ] **News Sentiment Analysis**: Real-time scanning of global news to detect black swan events.

### Phase 3: Real-Time Defense 🛡️
*   [ ] **Whale Watchers**: 24/7 monitoring of large wallet movements.
*   [ ] **Exchange Integration**: Direct connection to Binance/Bybit for automated execution.

---

## 🤖 GitHub Actions

The repository now ships with two automation flows:

*   **CI**: runs syntax validation, unit tests, and a quick status check on pushes and pull requests.
*   **Daily pipeline**: runs the full download -> process -> paper trading routine on a schedule, uploads artifacts, and commits generated reports/data back to the repository.

To enable the daily workflow in GitHub:

*   Use `Settings > Secrets and variables > Actions > Repository secrets` and create `FRED_API_KEY`.
*   Or use `Settings > Environments`, store `FRED_API_KEY` in that environment, and create the repository variable `WORKFLOW_ENVIRONMENT` with the exact environment name.

Check the `reports/daily/` folder for the generated investment memos.

---
*Built with Python and Financial Discipline.*
