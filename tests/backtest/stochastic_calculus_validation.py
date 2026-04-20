from __future__ import annotations

from datetime import datetime, timedelta
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.execution.advanced_portfolio_manager import AdvancedPortfolioManager
from src.execution.confidence_portfolio_manager import ConfidencePortfolioManager
from src.execution.portfolio_manager import PortfolioManager
from src.features.cycle import BitcoinCycle
from src.features.seasonality import BitcoinSeasonality
from src.strategy.score import AdvancedQuantScorer, QuantScorer
from src.utils.project_paths import PROCESSED_DATA_DIR
from tests.backtest.compare_models import PortfolioSimulator, buy_and_hold_metrics
from tests.backtest.data_loader import BacktestDataLoader


SEED = 123
TRADING_DAYS = 365.0
DT = 1.0 / TRADING_DAYS

N_PATHS = 220
HORIZON_DAYS = 180

GRID_DRIFT_SCALES = np.linspace(0.60, 1.50, 7)
GRID_VOL_SCALES = np.linspace(0.70, 1.80, 7)
GRID_PATHS = 48
GRID_HORIZON_DAYS = 120

COST_BPS = 15.0
ANNUAL_DEBT_RATE = 0.10

PATH_RESULTS_CSV = Path("tests/backtest/stochastic_path_results.csv")
SUMMARY_CSV = Path("tests/backtest/stochastic_summary.csv")
GRID_CSV = Path("tests/backtest/stochastic_surface_grid.csv")
REPORT_MD = Path("docs/backtesting-reports/stochastic_validation.md")
FIGURES_DIR = Path("reports/stochastic/figures")


def _safe_float(value, default=0.0) -> float:
    try:
        if value is None:
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _load_processed_daily_data() -> list[dict]:
    rows: list[dict] = []
    for file_path in sorted(PROCESSED_DATA_DIR.glob("processed_data_*.json")):
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        price = payload.get("market_data", {}).get("current_price")
        if price is None:
            continue
        rows.append(payload)

    rows.sort(key=lambda row: row.get("timestamp", ""))
    return rows


def _load_daily_data() -> list[dict]:
    processed_rows = _load_processed_daily_data()
    if len(processed_rows) >= 120:
        return processed_rows

    try:
        loader = BacktestDataLoader(start_date="2020-01-01")
        loader.fetch_data()
        data = list(loader.generator())
        if data:
            return data
    except Exception:
        pass

    if processed_rows:
        return processed_rows

    raise RuntimeError("Unable to load data for stochastic validation.")


def _price_series(daily_data: list[dict]) -> pd.Series:
    rows = []
    for row in daily_data:
        ts = row.get("timestamp")
        price = row.get("market_data", {}).get("current_price")
        if ts is None or price is None:
            continue
        rows.append((pd.to_datetime(ts), _safe_float(price)))

    if not rows:
        raise RuntimeError("No valid prices available for stochastic calibration.")

    series = pd.Series([value for _, value in rows], index=[idx for idx, _ in rows], dtype=float)
    series = series[~series.index.duplicated(keep="last")].sort_index()
    series = series[series > 0]
    if series.empty:
        raise RuntimeError("Price series is empty after filtering invalid values.")
    return series


def _macro_baseline(daily_data: list[dict]) -> dict:
    metrics_df = pd.DataFrame(
        [
            {
                "interest_rate": _safe_float(row.get("metrics", {}).get("interest_rate"), 3.5),
                "m2_yoy": _safe_float(row.get("metrics", {}).get("m2_yoy"), 5.0),
                "inflation_yoy": _safe_float(row.get("metrics", {}).get("inflation_yoy"), 3.0),
            }
            for row in daily_data
        ]
    )

    return {
        "interest_rate": float(metrics_df["interest_rate"].median()) if not metrics_df.empty else 3.5,
        "m2_yoy": float(metrics_df["m2_yoy"].median()) if not metrics_df.empty else 5.0,
        "inflation_yoy": float(metrics_df["inflation_yoy"].median()) if not metrics_df.empty else 3.0,
    }


