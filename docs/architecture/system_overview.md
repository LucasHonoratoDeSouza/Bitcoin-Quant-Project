**This project is a professional quant system for Bitcoin, divided into three fundamental pillars:**

The **Daily Analytical Pipeline** functions as the system's intelligent core: a batch process executed once a day that integrates multiple data sources (price, on-chain, derivatives, sentiment, data, cycles, news, etc.), applies advanced feature engineering, runs mathematical models and machine learning algorithms, assesses risk, and compiles a comprehensive decision-making snapshot. It synthesizes market signals, scenario probabilities, confidence metrics, potential leverage uses, and position recommendations, serving as the central component that transforms raw data into robust, auditable institutional decisions.

**24/7 Risk & Safety Mechanisms (Watchers)** – Lightweight modules that run continuously, monitoring only for critical events (Satoshi moving BTC, giant whale alerts, extreme institutional flows, extreme news). These modules can trigger emergency orders to protect the portfolio.

**Execution and Accounting** – The layer that securely executes orders, updates the portfolio state (cash, BTC, loan, equity), and ensures everything is auditable.

The philosophy is:

Heavy analysis → only in the daily process.
Instantaneous reaction to risks → 24/7 watchers.
Every decision is explainable and recorded.
Always prioritize greater accumulation of bitcoin and cash in the medium/long term.

## 2026-04-19 Update: Production vs Research Separation

The system now separates **production-grade defaults** from **research candidates**:

- Production scoring: legacy scorer (`QuantScorer(mode="legacy")`) selected by backtest gate.
- Production allocation: rule-based portfolio manager with tuned cooldown (`cooldown_days=1`).
- Research scoring: advanced probabilistic scorer (`AdvancedQuantScorer`) and adaptive allocator.

This avoids deploying underperforming candidates while keeping the research layer ready.

## Principles

1. Reproducibility: every decision can be re-run from saved artifacts.
2. Risk-first deployment: higher return alone is not sufficient for promotion.
3. Scientific rollout: candidates must pass objective checks on return, drawdown, and Sharpe.