from __future__ import annotations

import math

from src.strategy.legacy_score import LegacyQuantScorer


class AdvancedQuantScorer:
    """
    Regime-aware signal engine.

    Keeps the public API compatible with the previous scorer while replacing
    fixed decision boundaries with smoother probabilistic transforms.
    """

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

    def _normalize(self, value, min_val, max_val, invert=False):
        value = self._safe_float(value, default=0.0)
        if math.isclose(max_val, min_val):
            return 0.0

        clamped = max(min_val, min(value, max_val))
        normalized = (clamped - min_val) / (max_val - min_val)
        score = (normalized * 2.0) - 1.0

        if invert:
            score = -score

        return self._clip(score)

    def _cycle_to_score(self, cycle):
        mapping = {
            "Accumulation": 0.70,
            "Pre-Halving Rally": 0.85,
            "Post-Halving Expansion": 0.35,
            "Bear Market / Distribution": -0.65,
        }
        return mapping.get(cycle, 0.0)

    def _calc_long_term_quant(self, data: dict) -> dict:
        metrics = data.get("metrics", {})
        flags = data.get("flags", {})
        cycle = data.get("market_cycle_phase", "Unknown")

        # Valuation block (slow-moving alpha sources).
        mvrv_signal = self._normalize(metrics.get("mvrv_zscore"), -2.5, 3.0, invert=True)
        mayer_signal = self._normalize(metrics.get("mayer_multiple"), 0.6, 2.6, invert=True)
        rup_signal = self._normalize(metrics.get("rup"), 0.0, 3.0, invert=True)
        sopr_signal = self._normalize(metrics.get("sopr"), 0.90, 1.15, invert=True)
        valuation = (
            (mvrv_signal * 0.40)
            + (mayer_signal * 0.25)
            + (rup_signal * 0.20)
            + (sopr_signal * 0.15)
        )

        # Macro/liquidity block.
        m2_signal = self._normalize(metrics.get("m2_yoy"), -5.0, 12.0)
        rate_signal = self._normalize(metrics.get("interest_rate"), 0.5, 6.0, invert=True)
        inflation_signal = self._normalize(metrics.get("inflation_yoy"), 1.0, 8.0, invert=True)
        macro = (m2_signal * 0.45) + (rate_signal * 0.35) + (inflation_signal * 0.20)

        trend_score = 1.0 if flags.get("is_bull_trend") else -1.0
        season_score = 0.25 if flags.get("is_positive_seasonality") else -0.10
        cycle_score = self._cycle_to_score(cycle)

        derivatives_penalty = -0.35 if flags.get("is_derivatives_risk") else 0.0
        overheating_penalty = -0.50 if flags.get("is_overheated") else 0.0
        inflation_penalty = -0.20 if flags.get("is_inflation_high") and not flags.get("is_liquidity_good") else 0.0

        regime_linear = (
            (0.60 * valuation)
            + (0.80 * macro)
            + (1.15 * trend_score)
            + (0.70 * cycle_score)
            + (0.40 * season_score)
            + derivatives_penalty
            + overheating_penalty
            + inflation_penalty
        )
        bull_probability = self._sigmoid(regime_linear)
        regime_signal = (2.0 * bull_probability) - 1.0

        final_lt = self._clip((valuation * 0.50) + (macro * 0.25) + (regime_signal * 0.25))

        return {
            "score": round(final_lt * 100.0, 2),
            "components": {
                "valuation": round(valuation, 3),
                "macro": round(macro, 3),
                "regime": round(regime_signal, 3),
                "bull_probability": round(bull_probability, 3),
            },
        }

    def _calc_medium_term_quant(self, data: dict) -> dict:
        metrics = data.get("metrics", {})
        market = data.get("market_data", {})
        flags = data.get("flags", {})

        weekly_change = self._safe_float(market.get("weekly_change_pct"), 0.0)
        monthly_change = self._safe_float(market.get("monthly_change_pct"), 0.0)
        extension = self._safe_float(market.get("price_vs_ema_pct"), 0.0)

        momentum_weekly = self._normalize(weekly_change, -20.0, 25.0)
        momentum_monthly = self._normalize(monthly_change, -35.0, 45.0)
        momentum = (momentum_weekly * 0.45) + (momentum_monthly * 0.55)

        pullback = self._normalize(extension, -35.0, 80.0, invert=True)
        sentiment = self._normalize(metrics.get("fear_and_greed"), 10.0, 90.0, invert=True)

        trend_dir = 1.0 if flags.get("is_bull_trend") else -1.0
        volatility_event = 0.25 if flags.get("is_volatility_opportunity") else 0.0
        derivatives_penalty = -0.30 if flags.get("is_derivatives_risk") else 0.0
        correlation_penalty = -0.20 if flags.get("is_high_corr_spx") and not flags.get("is_liquidity_good") else 0.0

        base_mt = (
            (0.35 * trend_dir)
            + (0.30 * momentum)
            + (0.20 * pullback)
            + (0.15 * sentiment)
            + volatility_event
            + derivatives_penalty
            + correlation_penalty
        )

        # Confidence attenuation avoids overtrading when trend and momentum disagree.
        disagreement = abs(trend_dir - momentum) / 2.0
        confidence = self._clip(1.0 - (0.45 * disagreement), 0.25, 1.0)
        final_mt = self._clip(base_mt * confidence)

        return {
            "score": round(final_mt * 100.0, 2),
            "components": {
                "trend": round(trend_dir, 3),
                "momentum": round(momentum, 3),
                "pullback": round(pullback, 3),
                "sentiment": round(sentiment, 3),
                "confidence": round(confidence, 3),
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
        lt = self._calc_long_term_quant(data)
        mt = self._calc_medium_term_quant(data)

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
    - advanced: research model (regime-aware probabilistic)
    - blend: convex combination of legacy and advanced outputs
    """

    def __init__(self, mode: str = "legacy", advanced_weight: float = 0.25):
        self.mode = mode
        self.advanced_weight = max(0.0, min(1.0, advanced_weight))
        self._legacy = LegacyQuantScorer()
        self._advanced = AdvancedQuantScorer()

    def calculate_scores(self, data: dict) -> dict:
        if self.mode == "legacy":
            return self._legacy.calculate_scores(data)
        if self.mode == "advanced":
            return self._advanced.calculate_scores(data)
        if self.mode == "blend":
            legacy_result = self._legacy.calculate_scores(data)
            advanced_result = self._advanced.calculate_scores(data)

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
