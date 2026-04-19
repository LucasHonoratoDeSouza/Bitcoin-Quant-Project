from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
import sys
import math

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.execution.advanced_portfolio_manager import AdvancedPortfolioManager
from src.execution.confidence_portfolio_manager import ConfidencePortfolioManager
from src.execution.portfolio_manager import PortfolioManager
from src.strategy.score import AdvancedQuantScorer, QuantScorer
from tests.backtest.compare_models import INITIAL_CAPITAL, PortfolioSimulator, buy_and_hold_metrics
from tests.backtest.data_loader import BacktestDataLoader


START_DATE = "2020-01-01"
TRAIN_DAYS = 540
TEST_DAYS = 120
PURGE_DAYS = 7
EMBARGO_DAYS = 3
FOLD_STEP_DAYS = 60
BOOTSTRAP_SAMPLES = 3000
BOOTSTRAP_SEED = 42

CSV_PATH = Path("tests/backtest/walkforward_results.csv")
SUMMARY_PATH = Path("docs/backtesting-reports/walkforward_analysis.md")


def to_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def to_str(value: date) -> str:
    return value.isoformat()


def in_range(date_str: str, start: str, end: str) -> bool:
    return start <= date_str <= end


def filter_period(daily_data: list[dict], start: str, end: str) -> list[dict]:
    return [row for row in daily_data if in_range(row["timestamp"][:10], start, end)]


def buy_and_hold_daily_returns(daily_data: list[dict]) -> list[float]:
    prices = [float(day["market_data"]["current_price"]) for day in daily_data]
    if len(prices) < 2:
        return []

    units = INITIAL_CAPITAL / prices[0]
    equities = [units * price for price in prices]

    returns = []
    prev_equity = equities[0]
    for equity in equities[1:]:
        returns.append((equity / prev_equity) - 1.0 if prev_equity > 0 else 0.0)
        prev_equity = equity

    return returns


def simulate_daily_returns(daily_data: list[dict], scorer, manager) -> list[float]:
    simulator = PortfolioSimulator()

    cash = INITIAL_CAPITAL
    btc = 0.0
    debt = 0.0
    last_trade_date = None
    prev_equity = INITIAL_CAPITAL

    returns = []
    for day in daily_data:
        price = float(day["market_data"]["current_price"])
        date_str = day["timestamp"][:10]

        if debt > 0:
            debt *= 1.0 + (simulator.annual_debt_rate / 365.0)

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
            cash, btc, debt, traded_notional = simulator._execute_order(
                order.side,
                order.amount_usd,
                price,
                cash,
                btc,
                debt,
            )
            if traded_notional > 0:
                last_trade_date = date_str

        equity = max(cash + (btc * price) - debt, 1e-9)
        returns.append((equity / prev_equity) - 1.0 if prev_equity > 0 else 0.0)
        prev_equity = equity

    return returns[1:] if len(returns) > 1 else []


def _annualized_sharpe(values: np.ndarray) -> float:
    if values.size < 2:
        return 0.0
    stdev = values.std(ddof=1)
    if stdev <= 0:
        return 0.0
    return float((values.mean() / stdev) * math.sqrt(365.0))


