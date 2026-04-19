import math


class LegacyQuantScorer:
    """
    Baseline scorer preserved for backtest comparisons.
    """

    def _normalize(self, value, min_val, max_val, invert=False):
        if value is None:
            return 0.0

        clamped = max(min_val, min(value, max_val))
        normalized = (clamped - min_val) / (max_val - min_val)
        score = (normalized * 2) - 1

        if invert:
            score = -score

        return score

    def _calc_long_term_quant(self, data: dict) -> dict:
        metrics = data.get("metrics", {})
        cycle = data.get("market_cycle_phase", "Unknown")

        z_score = metrics.get("mvrv_zscore", 0.0)
        mvrv_score = self._normalize(z_score, -1.2, 2.5, invert=True)
        mm_score = self._normalize(metrics.get("mayer_multiple"), 0.6, 2.4, invert=True)
        rup_score = self._normalize(metrics.get("rup"), 0.0, 3.0, invert=True)

        onchain_score = (mvrv_score * 0.4) + (mm_score * 0.3) + (rup_score * 0.3)

        m2_score = self._normalize(metrics.get("m2_yoy"), 0.0, 10.0)
        ir_score = self._normalize(metrics.get("interest_rate"), 2.0, 5.0, invert=True)
        macro_score = (m2_score * 0.6) + (ir_score * 0.4)

        cycle_score = 0.0
        if cycle in ["Accumulation", "Pre-Halving Rally"]:
            cycle_score = 0.8
        elif cycle == "Post-Halving Expansion":
            cycle_score = 0.4
        elif cycle == "Bear Market / Distribution":
            cycle_score = -0.8

        final_lt = (onchain_score * 0.45) + (cycle_score * 0.40) + (macro_score * 0.15)

        return {
            "score": round(final_lt * 100, 2),
            "components": {
                "onchain": round(onchain_score, 2),
                "macro": round(macro_score, 2),
                "cycle": round(cycle_score, 2),
            },
        }

    def _calc_medium_term_quant(self, data: dict) -> dict:
        metrics = data.get("metrics", {})
        market = data.get("market_data", {})
        flags = data.get("flags", {})

        fng = metrics.get("fear_and_greed")
        fng_score = self._normalize(fng, 10, 90, invert=True)

        ext_pct = market.get("price_vs_ema_pct")
        trend_ext_score = self._normalize(ext_pct, -30, 100, invert=True)
        trend_dir = 1.0 if flags.get("is_bull_trend") else -1.0
        season_score = 1.0 if flags.get("is_positive_seasonality") else 0.0

        final_mt = (trend_dir * 0.60) + (fng_score * 0.20) + (trend_ext_score * 0.15) + (season_score * 0.05)

        return {
            "score": round(final_mt * 100, 2),
            "components": {
                "sentiment": round(fng_score, 2),
                "extension": round(trend_ext_score, 2),
                "trend_dir": round(trend_dir, 2),
            },
        }

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