def estimate_regime_jump_parameters(prices: pd.Series) -> dict:
    log_returns = np.log(prices / prices.shift(1)).dropna()
    if log_returns.empty:
        raise RuntimeError("Insufficient data to estimate stochastic parameters.")

    realized_vol = log_returns.rolling(window=21, min_periods=5).std().bfill().ffill()
    q1 = float(realized_vol.quantile(0.33))
    q2 = float(realized_vol.quantile(0.66))

    regimes = np.where(realized_vol <= q1, 0, np.where(realized_vol <= q2, 1, 2))

    global_mu = float(log_returns.mean() / DT)
    global_sigma = float(log_returns.std(ddof=1) / math.sqrt(DT))
    global_sigma = max(global_sigma, 0.05)

    mu_regimes: list[float] = []
    sigma_regimes: list[float] = []
    for state in (0, 1, 2):
        state_returns = log_returns[regimes == state]
        if state_returns.empty:
            mu_regimes.append(global_mu)
            sigma_regimes.append(global_sigma)
            continue

        mu_state = float(state_returns.mean() / DT)
        sigma_state = float(state_returns.std(ddof=1) / math.sqrt(DT))
        if not np.isfinite(sigma_state) or sigma_state <= 0:
            sigma_state = global_sigma
        sigma_state = max(sigma_state, 0.05)

        mu_regimes.append(mu_state)
        sigma_regimes.append(sigma_state)

    transition_counts = np.ones((3, 3), dtype=float)
    prev = regimes[:-1]
    nxt = regimes[1:]
    for p, n in zip(prev, nxt):
        transition_counts[int(p), int(n)] += 1.0
    transition_matrix = transition_counts / transition_counts.sum(axis=1, keepdims=True)

    center = float(log_returns.mean())
    dispersion = float(log_returns.std(ddof=1))
    jump_mask = np.abs(log_returns - center) > (2.5 * dispersion)
    jumps = log_returns[jump_mask]

    jump_lambda = float(jumps.shape[0] / (log_returns.shape[0] * DT))
    jump_lambda = max(0.05, min(jump_lambda, 12.0))

    if jumps.empty:
        jump_mu = -0.0010
        jump_sigma = 0.015
    else:
        jump_mu = float(jumps.mean())
        jump_sigma = float(jumps.std(ddof=1)) if jumps.shape[0] > 1 else 0.015
        jump_sigma = max(jump_sigma, 0.005)

    return {
        "mu_regimes": mu_regimes,
        "sigma_regimes": sigma_regimes,
        "transition_matrix": transition_matrix,
        "jump_lambda": jump_lambda,
        "jump_mu": jump_mu,
        "jump_sigma": jump_sigma,
        "historical_mu": global_mu,
        "historical_sigma": global_sigma,
    }


def simulate_regime_jump_diffusion(
    params: dict,
    s0: float,
    n_paths: int,
    horizon_days: int,
    seed: int,
    drift_scale: float = 1.0,
    vol_scale: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)

    mu_regimes = np.array(params["mu_regimes"], dtype=float) * float(drift_scale)
    sigma_regimes = np.array(params["sigma_regimes"], dtype=float) * float(vol_scale)
    sigma_regimes = np.maximum(sigma_regimes, 0.05)

    jump_lambda = float(params["jump_lambda"]) * max(0.4, float(vol_scale))
    jump_mu = float(params["jump_mu"])
    jump_sigma = float(params["jump_sigma"]) * max(0.5, float(vol_scale))

    transition = np.array(params["transition_matrix"], dtype=float)

    prices = np.zeros((n_paths, horizon_days + 1), dtype=float)
    regimes = np.zeros((n_paths, horizon_days + 1), dtype=int)
    prices[:, 0] = float(s0)
    regimes[:, 0] = 1

    for t in range(horizon_days):
        z = rng.standard_normal(n_paths)
        next_regimes = np.zeros(n_paths, dtype=int)

        for i in range(n_paths):
            p = int(regimes[i, t])
            next_regimes[i] = int(rng.choice(3, p=transition[p]))

        regimes[:, t + 1] = next_regimes

        mu_t = mu_regimes[next_regimes]
        sigma_t = sigma_regimes[next_regimes]

        jump_counts = rng.poisson(jump_lambda * DT, size=n_paths)
        jump_term = np.zeros(n_paths, dtype=float)

        jump_indices = np.where(jump_counts > 0)[0]
        for idx in jump_indices:
            count = int(jump_counts[idx])
            jump_term[idx] = float(rng.normal(loc=jump_mu, scale=jump_sigma, size=count).sum())

        diffusion = (mu_t - (0.5 * (sigma_t ** 2))) * DT + (sigma_t * math.sqrt(DT) * z)
        dlog_s = diffusion + jump_term

        prices[:, t + 1] = np.maximum(prices[:, t] * np.exp(dlog_s), 1.0)

    return prices, regimes