def bootstrap_significance(label: str, lhs_returns: list[float], rhs_returns: list[float]) -> dict:
    lhs = np.array(lhs_returns, dtype=float)
    rhs = np.array(rhs_returns, dtype=float)

    if lhs.size == 0 or rhs.size == 0:
        return {
            "comparison": label,
            "observations": 0,
            "alpha_ann_pct": 0.0,
            "alpha_ci_low_ann_pct": 0.0,
            "alpha_ci_high_ann_pct": 0.0,
            "alpha_p_value": 1.0,
            "delta_sharpe": 0.0,
            "delta_sharpe_ci_low": 0.0,
            "delta_sharpe_ci_high": 0.0,
            "delta_sharpe_p_value": 1.0,
        }

    n_obs = min(lhs.size, rhs.size)
    lhs = lhs[:n_obs]
    rhs = rhs[:n_obs]

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    alpha_samples = np.zeros(BOOTSTRAP_SAMPLES, dtype=float)
    sharpe_diff_samples = np.zeros(BOOTSTRAP_SAMPLES, dtype=float)

    for i in range(BOOTSTRAP_SAMPLES):
        idx = rng.integers(0, n_obs, size=n_obs)
        lhs_sample = lhs[idx]
        rhs_sample = rhs[idx]

        alpha_samples[i] = float((lhs_sample - rhs_sample).mean())
        sharpe_diff_samples[i] = _annualized_sharpe(lhs_sample) - _annualized_sharpe(rhs_sample)

    alpha_mean_daily = float((lhs - rhs).mean())
    alpha_ci = np.percentile(alpha_samples, [2.5, 97.5])
    delta_sharpe = _annualized_sharpe(lhs) - _annualized_sharpe(rhs)
    sharpe_ci = np.percentile(sharpe_diff_samples, [2.5, 97.5])

    alpha_p_value = float((np.sum(alpha_samples <= 0.0) + 1) / (BOOTSTRAP_SAMPLES + 1))
    sharpe_p_value = float((np.sum(sharpe_diff_samples <= 0.0) + 1) / (BOOTSTRAP_SAMPLES + 1))

    return {
        "comparison": label,
        "observations": int(n_obs),
        "alpha_ann_pct": round(alpha_mean_daily * 365.0 * 100.0, 2),
        "alpha_ci_low_ann_pct": round(float(alpha_ci[0]) * 365.0 * 100.0, 2),
        "alpha_ci_high_ann_pct": round(float(alpha_ci[1]) * 365.0 * 100.0, 2),
        "alpha_p_value": round(alpha_p_value, 4),
        "delta_sharpe": round(float(delta_sharpe), 3),
        "delta_sharpe_ci_low": round(float(sharpe_ci[0]), 3),
        "delta_sharpe_ci_high": round(float(sharpe_ci[1]), 3),
        "delta_sharpe_p_value": round(sharpe_p_value, 4),
    }


def build_folds(first_date: str, last_date: str) -> list[dict]:
    folds = []
    cursor = to_date(first_date)
    end_limit = to_date(last_date)
    fold_id = 1

    while True:
        train_start = cursor
        train_end = train_start + timedelta(days=TRAIN_DAYS - 1)

        test_start = train_end + timedelta(days=PURGE_DAYS + 1)
        test_end = test_start + timedelta(days=TEST_DAYS - 1)

        if test_end > end_limit:
            break

        embargo_start = test_end + timedelta(days=1)
        embargo_end = test_end + timedelta(days=EMBARGO_DAYS)

        folds.append(
            {
                "fold": fold_id,
                "train_start": to_str(train_start),
                "train_end": to_str(train_end),
                "purge_days": PURGE_DAYS,
                "test_start": to_str(test_start),
                "test_end": to_str(test_end),
                "embargo_days": EMBARGO_DAYS,
            }
        )

        cursor = cursor + timedelta(days=FOLD_STEP_DAYS)
        fold_id += 1

    return folds


def aggregate_oos(df: pd.DataFrame) -> pd.DataFrame:
    buy_hold = df[df["model"] == "buy_and_hold"][
        ["fold", "total_return_pct", "sharpe", "max_drawdown_pct"]
    ].rename(
        columns={
            "total_return_pct": "bnh_return_pct",
            "sharpe": "bnh_sharpe",
            "max_drawdown_pct": "bnh_max_drawdown_pct",
        }
    )

    candidates = df[df["model"] != "buy_and_hold"].merge(
        buy_hold,
        on="fold",
        how="left",
    )

    rows = []
    for model_name, group in candidates.groupby("model", sort=False):
        rows.append(
            {
                "model": model_name,
                "folds": int(len(group)),
                "mean_return_pct": round(float(group["total_return_pct"].mean()), 2),
                "median_return_pct": round(float(group["total_return_pct"].median()), 2),
                "mean_sharpe": round(float(group["sharpe"].mean()), 3),
                "worst_drawdown_pct": round(float(group["max_drawdown_pct"].min()), 2),
                "beat_bnh_return_folds": int((group["total_return_pct"] > group["bnh_return_pct"]).sum()),
                "beat_bnh_sharpe_folds": int((group["sharpe"] > group["bnh_sharpe"]).sum()),
                "lower_drawdown_than_bnh_folds": int(
                    (group["max_drawdown_pct"] > group["bnh_max_drawdown_pct"]).sum()
                ),
            }
        )

    summary_df = pd.DataFrame(rows)
    if not summary_df.empty:
        summary_df = summary_df.sort_values(by=["mean_return_pct", "mean_sharpe"], ascending=False)
    return summary_df


