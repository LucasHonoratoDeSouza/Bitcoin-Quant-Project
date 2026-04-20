from __future__ import annotations

from dataclasses import dataclass
import json
import math

import numpy as np

from src.strategy.legacy_score import LegacyQuantScorer
from src.utils.project_paths import PROCESSED_DATA_DIR


@dataclass(frozen=True)
class FeatureStat:
    center: float
    scale: float
    sample_size: int


class HistoricalFeatureCalibrator:
    """
    Builds robust feature distributions from processed daily files.

    This allows score normalization to adapt as BTC regimes drift over time,
    instead of relying on static hardcoded boundaries.
    """

    DEFAULT_STATS = {
        "mvrv_zscore": FeatureStat(0.0, 1.20, 0),
        "mayer_multiple": FeatureStat(1.20, 0.35, 0),
        "rup": FeatureStat(1.00, 0.55, 0),
        "sopr": FeatureStat(1.00, 0.06, 0),
        "fear_and_greed": FeatureStat(50.0, 16.0, 0),
        "interest_rate": FeatureStat(3.50, 1.20, 0),
        "m2_yoy": FeatureStat(5.00, 3.00, 0),
        "inflation_yoy": FeatureStat(3.00, 1.20, 0),
        "funding_rate": FeatureStat(0.005, 0.010, 0),
        "price_vs_ema_pct": FeatureStat(15.0, 22.0, 0),
        "weekly_change_pct": FeatureStat(1.0, 7.0, 0),
        "monthly_change_pct": FeatureStat(3.0, 17.0, 0),
        "realized_vol_30d": FeatureStat(0.65, 0.20, 0),
        "realized_vol_90d": FeatureStat(0.70, 0.18, 0),
        "momentum_63d": FeatureStat(0.06, 0.20, 0),
        "drawdown_180d": FeatureStat(-0.22, 0.16, 0),
        "trend_tscore_90d": FeatureStat(0.0, 1.80, 0),
    }

    def __init__(self, lookback_files: int = 900, min_samples: int = 80, max_file_date: str | None = None):
        self.lookback_files = lookback_files
        self.min_samples = min_samples
        self.max_file_date = max_file_date
        self.feature_stats: dict[str, FeatureStat] = dict(self.DEFAULT_STATS)
        self.cycle_priors: dict[str, float] = {}
        self._fit_from_processed_history()

    def _safe_float(self, value, default=0.0):
        try:
            if value is None:
                return float(default)
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    def _extract_date_from_filename(self, file_path) -> str | None:
        name = file_path.stem  # processed_data_YYYY-MM-DD
        if not name.startswith("processed_data_"):
            return None
        raw_date = name.replace("processed_data_", "", 1)
        if len(raw_date) != 10:
            return None
        return raw_date

    def _fit_from_processed_history(self):
        files = sorted(PROCESSED_DATA_DIR.glob("processed_data_*.json"))
        if self.max_file_date:
            filtered_files = []
            for file_path in files:
                file_date = self._extract_date_from_filename(file_path)
                if file_date is None:
                    continue
                if file_date <= self.max_file_date:
                    filtered_files.append(file_path)
            files = filtered_files

        files = files[-self.lookback_files :]
        if not files:
            return

        feature_values: dict[str, list[float]] = {key: [] for key in self.DEFAULT_STATS}
        cycle_records: list[dict] = []

        for file_path in files:
            try:
                payload = json.loads(file_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            market = payload.get("market_data", {})
            metrics = payload.get("metrics", {})
            cycle = payload.get("market_cycle_phase", "Unknown")
            timestamp = payload.get("timestamp", "")

            row = {
                "mvrv_zscore": metrics.get("mvrv_zscore"),
                "mayer_multiple": metrics.get("mayer_multiple"),
                "rup": metrics.get("rup"),
                "sopr": metrics.get("sopr"),
                "fear_and_greed": metrics.get("fear_and_greed"),
                "interest_rate": metrics.get("interest_rate"),
                "m2_yoy": metrics.get("m2_yoy"),
                "inflation_yoy": metrics.get("inflation_yoy"),
                "funding_rate": metrics.get("funding_rate"),
                "price_vs_ema_pct": market.get("price_vs_ema_pct"),
                "weekly_change_pct": market.get("weekly_change_pct"),
                "monthly_change_pct": market.get("monthly_change_pct"),
                "realized_vol_30d": metrics.get("realized_vol_30d"),
                "realized_vol_90d": metrics.get("realized_vol_90d"),
                "momentum_63d": metrics.get("momentum_63d"),
                "drawdown_180d": metrics.get("drawdown_180d"),
                "trend_tscore_90d": metrics.get("trend_tscore_90d"),
            }

            for feature_name, raw_value in row.items():
                value = self._safe_float(raw_value, default=float("nan"))
                if math.isfinite(value):
                    feature_values[feature_name].append(value)

            price = self._safe_float(market.get("current_price"), default=float("nan"))
            if math.isfinite(price) and price > 0:
                cycle_records.append(
                    {
                        "timestamp": str(timestamp),
                        "cycle": str(cycle),
                        "price": float(price),
                    }
                )

        for feature_name, values in feature_values.items():
            stat = self._build_robust_stat(values)
            if stat is not None:
                self.feature_stats[feature_name] = stat

        self.cycle_priors = self._build_cycle_priors(cycle_records)

    def _build_robust_stat(self, values: list[float]) -> FeatureStat | None:
        if len(values) < self.min_samples:
            return None

        arr = np.asarray(values, dtype=float)
        arr = arr[np.isfinite(arr)]
        if arr.size < self.min_samples:
            return None

        center = float(np.median(arr))
        mad = float(np.median(np.abs(arr - center)))

        if mad > 1e-9:
            scale = 1.4826 * mad
        else:
            q75, q25 = np.percentile(arr, [75, 25])
            iqr = float(q75 - q25)
            scale = iqr / 1.349 if iqr > 1e-9 else float(np.std(arr, ddof=1))

        scale = max(float(scale), 1e-3)
        return FeatureStat(center=center, scale=scale, sample_size=int(arr.size))

    def _build_cycle_priors(self, cycle_records: list[dict], horizon_days: int = 30) -> dict[str, float]:
        if len(cycle_records) <= horizon_days + 5:
            return {}

        ordered = sorted(cycle_records, key=lambda row: row["timestamp"])
        returns_by_cycle: dict[str, list[float]] = {}

        for idx in range(len(ordered) - horizon_days):
            current = ordered[idx]
            future = ordered[idx + horizon_days]
            p0 = float(current["price"])
            p1 = float(future["price"])
            if p0 <= 0 or p1 <= 0:
                continue

            forward_return = (p1 / p0) - 1.0
            returns_by_cycle.setdefault(current["cycle"], []).append(forward_return)

        cycle_priors = {}
        for cycle, values in returns_by_cycle.items():
            arr = np.asarray(values, dtype=float)
            arr = arr[np.isfinite(arr)]
            if arr.size < 25:
                continue

            mean_ret = float(np.mean(arr))
            std_ret = float(np.std(arr, ddof=1))
            if std_ret <= 1e-9:
                continue

            t_stat = mean_ret / (std_ret / math.sqrt(arr.size))
            prior_signal = math.tanh(t_stat / 3.0)
            cycle_priors[cycle] = max(-1.0, min(1.0, prior_signal))

        return cycle_priors

    def get_feature_stat(self, feature_name: str) -> FeatureStat:
        return self.feature_stats.get(feature_name, self.DEFAULT_STATS[feature_name])

    def robust_zscore(self, feature_name: str, value: float) -> tuple[float, float]:
        stat = self.get_feature_stat(feature_name)
        if not math.isfinite(value):
            return 0.0, 0.0

        z = (value - stat.center) / stat.scale
        z = max(-5.0, min(5.0, z))

        sample_reliability = min(1.0, stat.sample_size / 240.0)
        tail_penalty = 1.0 / (1.0 + max(0.0, abs(z) - 2.5))
        reliability = max(0.05, min(1.0, 0.15 + (0.85 * sample_reliability * tail_penalty)))
        return z, reliability

    def cycle_prior(self, cycle_name: str) -> float:
        if cycle_name in self.cycle_priors:
            return self.cycle_priors[cycle_name]

        fallback = {
            "Accumulation": 0.45,
            "Pre-Halving Rally": 0.50,
            "Post-Halving Expansion": 0.15,
            "Bear Market / Distribution": -0.50,
        }
        return fallback.get(cycle_name, 0.0)


class AdvancedQuantScorer:
    """
    Regime-aware signal engine.

    Robust quantitative engine with adaptive normalization and uncertainty control.

    Core principles:
    - Robust statistics (median/MAD) instead of fixed static thresholds.
    - Bayesian posterior over bull/bear regime with data-driven cycle priors.
    - Explicit uncertainty penalty to reduce exposure under conflicting evidence.
    """

    def __init__(self, lookback_files: int = 900, calibrator_max_date: str | None = None):
        self._calibrator = HistoricalFeatureCalibrator(
            lookback_files=lookback_files,
            max_file_date=calibrator_max_date,
        )

    def _safe_float(self, value, default=0.0):
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def _clip(self, value, low=-1.0, high=1.0):
        return max(low, min(high, value))

    def _sigmoid(self, x):
        x = self._clip(x, -60.0, 60.0)
        return 1.0 / (1.0 + math.exp(-x))

    def _extract_feature(self, data: dict, feature_name: str):
        metrics = data.get("metrics", {})
        market = data.get("market_data", {})

        market_features = {
            "price_vs_ema_pct",
            "weekly_change_pct",
            "monthly_change_pct",
        }

        if feature_name in market_features:
            return market.get(feature_name)
        return metrics.get(feature_name)

    def _feature_signal(self, data: dict, feature_name: str, direction: float) -> dict:
        value = self._safe_float(self._extract_feature(data, feature_name), default=float("nan"))
        if not math.isfinite(value):
            return {
                "signal": 0.0,
                "z": 0.0,
                "reliability": 0.0,
                "value": None,
            }

        z, reliability = self._calibrator.robust_zscore(feature_name, value)
        signed_z = direction * z
        signal = math.tanh(signed_z / 1.75)

        return {
            "signal": self._clip(signal),
            "z": float(z),
            "reliability": float(reliability),
            "value": float(value),
        }

    def _aggregate_block(self, data: dict, specs: list[tuple[str, float, float]]) -> dict:
        weighted_signal_sum = 0.0
        weighted_effective_sum = 0.0
        base_weight_sum = 0.0
        components = {}

        for feature_name, weight, direction in specs:
            stats = self._feature_signal(data, feature_name, direction)
            effective_weight = weight * stats["reliability"]

            weighted_signal_sum += effective_weight * stats["signal"]
            weighted_effective_sum += effective_weight
            base_weight_sum += weight

            components[feature_name] = {
                "value": stats["value"],
                "z": round(stats["z"], 3),
                "signal": round(stats["signal"], 3),
                "reliability": round(stats["reliability"], 3),
            }

        score = weighted_signal_sum / weighted_effective_sum if weighted_effective_sum > 1e-9 else 0.0
        coverage = weighted_effective_sum / base_weight_sum if base_weight_sum > 1e-9 else 0.0

        return {
            "score": self._clip(score),
            "coverage": self._clip(coverage, 0.0, 1.0),
            "components": components,
        }

    def _entropy_uncertainty(self, probability: float) -> float:
        p = self._clip(probability, 1e-6, 1.0 - 1e-6)
        entropy = -((p * math.log(p)) + ((1.0 - p) * math.log(1.0 - p))) / math.log(2.0)
        return self._clip(entropy, 0.0, 1.0)

    def _long_term_blocks(self, data: dict) -> dict:
        valuation = self._aggregate_block(
            data,
            [
                ("mvrv_zscore", 0.35, -1.0),
                ("mayer_multiple", 0.25, -1.0),
                ("rup", 0.20, -1.0),
                ("sopr", 0.20, -1.0),
            ],
        )
        macro = self._aggregate_block(
            data,
            [
                ("m2_yoy", 0.35, +1.0),
                ("interest_rate", 0.30, -1.0),
                ("inflation_yoy", 0.20, -1.0),
                ("funding_rate", 0.15, -1.0),
            ],
        )
        trend = self._aggregate_block(
            data,
            [
                ("price_vs_ema_pct", 0.30, -1.0),
                ("trend_tscore_90d", 0.30, +1.0),
                ("momentum_63d", 0.20, +1.0),
                ("drawdown_180d", 0.20, -1.0),
            ],
        )
        volatility = self._aggregate_block(
            data,
            [
                ("realized_vol_30d", 0.60, -1.0),
                ("realized_vol_90d", 0.40, -1.0),
            ],
        )

        return {
            "valuation": valuation,
            "macro": macro,
            "trend": trend,
            "volatility": volatility,
        }

    def _calc_long_term_quant(self, data: dict) -> tuple[dict, dict]:
        flags = data.get("flags", {})
        cycle = data.get("market_cycle_phase", "Unknown")

        blocks = self._long_term_blocks(data)
        valuation = blocks["valuation"]["score"]
        macro = blocks["macro"]["score"]
        trend = blocks["trend"]["score"]
        volatility = blocks["volatility"]["score"]

        trend_bias = 0.18 if flags.get("is_bull_trend") else -0.18
        season_bias = 0.08 if flags.get("is_positive_seasonality") else -0.05
        cycle_prior_signal = self._calibrator.cycle_prior(cycle)

        prior_logit = (0.90 * cycle_prior_signal) + (0.70 * trend_bias) + (0.40 * season_bias)
        likelihood_logit = (1.25 * valuation) + (1.10 * macro) + (0.80 * trend)

        if flags.get("is_derivatives_risk"):
            likelihood_logit -= 0.35
        if flags.get("is_overheated"):
            likelihood_logit -= 0.55
        if flags.get("is_accumulation"):
            likelihood_logit += 0.35
        if flags.get("is_volatility_opportunity"):
            likelihood_logit += 0.15
        if flags.get("is_high_corr_spx") and not flags.get("is_liquidity_good"):
            likelihood_logit -= 0.20
        if flags.get("is_inflation_high") and not flags.get("is_liquidity_good"):
            likelihood_logit -= 0.25

        regime_linear = prior_logit + likelihood_logit
        bull_probability = self._sigmoid(regime_linear)
        regime_signal = (2.0 * bull_probability) - 1.0

        coverages = np.asarray(
            [
                blocks["valuation"]["coverage"],
                blocks["macro"]["coverage"],
                blocks["trend"]["coverage"],
            ],
            dtype=float,
        )
        coverage = float(np.mean(coverages)) if coverages.size else 0.0

        signal_vector = np.asarray([valuation, macro, trend, regime_signal], dtype=float)
        disagreement = float(np.std(signal_vector))
        entropy = self._entropy_uncertainty(bull_probability)
        uncertainty = self._clip((0.45 * entropy) + (0.35 * disagreement) + (0.20 * (1.0 - coverage)), 0.0, 1.0)

        volatility_pressure = max(0.0, -volatility)
        raw_edge = (0.45 * valuation) + (0.30 * macro) + (0.25 * regime_signal)
        risk_adjusted_edge = raw_edge - (0.35 * uncertainty) - (0.20 * volatility_pressure)

        final_lt = self._clip(math.tanh(1.55 * risk_adjusted_edge))

        details = {
            "regime_signal": regime_signal,
            "uncertainty": uncertainty,
            "coverage": coverage,
            "volatility_pressure": volatility_pressure,
            "blocks": blocks,
        }

        result = {
            "score": round(final_lt * 100.0, 2),
            "components": {
                "valuation": round(valuation, 3),
                "macro": round(macro, 3),
                "trend": round(trend, 3),
                "regime": round(regime_signal, 3),
                "bull_probability": round(bull_probability, 3),
                "uncertainty": round(uncertainty, 3),
                "coverage": round(coverage, 3),
                "volatility_pressure": round(volatility_pressure, 3),
                "cycle_prior_signal": round(cycle_prior_signal, 3),
            },
        }
        return result, details

    def _calc_medium_term_quant(self, data: dict, lt_details: dict) -> dict:
        flags = data.get("flags", {})

        momentum_block = self._aggregate_block(
            data,
            [
                ("weekly_change_pct", 0.35, +1.0),
                ("monthly_change_pct", 0.40, +1.0),
                ("trend_tscore_90d", 0.25, +1.0),
            ],
        )
        reversion_block = self._aggregate_block(
            data,
            [
                ("price_vs_ema_pct", 0.40, -1.0),
                ("fear_and_greed", 0.35, -1.0),
                ("drawdown_180d", 0.25, -1.0),
            ],
        )
        risk_block = self._aggregate_block(
            data,
            [
                ("funding_rate", 0.30, -1.0),
                ("realized_vol_30d", 0.45, -1.0),
                ("realized_vol_90d", 0.25, -1.0),
            ],
        )

        momentum = momentum_block["score"]
        reversion = reversion_block["score"]
        risk = risk_block["score"]

        trend_bias = 0.18 if flags.get("is_bull_trend") else -0.18
        regime_signal = self._clip(self._safe_float(lt_details.get("regime_signal"), 0.0))
        uncertainty_lt = self._clip(self._safe_float(lt_details.get("uncertainty"), 0.5), 0.0, 1.0)

        regime_alignment = (0.65 * regime_signal) + (0.35 * trend_bias)

        base_mt = (
            (0.50 * momentum)
            + (0.30 * reversion)
            + (0.20 * risk)
            + (0.25 * regime_alignment)
        )

        if flags.get("is_derivatives_risk"):
            base_mt -= 0.18
        if flags.get("is_volatility_opportunity") and regime_signal > 0:
            base_mt += 0.10

        coverages = np.asarray(
            [
                momentum_block["coverage"],
                reversion_block["coverage"],
                risk_block["coverage"],
            ],
            dtype=float,
        )
        coverage = float(np.mean(coverages)) if coverages.size else 0.0
        disagreement = abs(momentum - reversion)
        confidence = self._clip(
            (0.50 * coverage) + (0.30 * (1.0 - (disagreement / 2.0))) + (0.20 * (1.0 - uncertainty_lt)),
            0.12,
            1.0,
        )
        final_mt = self._clip(base_mt * (0.60 + (0.50 * confidence)))

        return {
            "score": round(final_mt * 100.0, 2),
            "components": {
                "momentum": round(momentum, 3),
                "reversion": round(reversion, 3),
                "risk": round(risk, 3),
                "regime_alignment": round(regime_alignment, 3),
                "confidence": round(confidence, 3),
                "coverage": round(coverage, 3),
            },
        }

    def _describe_score(self, score):
        if score >= 80:
            return "Extreme Bullish (Max Opportunity)"
        if score >= 50:
            return "Bullish (Favorable)"
        if score >= 20:
            return "Mildly Bullish"
        if score > -20:
            return "Neutral"
        if score > -50:
            return "Mildly Bearish"
        if score > -80:
            return "Bearish (Unfavorable)"
        return "Extreme Bearish (Max Risk)"

    def calculate_scores(self, data: dict) -> dict:
        lt, lt_details = self._calc_long_term_quant(data)
        mt = self._calc_medium_term_quant(data, lt_details)

        lt_score = lt["score"]
        mt_score = mt["score"]

        return {
            "scores": {
                "long_term": {
                    "value": lt_score,
                    "components": lt["components"],
                    "description": self._describe_score(lt_score),
                },
                "medium_term": {
                    "value": mt_score,
                    "components": mt["components"],
                    "description": self._describe_score(mt_score),
                },
            },
            "metadata": {
                "method": "robust_bayesian_quant_v2",
                "range": {
                    "min": -100,
                    "max": 100,
                    "neutral": 0,
                },
                "interpretation": {
                    "-100": "Maximum Bearish / Overvalued / Extreme Risk",
                    "0": "Neutral / Fair Value",
                    "100": "Maximum Bullish / Undervalued / Extreme Opportunity",
                },
            },
        }


class QuantScorer:
    """
    Production scorer facade.

    Modes:
    - legacy: backtest-approved default for production
    - advanced: robust quantitative model (adaptive + uncertainty-aware)
    - quant: alias for advanced
    - blend: convex combination of legacy and advanced outputs
    """

    def __init__(
        self,
        mode: str = "legacy",
        advanced_weight: float = 0.25,
        lookback_files: int = 900,
        calibrator_max_date: str | None = None,
    ):
        self.mode = mode
        self.advanced_weight = max(0.0, min(1.0, advanced_weight))
        self.lookback_files = lookback_files
        self.calibrator_max_date = calibrator_max_date
        self._legacy = LegacyQuantScorer()
        self._advanced: AdvancedQuantScorer | None = None

    def _get_advanced(self) -> AdvancedQuantScorer:
        if self._advanced is None:
            self._advanced = AdvancedQuantScorer(
                lookback_files=self.lookback_files,
                calibrator_max_date=self.calibrator_max_date,
            )
        return self._advanced

    def calculate_scores(self, data: dict) -> dict:
        if self.mode == "legacy":
            return self._legacy.calculate_scores(data)
        if self.mode in {"advanced", "quant"}:
            return self._get_advanced().calculate_scores(data)
        if self.mode == "blend":
            legacy_result = self._legacy.calculate_scores(data)
            advanced_result = self._get_advanced().calculate_scores(data)

            lw = 1.0 - self.advanced_weight
            aw = self.advanced_weight

            lt = (lw * legacy_result["scores"]["long_term"]["value"]) + (
                aw * advanced_result["scores"]["long_term"]["value"]
            )
            mt = (lw * legacy_result["scores"]["medium_term"]["value"]) + (
                aw * advanced_result["scores"]["medium_term"]["value"]
            )

            legacy_result["scores"]["long_term"]["value"] = round(lt, 2)
            legacy_result["scores"]["medium_term"]["value"] = round(mt, 2)
            return legacy_result

        raise ValueError(f"Unsupported scorer mode: {self.mode}")