def _phase_for_date(cycle: BitcoinCycle, date_value: datetime) -> str:
    return cycle.get_phase(date_value.strftime("%Y-%m-%d"))["phase"]


def build_synthetic_daily_data(
    price_path: np.ndarray,
    start_date: datetime,
    macro_baseline: dict,
) -> list[dict]:
    cycle = BitcoinCycle()
    seasonality = BitcoinSeasonality()

    dates = [start_date + timedelta(days=i) for i in range(len(price_path))]
    df = pd.DataFrame({"price": price_path}, index=pd.to_datetime(dates))

    df["daily_change_pct"] = df["price"].pct_change().fillna(0.0) * 100.0
    df["weekly_change_pct"] = df["price"].pct_change(7).fillna(0.0) * 100.0
    df["monthly_change_pct"] = df["price"].pct_change(30).fillna(0.0) * 100.0

    df["ema_365"] = df["price"].ewm(span=365, adjust=False, min_periods=1).mean()
    df["sma_200"] = df["price"].rolling(window=200, min_periods=20).mean().bfill().ffill()
    df["sma_365"] = df["price"].rolling(window=365, min_periods=20).mean().bfill().ffill()

    df["price_vs_ema_pct"] = ((df["price"] - df["ema_365"]) / df["ema_365"]) * 100.0
    df["mvrv_proxy"] = df["price"] / df["sma_365"]
    df["mayer_multiple"] = df["price"] / df["sma_200"]

    rolling_mean = df["mvrv_proxy"].rolling(window=180, min_periods=20).mean().bfill().ffill()
    rolling_std = df["mvrv_proxy"].rolling(window=180, min_periods=20).std().bfill().ffill()
    rolling_std = rolling_std.replace(0.0, np.nan).bfill().ffill().fillna(1.0)
    df["mvrv_zscore"] = ((df["mvrv_proxy"] - rolling_mean) / rolling_std).clip(-4.0, 4.0)

    daily_return = df["price"].pct_change().fillna(0.0)
    rv_30 = daily_return.rolling(window=30, min_periods=5).std().bfill().ffill().fillna(0.02)

    df["rup"] = (0.80 + (1.35 * (df["mvrv_proxy"] - 1.0))).clip(0.0, 3.0)
    df["sopr"] = (1.0 + (2.1 * daily_return)).clip(0.85, 1.20)

    fng = 50.0 + (0.72 * df["weekly_change_pct"]) + (0.38 * df["monthly_change_pct"]) - (260.0 * rv_30)
    df["fear_and_greed"] = fng.clip(5.0, 95.0)

    base_interest = _safe_float(macro_baseline.get("interest_rate"), 3.5)
    base_m2 = _safe_float(macro_baseline.get("m2_yoy"), 5.0)
    base_infl = _safe_float(macro_baseline.get("inflation_yoy"), 3.0)

    df["interest_rate"] = (base_interest + (1.8 * rv_30)).clip(0.5, 10.0)
    df["m2_yoy"] = (base_m2 - (5.5 * rv_30)).clip(-8.0, 15.0)
    df["inflation_yoy"] = (base_infl + (2.3 * rv_30)).clip(0.0, 12.0)
    df["funding_rate"] = (0.0045 + (0.0006 * df["weekly_change_pct"]) - (0.03 * rv_30)).clip(-0.05, 0.08)

    rows: list[dict] = []
    for date_idx, row in df.iterrows():
        date_str = date_idx.strftime("%Y-%m-%d")
        seasonality_status = seasonality.get_seasonality(date_str)["status"]

        is_bull = bool(row["price"] > row["ema_365"])
        is_derivatives_risk = bool(row["funding_rate"] > 0.03)
        is_high_vol = bool(abs(row["daily_change_pct"]) > 4.0)

        rows.append(
            {
                "timestamp": f"{date_str}T00:00:00",
                "market_cycle_phase": _phase_for_date(cycle, date_idx.to_pydatetime()),
                "market_data": {
                    "current_price": float(row["price"]),
                    "daily_change_pct": float(row["daily_change_pct"]),
                    "weekly_change_pct": float(row["weekly_change_pct"]),
                    "monthly_change_pct": float(row["monthly_change_pct"]),
                    "ema_365": float(row["ema_365"]),
                    "price_vs_ema_pct": float(row["price_vs_ema_pct"]),
                },
                "metrics": {
                    "mvrv": float(row["mvrv_proxy"]),
                    "mvrv_zscore": float(row["mvrv_zscore"]),
                    "sopr": float(row["sopr"]),
                    "rup": float(row["rup"]),
                    "mayer_multiple": float(row["mayer_multiple"]),
                    "fear_and_greed": float(row["fear_and_greed"]),
                    "interest_rate": float(row["interest_rate"]),
                    "m2_yoy": float(row["m2_yoy"]),
                    "inflation_yoy": float(row["inflation_yoy"]),
                    "funding_rate": float(row["funding_rate"]),
                },
                "flags": {
                    "is_accumulation": bool((row["rup"] < 0.60) and (row["mvrv_proxy"] < 1.2) and (row["sopr"] < 1.0)),
                    "is_overheated": bool((row["mayer_multiple"] > 2.30) or (row["mvrv_zscore"] > 2.0)),
                    "is_fear_extreme": bool(row["fear_and_greed"] < 15.0),
                    "is_greed_extreme": bool(row["fear_and_greed"] > 80.0),
                    "is_liquidity_good": bool((row["m2_yoy"] > 5.0) or (row["interest_rate"] < 2.0)),
                    "is_inflation_high": bool(row["inflation_yoy"] > 3.0),
                    "is_inflation_falling": bool(row["daily_change_pct"] < 0.0),
                    "is_bull_trend": is_bull,
                    "is_derivatives_risk": is_derivatives_risk,
                    "is_volatility_opportunity": bool((row["daily_change_pct"] < -5.0) and is_bull),
                    "is_positive_seasonality": seasonality_status in {"BULLISH", "VERY BULLISH"},
                    "is_high_corr_spx": bool((not is_bull) and is_high_vol),
                    "is_high_corr_gold": bool(is_bull and is_high_vol and (row["m2_yoy"] < 1.0)),
                },
            }
        )

    return rows


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