def recommendation_table(summary_df: pd.DataFrame) -> list[tuple[str, str, str]]:
    baseline_name = "legacy_cooldown3_baseline"
    baseline = summary_df.loc[summary_df["model"] == baseline_name]
    if baseline.empty:
        return []

    baseline_row = baseline.iloc[0]
    rows = []
    return_tolerance = 0.10
    sharpe_tolerance = 0.005
    drawdown_tolerance = 0.10

    for _, row in summary_df.iterrows():
        model_name = row["model"]

        if model_name == baseline_name:
            rows.append((model_name, "oos baseline", "KEEP (benchmark)"))
            continue

        checks = {
            "higher_or_equal_mean_return": row["mean_return_pct"] >= (baseline_row["mean_return_pct"] - return_tolerance),
            "higher_or_equal_mean_sharpe": row["mean_sharpe"] >= (baseline_row["mean_sharpe"] - sharpe_tolerance),
            "better_or_equal_worst_drawdown": row["worst_drawdown_pct"] >= (baseline_row["worst_drawdown_pct"] - drawdown_tolerance),
        }
        passed = sum(checks.values())

        if passed >= 2:
            decision = "IMPLEMENT WITH GUARDRAILS"
        else:
            decision = "DO NOT IMPLEMENT"

        evidence = ", ".join(f"{name}={'yes' if ok else 'no'}" for name, ok in checks.items())
        rows.append((model_name, evidence, decision))

    return rows


