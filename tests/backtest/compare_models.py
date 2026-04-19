from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sys

import math
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.execution.advanced_portfolio_manager import AdvancedPortfolioManager
from src.execution.confidence_portfolio_manager import ConfidencePortfolioManager
from src.execution.portfolio_manager import PortfolioManager
from src.strategy.legacy_score import LegacyQuantScorer
from src.strategy.score import AdvancedQuantScorer, QuantScorer
from tests.backtest.data_loader import BacktestDataLoader


INITIAL_CAPITAL = 10_000.0
START_DATE = "2021-01-01"
TRADING_COST_BPS = 15.0
ANNUAL_DEBT_RATE = 0.10

SUMMARY_PATH = Path("docs/backtesting-reports/backtest_summary.md")
CSV_PATH = Path("tests/backtest/model_comparison.csv")


@dataclass
class SimulationResult:
    model: str
    total_return_pct: float
    cagr_pct: float
    max_drawdown_pct: float
    sharpe: float
    sortino: float
    calmar: float
    annual_volatility_pct: float
    trades: int
    turnover_usd: float
    trades_per_year: float
    avg_leverage: float
    max_leverage: float
    final_equity: float


class PortfolioSimulator:
    def __init__(self, trading_cost_bps=TRADING_COST_BPS, annual_debt_rate=ANNUAL_DEBT_RATE):
        self.trading_cost_bps = trading_cost_bps
        self.annual_debt_rate = annual_debt_rate

    def _execute_order(self, side, amount_usd, price, cash, btc, debt):
        fee_rate = self.trading_cost_bps / 10_000.0
        notional = max(float(amount_usd), 0.0)
        traded_notional = 0.0

        if side == "BUY" and notional > 0:
            fee = notional * fee_rate
            total_cost = notional + fee

            if total_cost > cash:
                debt += total_cost - cash
                cash = 0.0
            else:
                cash -= total_cost

            btc += notional / price
            traded_notional = notional

        elif side == "SELL" and notional > 0 and btc > 0:
            btc_to_sell = min(btc, notional / price)
            gross = btc_to_sell * price
            fee = gross * fee_rate
            proceeds = gross - fee

            btc -= btc_to_sell
            cash += proceeds
            traded_notional = gross

            if debt > 0 and cash > 0:
                repayment = min(debt, cash)
                debt -= repayment
                cash -= repayment

        return cash, btc, debt, traded_notional

    def run(self, model_name, scorer, manager, daily_data):
        cash = INITIAL_CAPITAL
        btc = 0.0
        debt = 0.0
        last_trade_date = None

        equities = []
        leverages = []
        daily_returns = []

        turnover = 0.0
        trades = 0
        prev_equity = INITIAL_CAPITAL

        for day in daily_data:
            price = float(day["market_data"]["current_price"])
            date_str = day["timestamp"][:10]

            if debt > 0:
                debt *= 1.0 + (self.annual_debt_rate / 365.0)

            scores = scorer.calculate_scores(day)["scores"]
            order = manager.calculate_order(
                scores=scores,
                current_cash=cash,
                current_btc_value=btc * price,
                current_debt=debt,
                last_trade_date=last_trade_date,
                current_date=date_str,
            )

            if order is not None:
                cash, btc, debt, traded_notional = self._execute_order(
                    order.side,
                    order.amount_usd,
                    price,
                    cash,
                    btc,
                    debt,
                )
                if traded_notional > 0:
                    trades += 1
                    turnover += traded_notional
                    last_trade_date = date_str

            equity = cash + (btc * price) - debt
            equity = max(equity, 1e-9)

            daily_ret = (equity / prev_equity) - 1.0 if prev_equity > 0 else 0.0
            prev_equity = equity

            leverage = ((btc * price) + debt) / equity if equity > 0 else 0.0

            equities.append(equity)
            leverages.append(leverage)
            daily_returns.append(daily_ret)

        return self._compute_metrics(model_name, equities, daily_returns, leverages, trades, turnover)

    def _compute_metrics(self, model_name, equities, daily_returns, leverages, trades, turnover):
        equity_series = pd.Series(equities)
        returns = pd.Series(daily_returns[1:]) if len(daily_returns) > 1 else pd.Series(dtype=float)

        start_equity = INITIAL_CAPITAL
        final_equity = float(equity_series.iloc[-1]) if not equity_series.empty else start_equity

        total_return = ((final_equity / start_equity) - 1.0) * 100.0

        n_days = max(len(equity_series) - 1, 1)
        cagr = ((final_equity / start_equity) ** (365.0 / n_days) - 1.0) * 100.0

        running_max = equity_series.cummax()
        drawdown = (equity_series / running_max) - 1.0
        max_drawdown = float(drawdown.min() * 100.0)

        vol = float(returns.std() * math.sqrt(365.0) * 100.0) if not returns.empty else 0.0
        sharpe = float((returns.mean() / returns.std()) * math.sqrt(365.0)) if returns.std() and returns.std() > 0 else 0.0

        downside = returns[returns < 0]
        downside_std = downside.std()
        sortino = float((returns.mean() / downside_std) * math.sqrt(365.0)) if downside_std and downside_std > 0 else 0.0

        calmar = float(cagr / abs(max_drawdown)) if max_drawdown < 0 else 0.0

        years = n_days / 365.0
        trades_per_year = trades / years if years > 0 else 0.0

        avg_leverage = float(pd.Series(leverages).mean()) if leverages else 0.0
        max_leverage = float(pd.Series(leverages).max()) if leverages else 0.0

        return SimulationResult(
            model=model_name,
            total_return_pct=round(total_return, 2),
            cagr_pct=round(cagr, 2),
            max_drawdown_pct=round(max_drawdown, 2),
            sharpe=round(sharpe, 3),
            sortino=round(sortino, 3),
            calmar=round(calmar, 3),
            annual_volatility_pct=round(vol, 2),
            trades=trades,
            turnover_usd=round(turnover, 2),
            trades_per_year=round(trades_per_year, 2),
            avg_leverage=round(avg_leverage, 2),
            max_leverage=round(max_leverage, 2),
            final_equity=round(final_equity, 2),
        )