def run_stochastic_paths(
    simulated_prices: np.ndarray,
    start_date: datetime,
    macro_baseline: dict,
    simulator: PortfolioSimulator,
) -> pd.DataFrame:
    rows: list[dict] = []
    specs = model_specs()

    for path_id in range(simulated_prices.shape[0]):
        synthetic_data = build_synthetic_daily_data(
            price_path=simulated_prices[path_id],
            start_date=start_date,
            macro_baseline=macro_baseline,
        )

        bnh = buy_and_hold_metrics(synthetic_data)
        rows.append(
            {
                "path_id": path_id,
                "model": "buy_and_hold",
                "total_return_pct": bnh["total_return_pct"],
                "cagr_pct": bnh["cagr_pct"],
                "max_drawdown_pct": bnh["max_drawdown_pct"],
                "sharpe": bnh["sharpe"],
                "trades": 0,
                "final_equity": bnh["final_equity"],
            }
        )

        for model_name, scorer, manager in specs:
            result = simulator.run(model_name, scorer, manager, synthetic_data)
            rows.append(
                {
                    "path_id": path_id,
                    "model": model_name,
                    "total_return_pct": result.total_return_pct,
                    "cagr_pct": result.cagr_pct,
                    "max_drawdown_pct": result.max_drawdown_pct,
                    "sharpe": result.sharpe,
                    "trades": result.trades,
                    "final_equity": result.final_equity,
                }
            )

    return pd.DataFrame(rows)