def write_outputs(
    results_df: pd.DataFrame,
    fold_meta: list[dict],
    summary_df: pd.DataFrame,
    recommendations: list[tuple[str, str, str]],
    bootstrap_rows: list[dict],
) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

    results_df.to_csv(CSV_PATH, index=False)

    lines = []
    lines.append("# Walk-Forward Purged/Embargo Analysis")
    lines.append("")
    lines.append(f"Generated on: **{datetime.now().strftime('%Y-%m-%d')}**")
    lines.append("")
    lines.append("## Configuration")
    lines.append(f"- Start date: `{START_DATE}`")
    lines.append(f"- Train window: `{TRAIN_DAYS}` days")
    lines.append(f"- Test window: `{TEST_DAYS}` days")
    lines.append(f"- Purge gap: `{PURGE_DAYS}` days")
    lines.append(f"- Embargo gap: `{EMBARGO_DAYS}` days")
    lines.append(f"- Fold step: `{FOLD_STEP_DAYS}` days")
    lines.append(f"- Number of folds: `{len(fold_meta)}`")
    lines.append("")

    lines.append("## Fold Schedule")
    lines.append("")
    lines.append("| Fold | Train Window | Purge | Test Window | Embargo | Test Obs |")
    lines.append("| :--- | :--- | ---: | :--- | ---: | ---: |")

    obs_by_fold = results_df.groupby("fold")["test_observations"].max().to_dict()
    for fold in fold_meta:
        fold_id = fold["fold"]
        lines.append(
            f"| {fold_id} | {fold['train_start']} to {fold['train_end']} | {fold['purge_days']} | {fold['test_start']} to {fold['test_end']} | {fold['embargo_days']} | {obs_by_fold.get(fold_id, 0)} |"
        )

    lines.append("")
    lines.append("## Out-of-Sample Aggregate")
    lines.append("")
    lines.append("| Model | Folds | Mean Return | Median Return | Mean Sharpe | Worst Max DD | Return > BnH (folds) | Sharpe > BnH (folds) | Lower DD than BnH (folds) |")
    lines.append("| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")

    for _, row in summary_df.iterrows():
        lines.append(
            "| {model} | {folds} | {mean_return_pct:+.2f}% | {median_return_pct:+.2f}% | {mean_sharpe:.3f} | {worst_drawdown_pct:.2f}% | {beat_bnh_return_folds}/{folds} | {beat_bnh_sharpe_folds}/{folds} | {lower_drawdown_than_bnh_folds}/{folds} |".format(
                **row.to_dict()
            )
        )

    lines.append("")
    lines.append("## Walk-Forward Gate Decision")
    lines.append("")
    lines.append("| Candidate | Evidence vs OOS Baseline | Decision |")
    lines.append("| :--- | :--- | :--- |")

    for model_name, evidence, decision in recommendations:
        lines.append(f"| {model_name} | {evidence} | **{decision}** |")

    if bootstrap_rows:
        lines.append("")
        lines.append("## Bootstrap Significance (OOS Daily Returns)")
        lines.append("")
        lines.append(
            "| Comparison | Obs | Annualized Alpha | Alpha 95% CI | p(alpha<=0) | Delta Sharpe | Delta Sharpe 95% CI | p(delta_sharpe<=0) |"
        )
        lines.append("| :--- | ---: | ---: | :--- | ---: | ---: | :--- | ---: |")

        for row in bootstrap_rows:
            lines.append(
                "| {comparison} | {observations} | {alpha_ann_pct:+.2f}% | [{alpha_ci_low_ann_pct:+.2f}%, {alpha_ci_high_ann_pct:+.2f}%] | {alpha_p_value:.4f} | {delta_sharpe:+.3f} | [{delta_sharpe_ci_low:+.3f}, {delta_sharpe_ci_high:+.3f}] | {delta_sharpe_p_value:.4f} |".format(
                    **row
                )
            )

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- This validation is strictly out-of-sample by fold test windows.")
    lines.append("- Purge and embargo are temporal guards to reduce leakage across adjacent windows.")
    lines.append("- Strategy parameters are fixed; no per-fold re-optimization is performed.")

    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def run_walkforward_analysis() -> None:
    loader = BacktestDataLoader(start_date=START_DATE)
    loader.fetch_data()
    daily_data = list(loader.generator())

    if not daily_data:
        raise RuntimeError("Walk-forward dataset is empty.")

    first_date = daily_data[0]["timestamp"][:10]
    last_date = daily_data[-1]["timestamp"][:10]
    folds = build_folds(first_date, last_date)

    if not folds:
        raise RuntimeError("Not enough data to build walk-forward folds.")

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

    oos_returns = {
        "production_legacy_cooldown1": [],
        "legacy_cooldown3_baseline": [],
        "advanced_adaptive_research": [],
        "legacy_confidence_research": [],
        "buy_and_hold": [],
    }

    rows = []
    for fold in folds:
        test_data = filter_period(daily_data, fold["test_start"], fold["test_end"])
        if len(test_data) < 30:
            continue

        bnh = buy_and_hold_metrics(test_data)
        oos_returns["buy_and_hold"].extend(buy_and_hold_daily_returns(test_data))
        rows.append(
            {
                "fold": fold["fold"],
                "train_start": fold["train_start"],
                "train_end": fold["train_end"],
                "test_start": fold["test_start"],
                "test_end": fold["test_end"],
                "test_observations": len(test_data),
                "model": "buy_and_hold",
                "total_return_pct": bnh["total_return_pct"],
                "cagr_pct": bnh["cagr_pct"],
                "max_drawdown_pct": bnh["max_drawdown_pct"],
                "sharpe": bnh["sharpe"],
                "trades": 0,
            }
        )

        for model_name, scorer, manager in model_specs:
            result = simulator.run(model_name, scorer, manager, test_data)
            fold_returns = simulate_daily_returns(test_data, scorer, manager)
            oos_returns[model_name].extend(fold_returns)
            rows.append(
                {
                    "fold": fold["fold"],
                    "train_start": fold["train_start"],
                    "train_end": fold["train_end"],
                    "test_start": fold["test_start"],
                    "test_end": fold["test_end"],
                    "test_observations": len(test_data),
                    "model": model_name,
                    "total_return_pct": result.total_return_pct,
                    "cagr_pct": result.cagr_pct,
                    "max_drawdown_pct": result.max_drawdown_pct,
                    "sharpe": result.sharpe,
                    "trades": result.trades,
                }
            )

    results_df = pd.DataFrame(rows)
    if results_df.empty:
        raise RuntimeError("Walk-forward produced no rows.")

    summary_df = aggregate_oos(results_df)
    recommendations = recommendation_table(summary_df)

    bootstrap_rows = [
        bootstrap_significance(
            "production_vs_baseline",
            oos_returns["production_legacy_cooldown1"],
            oos_returns["legacy_cooldown3_baseline"],
        ),
        bootstrap_significance(
            "production_vs_buy_and_hold",
            oos_returns["production_legacy_cooldown1"],
            oos_returns["buy_and_hold"],
        ),
        bootstrap_significance(
            "confidence_vs_production",
            oos_returns["legacy_confidence_research"],
            oos_returns["production_legacy_cooldown1"],
        ),
    ]

    write_outputs(results_df, folds, summary_df, recommendations, bootstrap_rows)

    print("Walk-forward analysis completed.")
    print(summary_df)


if __name__ == "__main__":
    run_walkforward_analysis()
