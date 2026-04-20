from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.execution.advanced_portfolio_manager import AdvancedPortfolioManager
from src.execution.confidence_portfolio_manager import ConfidencePortfolioManager
from src.execution.portfolio_manager import PortfolioManager
from src.strategy.score import AdvancedQuantScorer, QuantScorer
from tests.backtest.compare_models import PortfolioSimulator, buy_and_hold_metrics
from tests.backtest.data_loader import BacktestDataLoader


START_DATE = "2020-01-01"

COST_SCENARIOS = [
    ("low_friction", 5.0, 0.05),
    ("base_case", 15.0, 0.10),
    ("stressed", 30.0, 0.15),
    ("extreme", 50.0, 0.20),
]

TRANSITION_DATES = [
    ("2021_peak_to_bear", "2021-11-11"),
    ("2022_bear_to_recovery", "2022-11-22"),
    ("2024_halving", "2024-04-20"),
]

TRANSITION_HALF_WINDOW_DAYS = 45
TRANSITION_COST_BPS = (15.0, 35.0)
TRANSITION_DEBT_RATE = 0.10

CSV_PATH = Path("tests/backtest/robustness_results.csv")
SUMMARY_PATH = Path("docs/backtesting-reports/robustness_analysis.md")


def to_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def in_range(date_str: str, start: str, end: str) -> bool:
    return start <= date_str <= end


def filter_period(daily_data: list[dict], start: str, end: str) -> list[dict]:
    return [row for row in daily_data if in_range(row["timestamp"][:10], start, end)]


def model_specs() -> list[tuple[str, object, object]]:
    return [
        (
            "production_legacy_cooldown1",
            QuantScorer(mode="legacy"),
            PortfolioManager(min_trade_usd=20.0, cooldown_days=1),
        ),
        (
            "legacy_cooldown3_baseline",
            QuantScorer(mode="legacy"),
            PortfolioManager(min_trade_usd=20.0, cooldown_days=3),
        ),
        (
            "legacy_confidence_research",
            QuantScorer(mode="legacy"),
            ConfidencePortfolioManager(min_trade_usd=20.0, cooldown_days=1),
        ),
        (
            "advanced_adaptive_research",
            AdvancedQuantScorer(),
            AdvancedPortfolioManager(min_trade_usd=20.0, cooldown_days=1),
        ),
    ]


def run_period_simulations(
    daily_data: list[dict],
    analysis_type: str,
    scenario: str,
    regime_context: str,
    window_start: str,
    window_end: str,
    trading_cost_bps: float,
    annual_debt_rate: float,
) -> list[dict]:
    simulator = PortfolioSimulator(
        trading_cost_bps=trading_cost_bps,
        annual_debt_rate=annual_debt_rate,
    )

    rows = []

    bnh = buy_and_hold_metrics(daily_data)
    rows.append(
        {
            "analysis_type": analysis_type,
            "scenario": scenario,
            "regime_context": regime_context,
            "window_start": window_start,
            "window_end": window_end,
            "trading_cost_bps": trading_cost_bps,
            "annual_debt_rate": annual_debt_rate,
            "model": "buy_and_hold",
            "total_return_pct": bnh["total_return_pct"],
            "cagr_pct": bnh["cagr_pct"],
            "max_drawdown_pct": bnh["max_drawdown_pct"],
            "sharpe": bnh["sharpe"],
            "trades": 0,
        }
    )

    for model_name, scorer, manager in model_specs():
        result = simulator.run(model_name, scorer, manager, daily_data)
        rows.append(
            {
                "analysis_type": analysis_type,
                "scenario": scenario,
                "regime_context": regime_context,
                "window_start": window_start,
                "window_end": window_end,
                "trading_cost_bps": trading_cost_bps,
                "annual_debt_rate": annual_debt_rate,
                "model": model_name,
                "total_return_pct": result.total_return_pct,
                "cagr_pct": result.cagr_pct,
                "max_drawdown_pct": result.max_drawdown_pct,
                "sharpe": result.sharpe,
                "trades": result.trades,
            }
        )

    return rows


