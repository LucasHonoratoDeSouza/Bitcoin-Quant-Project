import copy
import unittest

from src.strategy.score import QuantScorer


class TestQuantScorer(unittest.TestCase):
    def _base_snapshot(self) -> dict:
        return {
            "timestamp": "2026-04-20T00:00:00",
            "market_cycle_phase": "Accumulation",
            "market_data": {
                "current_price": 98000.0,
                "daily_change_pct": 1.2,
                "weekly_change_pct": 4.5,
                "monthly_change_pct": 12.0,
                "ema_365": 89000.0,
                "price_vs_ema_pct": 10.11,
            },
            "metrics": {
                "mvrv_zscore": -0.8,
                "mayer_multiple": 1.10,
                "rup": 0.90,
                "sopr": 0.99,
                "fear_and_greed": 42.0,
                "interest_rate": 3.2,
                "m2_yoy": 6.1,
                "inflation_yoy": 2.7,
                "funding_rate": 0.004,
                "realized_vol_30d": 0.58,
                "realized_vol_90d": 0.63,
                "momentum_63d": 0.16,
                "drawdown_180d": -0.17,
                "trend_tscore_90d": 1.35,
            },
            "flags": {
                "is_accumulation": True,
                "is_overheated": False,
                "is_fear_extreme": False,
                "is_greed_extreme": False,
                "is_liquidity_good": True,
                "is_inflation_high": False,
                "is_inflation_falling": True,
                "is_bull_trend": True,
                "is_derivatives_risk": False,
                "is_volatility_opportunity": False,
                "is_positive_seasonality": True,
                "is_high_corr_spx": False,
                "is_high_corr_gold": False,
            },
        }

    def test_quant_mode_output_contract(self):
        scorer = QuantScorer(mode="quant")
        result = scorer.calculate_scores(self._base_snapshot())

        self.assertIn("scores", result)
        self.assertIn("metadata", result)
        self.assertIn("long_term", result["scores"])
        self.assertIn("medium_term", result["scores"])

        lt_value = result["scores"]["long_term"]["value"]
        mt_value = result["scores"]["medium_term"]["value"]
        self.assertGreaterEqual(lt_value, -100.0)
        self.assertLessEqual(lt_value, 100.0)
        self.assertGreaterEqual(mt_value, -100.0)
        self.assertLessEqual(mt_value, 100.0)

        lt_components = result["scores"]["long_term"]["components"]
        self.assertIn("uncertainty", lt_components)
        self.assertIn("coverage", lt_components)

    def test_valuation_discount_improves_long_term_score(self):
        scorer = QuantScorer(mode="quant")

        cheap = self._base_snapshot()
        expensive = copy.deepcopy(cheap)

        cheap["metrics"]["mvrv_zscore"] = -1.8
        cheap["metrics"]["mayer_multiple"] = 0.92
        cheap["metrics"]["rup"] = 0.60
        cheap["metrics"]["sopr"] = 0.97

        expensive["metrics"]["mvrv_zscore"] = 2.2
        expensive["metrics"]["mayer_multiple"] = 2.15
        expensive["metrics"]["rup"] = 2.20
        expensive["metrics"]["sopr"] = 1.10
        expensive["flags"]["is_overheated"] = True

        cheap_lt = scorer.calculate_scores(cheap)["scores"]["long_term"]["value"]
        expensive_lt = scorer.calculate_scores(expensive)["scores"]["long_term"]["value"]

        self.assertGreater(cheap_lt, expensive_lt)

    def test_conflicting_signals_raise_uncertainty(self):
        scorer = QuantScorer(mode="quant")

        coherent = self._base_snapshot()
        conflicting = copy.deepcopy(coherent)

        conflicting["metrics"]["weekly_change_pct"] = 11.0
        conflicting["market_data"]["weekly_change_pct"] = 11.0
        conflicting["market_data"]["monthly_change_pct"] = 26.0
        conflicting["metrics"]["m2_yoy"] = -2.0
        conflicting["metrics"]["interest_rate"] = 7.5
        conflicting["metrics"]["inflation_yoy"] = 6.8
        conflicting["metrics"]["funding_rate"] = 0.045
        conflicting["metrics"]["realized_vol_30d"] = 1.10
        conflicting["metrics"]["realized_vol_90d"] = 1.05
        conflicting["metrics"]["mvrv_zscore"] = 1.8
        conflicting["flags"]["is_derivatives_risk"] = True
        conflicting["flags"]["is_liquidity_good"] = False
        conflicting["flags"]["is_inflation_high"] = True
        conflicting["flags"]["is_overheated"] = True

        coherent_result = scorer.calculate_scores(coherent)
        conflict_result = scorer.calculate_scores(conflicting)

        coherent_uncertainty = coherent_result["scores"]["long_term"]["components"]["uncertainty"]
        conflict_uncertainty = conflict_result["scores"]["long_term"]["components"]["uncertainty"]

        self.assertGreater(conflict_uncertainty, coherent_uncertainty)


if __name__ == "__main__":
    unittest.main()