def summarize_stochastic_results(path_df: pd.DataFrame) -> pd.DataFrame:
    non_bnh = path_df[path_df["model"] != "buy_and_hold"].copy()
    bnh = path_df[path_df["model"] == "buy_and_hold"][["path_id", "total_return_pct"]].rename(
        columns={"total_return_pct": "bnh_return_pct"}
    )
    merged = non_bnh.merge(bnh, on="path_id", how="left")

    rows = []
    for model_name, group in merged.groupby("model", sort=False):
        ret = group["total_return_pct"].astype(float)
        dd = group["max_drawdown_pct"].astype(float)
        sharpe = group["sharpe"].astype(float)

        var_95 = float(np.percentile(ret, 5))
        cvar_95 = float(ret[ret <= var_95].mean()) if (ret <= var_95).any() else var_95

        rows.append(
            {
                "model": model_name,
                "paths": int(len(group)),
                "mean_return_pct": round(float(ret.mean()), 2),
                "std_return_pct": round(float(ret.std(ddof=1)), 2),
                "var_95_return_pct": round(var_95, 2),
                "cvar_95_return_pct": round(cvar_95, 2),
                "mean_sharpe": round(float(sharpe.mean()), 3),
                "mean_max_drawdown_pct": round(float(dd.mean()), 2),
                "worst_drawdown_pct": round(float(dd.min()), 2),
                "prob_positive_return": round(float((ret > 0).mean()), 4),
                "prob_beat_bnh": round(float((group["total_return_pct"] > group["bnh_return_pct"]).mean()), 4),
                "mean_trades": round(float(group["trades"].mean()), 1),
            }
        )

    summary = pd.DataFrame(rows)
    if not summary.empty:
        summary = summary.sort_values(by=["mean_return_pct", "mean_sharpe"], ascending=False)
    return summary


def build_sensitivity_surface(
    params: dict,
    s0: float,
    start_date: datetime,
    macro_baseline: dict,
) -> pd.DataFrame:
    simulator = PortfolioSimulator(trading_cost_bps=COST_BPS, annual_debt_rate=ANNUAL_DEBT_RATE)

    rows: list[dict] = []
    scorer = QuantScorer(mode="legacy")
    manager = PortfolioManager(min_trade_usd=20.0, cooldown_days=1)

    seed_base = 10_000
    for i, drift_scale in enumerate(GRID_DRIFT_SCALES):
        for j, vol_scale in enumerate(GRID_VOL_SCALES):
            prices, _ = simulate_regime_jump_diffusion(
                params=params,
                s0=s0,
                n_paths=GRID_PATHS,
                horizon_days=GRID_HORIZON_DAYS,
                seed=seed_base + (100 * i) + j,
                drift_scale=float(drift_scale),
                vol_scale=float(vol_scale),
            )

            returns = []
            drawdowns = []
            for k in range(prices.shape[0]):
                synthetic_data = build_synthetic_daily_data(
                    price_path=prices[k],
                    start_date=start_date,
                    macro_baseline=macro_baseline,
                )
                result = simulator.run("production_legacy_cooldown1", scorer, manager, synthetic_data)
                returns.append(result.total_return_pct)
                drawdowns.append(result.max_drawdown_pct)

            rows.append(
                {
                    "drift_scale": float(drift_scale),
                    "vol_scale": float(vol_scale),
                    "mean_return_pct": float(np.mean(returns)),
                    "median_return_pct": float(np.median(returns)),
                    "mean_max_drawdown_pct": float(np.mean(drawdowns)),
                }
            )

    return pd.DataFrame(rows)


