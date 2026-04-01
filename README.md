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

### 2. The Risk Manager (Portfolio Manager)
The engine doesn't just say "Buy" or "Sell". It manages **Risk**.
*   **Accumulation**: Slowly buying when the market is undervalued.
*   **Sniper Mode (Scalp)**: Taking quick profits during short-term rallies.
*   **Capital Preservation**: Moving to Cash (USD) when risk is extreme.
*   **Smart Leverage**: Only borrowing (up to 2x) when conditions are "Perfect" (>80/100 Score).

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
| **Current Equity** | `$1,863.33` | Updated from the latest paper trading snapshot |
| **Alpha vs BTC** | `+13.84%` | Strategy ROI minus BTC buy-and-hold ROI over the same forward-testing window |
| **Net Profit** | `$-136.67` | **-6.83%** |
| **Avg. Monthly Return** | `-1.63%` | Projected (30-day) |
| **Win Rate** | `0.0%` | 0 Trades Executed |

> **Status**: 🔴 **Active** & **Drawdown** (Capital Preserved).
<!-- live-stats:end -->

*The system is currently in "Forward Testing" mode to validate the Backtest results in real-time market conditions.*

---

## 📊 Backtest Performance (2021-2025)
*Validated against 1,789 days of real market conditions with institutional-grade macro data.*

### The Numbers

| Metric | Buy & Hold | Quant Strategy | Outcome |
| :--- | :--- | :--- | :--- |
| **Total Return** | +195.51% | **+225.73%** | **+30.22%** 🚀 |
| **Max Drawdown** | -76.63% | **-51.36%** | **-25.27%** 🛡️ |
| **Test Period** | Jan 2021 - Nov 2025 | 4+ Years | **Full Cycle+** |

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