def buy_and_hold_metrics(daily_data):
    prices = [float(day["market_data"]["current_price"]) for day in daily_data]
    if not prices:
        raise RuntimeError("Backtest dataset is empty.")

    units = INITIAL_CAPITAL / prices[0]
    equities = [units * p for p in prices]
    returns = pd.Series(equities).pct_change().dropna()

    total_return = ((equities[-1] / INITIAL_CAPITAL) - 1.0) * 100.0
    n_days = max(len(equities) - 1, 1)
    cagr = ((equities[-1] / INITIAL_CAPITAL) ** (365.0 / n_days) - 1.0) * 100.0

    equity_series = pd.Series(equities)
    running_max = equity_series.cummax()
    drawdown = (equity_series / running_max) - 1.0
    max_drawdown = float(drawdown.min() * 100.0)

    vol = float(returns.std() * math.sqrt(365.0) * 100.0) if not returns.empty else 0.0
    sharpe = float((returns.mean() / returns.std()) * math.sqrt(365.0)) if returns.std() and returns.std() > 0 else 0.0

    return {
        "total_return_pct": round(total_return, 2),
        "cagr_pct": round(cagr, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
        "annual_volatility_pct": round(vol, 2),
        "sharpe": round(sharpe, 3),
        "final_equity": round(float(equities[-1]), 2),
    }


def recommendation_table(results_df):
    baseline = results_df.loc[results_df["model"] == "legacy_signal + legacy_allocation(cooldown=3)"].iloc[0]

    rows = []
    for _, row in results_df.iterrows():
        if row["model"] == "legacy_signal + legacy_allocation(cooldown=3)":
            rows.append((row["model"], "Baseline", "KEEP (benchmark)"))
            continue

        checks = {
            "higher_return": row["total_return_pct"] > baseline["total_return_pct"],
            "lower_drawdown": row["max_drawdown_pct"] > baseline["max_drawdown_pct"],
            "higher_sharpe": row["sharpe"] > baseline["sharpe"],
        }
        passed = sum(checks.values())

        if passed == 3:
            decision = "IMPLEMENT"
        elif passed == 2:
            decision = "IMPLEMENT WITH GUARDRAILS"
        else:
            decision = "DO NOT IMPLEMENT"

        rationale = ", ".join([f"{k}={'yes' if v else 'no'}" for k, v in checks.items()])
        rows.append((row["model"], rationale, decision))

    return rows


def write_outputs(results_df, buy_hold, recommendations):
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

    results_df.to_csv(CSV_PATH, index=False)

    today = datetime.now().strftime("%Y-%m-%d")

    md = []
    md.append("# Backtest Summary")
    md.append("")
    md.append(f"Generated on: **{today}**")
    md.append("")
    md.append("## Configuration")
    md.append(f"- Initial capital: `${INITIAL_CAPITAL:,.2f}`")
    md.append(f"- Start date: `{START_DATE}`")
    md.append(f"- Trading cost: `{TRADING_COST_BPS:.2f}` bps per side")
    md.append(f"- Debt interest: `{ANNUAL_DEBT_RATE * 100:.2f}%` annual")
    md.append("")
    md.append("## Model Comparison")
    md.append("")
    md.append("| Model | Total Return | CAGR | Max Drawdown | Sharpe | Sortino | Calmar | Volatility | Trades | Avg Lev | Max Lev |")
    md.append("| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")

    for _, row in results_df.iterrows():
        md.append(
            "| {model} | {total_return_pct:+.2f}% | {cagr_pct:+.2f}% | {max_drawdown_pct:.2f}% | {sharpe:.3f} | {sortino:.3f} | {calmar:.3f} | {annual_volatility_pct:.2f}% | {trades} | {avg_leverage:.2f}x | {max_leverage:.2f}x |".format(
                **row.to_dict()
            )
        )

    md.append("")
    md.append("## Buy and Hold (BTC)")
    md.append("")
    md.append("| Metric | Value |")
    md.append("| :--- | ---: |")
    md.append(f"| Total Return | {buy_hold['total_return_pct']:+.2f}% |")
    md.append(f"| CAGR | {buy_hold['cagr_pct']:+.2f}% |")
    md.append(f"| Max Drawdown | {buy_hold['max_drawdown_pct']:.2f}% |")
    md.append(f"| Sharpe | {buy_hold['sharpe']:.3f} |")
    md.append("")

    md.append("## Implementation Decision")
    md.append("")
    md.append("| Candidate | Evidence | Decision |")
    md.append("| :--- | :--- | :--- |")
    for model, rationale, decision in recommendations:
        md.append(f"| {model} | {rationale} | **{decision}** |")

    md.append("")
    md.append("## Notes")
    md.append("")
    md.append("- This research backtest uses the same feature schema as production but includes transaction costs and debt carry.")
    md.append("- Use these results as a gate before changing production defaults.")
    md.append("- Regime stability details: `docs/backtesting-reports/subperiod_analysis.md`.")
    md.append("- Walk-forward + bootstrap significance: `docs/backtesting-reports/walkforward_analysis.md`.")

    SUMMARY_PATH.write_text("\n".join(md), encoding="utf-8")


def run_model_comparison():
    loader = BacktestDataLoader(start_date=START_DATE)
    loader.fetch_data()
    daily_data = list(loader.generator())

    simulator = PortfolioSimulator()

    candidates = [
        (
            "legacy_signal + legacy_allocation(cooldown=3)",
            LegacyQuantScorer(),
            PortfolioManager(min_trade_usd=20.0, cooldown_days=3),
        ),
        (
            "legacy_signal + legacy_allocation(cooldown=1)",
            QuantScorer(mode="legacy"),
            PortfolioManager(min_trade_usd=20.0, cooldown_days=1),
        ),
        (
            "advanced_signal + legacy_allocation(cooldown=3)",
            AdvancedQuantScorer(),
            PortfolioManager(min_trade_usd=20.0, cooldown_days=3),
        ),
        (
            "advanced_signal + adaptive_allocation",
            AdvancedQuantScorer(),
            AdvancedPortfolioManager(min_trade_usd=20.0, cooldown_days=1),
        ),
        (
            "legacy_signal + confidence_allocation",
            QuantScorer(mode="legacy"),
            ConfidencePortfolioManager(min_trade_usd=20.0, cooldown_days=1),
        ),
    ]

    results = [simulator.run(name, scorer, manager, daily_data) for name, scorer, manager in candidates]

    results_df = pd.DataFrame([r.__dict__ for r in results])
    buy_hold = buy_and_hold_metrics(daily_data)
    recommendations = recommendation_table(results_df)

    write_outputs(results_df, buy_hold, recommendations)

    print("Model comparison finished.")
    print(results_df[["model", "total_return_pct", "max_drawdown_pct", "sharpe", "trades"]])
    print("Buy and Hold:", buy_hold)


if __name__ == "__main__":
    run_model_comparison()