def save_fan_chart(simulated_prices: np.ndarray, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    days = np.arange(simulated_prices.shape[1])
    quantiles = np.quantile(simulated_prices, [0.05, 0.25, 0.50, 0.75, 0.95], axis=0)

    fig = go.Figure()
    for i in range(min(70, simulated_prices.shape[0])):
        fig.add_trace(
            go.Scatter(
                x=days,
                y=simulated_prices[i],
                mode="lines",
                line={"color": "rgba(6, 87, 204, 0.08)", "width": 1},
                showlegend=False,
            )
        )

    fig.add_trace(
        go.Scatter(
            x=days,
            y=quantiles[4],
            mode="lines",
            line={"color": "rgba(226, 149, 1, 0.6)", "width": 1},
            name="P95",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=days,
            y=quantiles[0],
            mode="lines",
            line={"color": "rgba(226, 149, 1, 0.6)", "width": 1},
            fill="tonexty",
            fillcolor="rgba(255, 191, 105, 0.20)",
            name="P05-P95",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=days,
            y=quantiles[3],
            mode="lines",
            line={"color": "rgba(19, 142, 49, 0.8)", "width": 1},
            name="P75",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=days,
            y=quantiles[1],
            mode="lines",
            line={"color": "rgba(19, 142, 49, 0.8)", "width": 1},
            fill="tonexty",
            fillcolor="rgba(80, 220, 120, 0.20)",
            name="P25-P75",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=days,
            y=quantiles[2],
            mode="lines",
            line={"color": "#c1121f", "width": 3},
            name="Mediana",
        )
    )

    fig.update_layout(
        title="Monte Carlo Fan Chart - Regime-Switching Jump Diffusion",
        template="plotly_white",
        xaxis_title="Dias simulados",
        yaxis_title="Preco BTC (USD)",
        width=1200,
        height=700,
    )
    fig.write_html(output_path, include_plotlyjs="cdn")


def save_3d_surface(grid_df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pivot = grid_df.pivot(index="vol_scale", columns="drift_scale", values="mean_return_pct")
    x = pivot.columns.to_numpy(dtype=float)
    y = pivot.index.to_numpy(dtype=float)
    z = pivot.to_numpy(dtype=float)

    fig = go.Figure(
        data=[
            go.Surface(
                x=x,
                y=y,
                z=z,
                colorscale=[
                    [0.0, "#14213d"],
                    [0.4, "#1f78b4"],
                    [0.7, "#fca311"],
                    [1.0, "#d00000"],
                ],
                colorbar={"title": "Retorno medio (%)"},
            )
        ]
    )

    fig.update_layout(
        title="Superficie 3D de Sensibilidade: Drift x Volatilidade",
        template="plotly_white",
        width=1200,
        height=800,
        scene={
            "xaxis_title": "Escala de Drift",
            "yaxis_title": "Escala de Volatilidade",
            "zaxis_title": "Retorno medio do modelo (%)",
            "camera": {"eye": {"x": 1.55, "y": 1.35, "z": 0.85}},
        },
    )

    fig.write_html(output_path, include_plotlyjs="cdn")


def save_3d_scatter(path_results: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    non_bnh = path_results[path_results["model"] != "buy_and_hold"].copy()

    fig = px.scatter_3d(
        non_bnh,
        x="max_drawdown_pct",
        y="sharpe",
        z="total_return_pct",
        color="model",
        size=np.maximum(non_bnh["trades"].to_numpy(dtype=float), 1.0),
        size_max=12,
        opacity=0.72,
        color_discrete_sequence=["#005f73", "#ee9b00", "#bb3e03", "#9b2226"],
        title="Nuvem 3D de resultados estocasticos por caminho",
    )

    fig.update_layout(
        template="plotly_white",
        width=1200,
        height=800,
        legend_title_text="Modelo",
        scene={
            "xaxis_title": "Max Drawdown (%)",
            "yaxis_title": "Sharpe",
            "zaxis_title": "Retorno total (%)",
            "camera": {"eye": {"x": 1.2, "y": -1.4, "z": 0.9}},
        },
    )

    fig.write_html(output_path, include_plotlyjs="cdn")


def save_regime_transition_heatmap(params: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    matrix = np.array(params["transition_matrix"], dtype=float)
    labels = ["Low Vol", "Mid Vol", "High Vol"]

    fig = go.Figure(
        data=[
            go.Heatmap(
                z=matrix,
                x=labels,
                y=labels,
                text=np.round(matrix, 3),
                texttemplate="%{text}",
                colorscale="YlGnBu",
                zmin=0,
                zmax=1,
            )
        ]
    )

    fig.update_layout(
        title="Matriz de transicao de regimes (estimada)",
        template="plotly_white",
        xaxis_title="Proximo regime",
        yaxis_title="Regime atual",
        width=950,
        height=760,
    )

    fig.write_html(output_path, include_plotlyjs="cdn")


def write_report(
    params: dict,
    summary_df: pd.DataFrame,
    path_results: pd.DataFrame,
    grid_df: pd.DataFrame,
    figures: dict,
    n_paths: int,
    horizon_days: int,
) -> None:
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# Stochastic Calculus Validation")
    lines.append("")
    lines.append(f"Generated on: **{datetime.now().strftime('%Y-%m-%d')}**")
    lines.append("")
    lines.append("## Stochastic Model")
    lines.append("")
    lines.append("Validation is built on a regime-switching jump-diffusion process:")
    lines.append("")
    lines.append("$$")
    lines.append("dS_t = \\mu_{r_t} S_t \\, dt + \\sigma_{r_t} S_t \\, dW_t + S_t (e^{J_t} - 1) \\, dN_t")
    lines.append("$$")
    lines.append("")
    lines.append("where $r_t$ is a Markov regime state, $W_t$ is Brownian motion, and $N_t$ is a Poisson jump process.")
    lines.append("")
    lines.append("Estimated annualized parameters from historical returns:")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("| :--- | ---: |")
    lines.append(f"| Historical drift $\\mu$ | {params['historical_mu']:+.4f} |")
    lines.append(f"| Historical volatility $\\sigma$ | {params['historical_sigma']:.4f} |")
    lines.append(f"| Jump intensity $\\lambda$ | {params['jump_lambda']:.4f} |")
    lines.append(f"| Jump mean $E[J]$ | {params['jump_mu']:+.5f} |")
    lines.append(f"| Jump std $\\sigma_J$ | {params['jump_sigma']:.5f} |")
    lines.append("")
    lines.append("Regime annualized drifts and vols:")
    lines.append("")
    lines.append("| Regime | Drift | Volatility |")
    lines.append("| :--- | ---: | ---: |")
    for idx, (mu, sigma) in enumerate(zip(params["mu_regimes"], params["sigma_regimes"])):
        lines.append(f"| {idx} | {mu:+.4f} | {sigma:.4f} |")

    lines.append("")
    lines.append("## Monte Carlo Setup")
    lines.append("")
    lines.append(f"- Paths: `{n_paths}`")
    lines.append(f"- Horizon: `{horizon_days}` days")
    lines.append(f"- Cost model: `{COST_BPS:.2f}` bps per side")
    lines.append(f"- Debt carry: `{ANNUAL_DEBT_RATE:.2%}` annual")
    lines.append("")

    lines.append("## Model Robustness Under Stochastic Paths")
    lines.append("")
    lines.append("| Model | Paths | Mean Return | Std Return | VaR 95% | CVaR 95% | Mean Sharpe | Mean Max DD | Worst DD | P(Return>0) | P(Beat BnH) | Mean Trades |")
    lines.append("| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for _, row in summary_df.iterrows():
        lines.append(
            "| {model} | {paths} | {mean_return_pct:+.2f}% | {std_return_pct:.2f}% | {var_95_return_pct:+.2f}% | {cvar_95_return_pct:+.2f}% | {mean_sharpe:.3f} | {mean_max_drawdown_pct:.2f}% | {worst_drawdown_pct:.2f}% | {prob_positive_return:.2%} | {prob_beat_bnh:.2%} | {mean_trades:.1f} |".format(
                **row.to_dict()
            )
        )

    lines.append("")
    lines.append("## Sensitivity Surface")
    lines.append("")
    lines.append("The 3D surface maps expected production-model return as drift and volatility are jointly perturbed.")
    lines.append("")
    lines.append("| Drift Scale | Vol Scale | Mean Return | Median Return | Mean Max DD |")
    lines.append("| ---: | ---: | ---: | ---: | ---: |")
    for _, row in grid_df.sort_values(["drift_scale", "vol_scale"]).iterrows():
        lines.append(
            "| {drift_scale:.2f} | {vol_scale:.2f} | {mean_return_pct:+.2f}% | {median_return_pct:+.2f}% | {mean_max_drawdown_pct:.2f}% |".format(
                **row.to_dict()
            )
        )

    lines.append("")
    lines.append("## Figures")
    lines.append("")
    lines.append(f"- Fan chart: `{figures['fan_chart']}`")
    lines.append(f"- 3D surface: `{figures['surface_3d']}`")
    lines.append(f"- 3D scatter: `{figures['scatter_3d']}`")
    lines.append(f"- Regime heatmap: `{figures['heatmap']}`")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Synthetic features are rebuilt path-by-path, then scored and executed by the same strategy code used in backtests.")
    lines.append("- Results are scenario evidence and should be combined with walk-forward gate decisions before production promotion.")

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def run_stochastic_validation() -> None:
    rng = np.random.default_rng(SEED)

    daily_data = _load_daily_data()
    prices = _price_series(daily_data)

    params = estimate_regime_jump_parameters(prices)
    s0 = float(prices.iloc[-1])

    simulated_prices, _ = simulate_regime_jump_diffusion(
        params=params,
        s0=s0,
        n_paths=N_PATHS,
        horizon_days=HORIZON_DAYS,
        seed=int(rng.integers(0, 10_000_000)),
    )

    macro_baseline = _macro_baseline(daily_data)
    start_date = prices.index[-1].to_pydatetime() + timedelta(days=1)

    simulator = PortfolioSimulator(trading_cost_bps=COST_BPS, annual_debt_rate=ANNUAL_DEBT_RATE)
    path_results = run_stochastic_paths(
        simulated_prices=simulated_prices,
        start_date=start_date,
        macro_baseline=macro_baseline,
        simulator=simulator,
    )

    summary_df = summarize_stochastic_results(path_results)
    grid_df = build_sensitivity_surface(
        params=params,
        s0=s0,
        start_date=start_date,
        macro_baseline=macro_baseline,
    )

    PATH_RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    PATH_RESULTS_CSV.write_text(path_results.to_csv(index=False), encoding="utf-8")
    SUMMARY_CSV.write_text(summary_df.to_csv(index=False), encoding="utf-8")
    GRID_CSV.write_text(grid_df.to_csv(index=False), encoding="utf-8")

    fan_chart_path = FIGURES_DIR / "stochastic_fan_chart.html"
    surface_path = FIGURES_DIR / "stochastic_surface_3d.html"
    scatter_path = FIGURES_DIR / "stochastic_scatter_3d.html"
    heatmap_path = FIGURES_DIR / "regime_transition_heatmap.html"

    save_fan_chart(simulated_prices, fan_chart_path)
    save_3d_surface(grid_df, surface_path)
    save_3d_scatter(path_results, scatter_path)
    save_regime_transition_heatmap(params, heatmap_path)

    figures = {
        "fan_chart": str(fan_chart_path),
        "surface_3d": str(surface_path),
        "scatter_3d": str(scatter_path),
        "heatmap": str(heatmap_path),
    }

    write_report(
        params=params,
        summary_df=summary_df,
        path_results=path_results,
        grid_df=grid_df,
        figures=figures,
        n_paths=N_PATHS,
        horizon_days=HORIZON_DAYS,
    )

    print("Stochastic calculus validation completed.")
    print(summary_df)


if __name__ == "__main__":
    run_stochastic_validation()