def write_summary(df: pd.DataFrame) -> None:
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Execution Cost and Regime-Transition Robustness")
    lines.append("")
    lines.append(f"Generated on: **{datetime.now().strftime('%Y-%m-%d')}**")
    lines.append("")
    lines.append("This report stress-tests execution frictions and transition windows around regime changes.")
    lines.append("")

    cost_df = df[(df["analysis_type"] == "cost_stress") & (df["model"] != "buy_and_hold")]
    lines.append("## Cost Stress (Full Sample)")
    lines.append("")
    lines.append("| Scenario | Trading Cost | Debt Rate | Model | Total Return | Sharpe | Max Drawdown | Trades |")
    lines.append("| :--- | ---: | ---: | :--- | ---: | ---: | ---: | ---: |")
    for _, row in cost_df.iterrows():
        lines.append(
            "| {scenario} | {trading_cost_bps:.2f} bps | {annual_debt_rate:.2%} | {model} | {total_return_pct:+.2f}% | {sharpe:.3f} | {max_drawdown_pct:.2f}% | {trades} |".format(
                **row.to_dict()
            )
        )

    lines.append("")
    transition_df = df[(df["analysis_type"] == "transition_stress") & (df["model"] != "buy_and_hold")]
    lines.append("## Regime Transition Windows")
    lines.append("")
    lines.append("| Regime Transition | Window | Trading Cost | Model | Total Return | Sharpe | Max Drawdown | Trades |")
    lines.append("| :--- | :--- | ---: | :--- | ---: | ---: | ---: | ---: |")
    for _, row in transition_df.iterrows():
        lines.append(
            "| {regime_context} | {window_start} to {window_end} | {trading_cost_bps:.2f} bps | {model} | {total_return_pct:+.2f}% | {sharpe:.3f} | {max_drawdown_pct:.2f}% | {trades} |".format(
                **row.to_dict()
            )
        )

    lines.append("")
    lines.append("## Robustness Diagnostics")
    lines.append("")

    prod_cost = cost_df[cost_df["model"] == "production_legacy_cooldown1"]
    base_cost = cost_df[cost_df["model"] == "legacy_cooldown3_baseline"]
    merged_cost = prod_cost.merge(
        base_cost,
        on="scenario",
        suffixes=("_prod", "_base"),
    )
    prod_cost_beats = int(
        (merged_cost["total_return_pct_prod"] > merged_cost["total_return_pct_base"]).sum()
    )

    prod_trans = transition_df[transition_df["model"] == "production_legacy_cooldown1"]
    conf_trans = transition_df[transition_df["model"] == "legacy_confidence_research"]
    merged_trans = prod_trans.merge(
        conf_trans,
        on=["regime_context", "trading_cost_bps"],
        suffixes=("_prod", "_conf"),
    )
    conf_better_dd = int(
        (merged_trans["max_drawdown_pct_conf"] > merged_trans["max_drawdown_pct_prod"]).sum()
    )

    lines.append(
        f"- Production beat baseline in return on **{prod_cost_beats}/{len(merged_cost)}** full-sample cost scenarios."
    )
    lines.append(
        f"- Confidence model had lower drawdown than production on **{conf_better_dd}/{len(merged_trans)}** transition stress scenarios."
    )
    lines.append(
        "- Use this report together with walk-forward gate outputs before any production promotion."
    )

    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def run_robustness_analysis() -> None:
    loader = BacktestDataLoader(start_date=START_DATE)
    loader.fetch_data()
    daily_data = list(loader.generator())

    if not daily_data:
        raise RuntimeError("Robustness dataset is empty.")

    rows = []

    first_date = daily_data[0]["timestamp"][:10]
    last_date = daily_data[-1]["timestamp"][:10]
    for scenario_name, cost_bps, debt_rate in COST_SCENARIOS:
        rows.extend(
            run_period_simulations(
                daily_data=daily_data,
                analysis_type="cost_stress",
                scenario=scenario_name,
                regime_context="full_sample",
                window_start=first_date,
                window_end=last_date,
                trading_cost_bps=cost_bps,
                annual_debt_rate=debt_rate,
            )
        )

    for regime_name, transition_date in TRANSITION_DATES:
        center = to_date(transition_date)
        window_start = (center - timedelta(days=TRANSITION_HALF_WINDOW_DAYS)).isoformat()
        window_end = (center + timedelta(days=TRANSITION_HALF_WINDOW_DAYS)).isoformat()

        period_data = filter_period(daily_data, window_start, window_end)
        if len(period_data) < 30:
            continue

        for cost_bps in TRANSITION_COST_BPS:
            rows.extend(
                run_period_simulations(
                    daily_data=period_data,
                    analysis_type="transition_stress",
                    scenario=f"{regime_name}_{int(cost_bps)}bps",
                    regime_context=regime_name,
                    window_start=window_start,
                    window_end=window_end,
                    trading_cost_bps=cost_bps,
                    annual_debt_rate=TRANSITION_DEBT_RATE,
                )
            )

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("Robustness analysis produced no rows.")

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV_PATH, index=False)
    write_summary(df)

    print("Robustness analysis completed.")
    print(df[["analysis_type", "scenario", "model", "total_return_pct", "sharpe"]].head(20))


if __name__ == "__main__":
    run_robustness_analysis()
