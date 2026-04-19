from __future__ import annotations

from datetime import datetime
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
CSV_PATH = Path("tests/backtest/subperiod_results.csv")
SUMMARY_PATH = Path("docs/backtesting-reports/subperiod_analysis.md")

SUBPERIODS = [
    ("Bull 2021", "2021-01-01", "2021-11-10"),
    ("Bear 2021-2022", "2021-11-11", "2022-11-21"),
    ("Recovery 2022-2024", "2022-11-22", "2024-04-19"),
    ("Post-Halving 2024-2026", "2024-04-20", "2026-04-19"),
]


def in_range(date_str: str, start: str, end: str) -> bool:
    return start <= date_str <= end


def filter_period(daily_data: list[dict], start: str, end: str) -> list[dict]:
    return [row for row in daily_data if in_range(row["timestamp"][:10], start, end)]


def run_subperiod_analysis() -> None:
    loader = BacktestDataLoader(start_date=START_DATE)
    loader.fetch_data()
    daily_data = list(loader.generator())

    simulator = PortfolioSimulator()

    model_specs = [
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
            "advanced_adaptive_research",
            AdvancedQuantScorer(),
            AdvancedPortfolioManager(min_trade_usd=20.0, cooldown_days=1),
        ),
        (
            "legacy_confidence_research",
            QuantScorer(mode="legacy"),
            ConfidencePortfolioManager(min_trade_usd=20.0, cooldown_days=1),
        ),
    ]

    rows = []

    for period_name, start, end in SUBPERIODS:
        period_data = filter_period(daily_data, start, end)
        if len(period_data) < 30:
            continue

        bnh = buy_and_hold_metrics(period_data)
        rows.append(
            {
                "period": period_name,
                "model": "buy_and_hold",
                "total_return_pct": bnh["total_return_pct"],
                "cagr_pct": bnh["cagr_pct"],
                "max_drawdown_pct": bnh["max_drawdown_pct"],
                "sharpe": bnh["sharpe"],
                "trades": 0,
            }
        )

        for model_name, scorer, manager in model_specs:
            result = simulator.run(model_name, scorer, manager, period_data)
            rows.append(
                {
                    "period": period_name,
                    "model": model_name,
                    "total_return_pct": result.total_return_pct,
                    "cagr_pct": result.cagr_pct,
                    "max_drawdown_pct": result.max_drawdown_pct,
                    "sharpe": result.sharpe,
                    "trades": result.trades,
                }
            )

    df = pd.DataFrame(rows)
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV_PATH, index=False)

    lines = []
    lines.append("# Subperiod Stability Analysis")
    lines.append("")
    lines.append(f"Generated on: **{datetime.now().strftime('%Y-%m-%d')}**")
    lines.append("")
    lines.append("This report evaluates model behavior across different BTC market regimes.")
    lines.append("")

    for period_name, start, end in SUBPERIODS:
        period_df = df[df["period"] == period_name]
        if period_df.empty:
            continue

        lines.append(f"## {period_name} ({start} to {end})")
        lines.append("")
        lines.append("| Model | Total Return | CAGR | Max Drawdown | Sharpe | Trades |")
        lines.append("| :--- | ---: | ---: | ---: | ---: | ---: |")

        for _, row in period_df.iterrows():
            lines.append(
                "| {model} | {total_return_pct:+.2f}% | {cagr_pct:+.2f}% | {max_drawdown_pct:.2f}% | {sharpe:.3f} | {trades} |".format(
                    **row.to_dict()
                )
            )
        lines.append("")

    prod = df[df["model"] == "production_legacy_cooldown1"]
    bnh = df[df["model"] == "buy_and_hold"]
    merged = prod.merge(bnh, on="period", suffixes=("_prod", "_bnh"))

    outperform_return = int((merged["total_return_pct_prod"] > merged["total_return_pct_bnh"]).sum())
    outperform_sharpe = int((merged["sharpe_prod"] > merged["sharpe_bnh"]).sum())
    better_drawdown = int((merged["max_drawdown_pct_prod"] > merged["max_drawdown_pct_bnh"]).sum())

    lines.append("## Robustness Summary")
    lines.append("")
    lines.append(f"- Production model beat Buy & Hold in **return** on {outperform_return}/{len(merged)} subperiods.")
    lines.append(f"- Production model beat Buy & Hold in **Sharpe** on {outperform_sharpe}/{len(merged)} subperiods.")
    lines.append(f"- Production model had **lower drawdown** on {better_drawdown}/{len(merged)} subperiods.")

    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")

    print("Subperiod analysis completed.")
    print(df)


if __name__ == "__main__":
    run_subperiod_analysis()
