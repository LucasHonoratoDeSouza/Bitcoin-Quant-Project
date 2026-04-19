import unittest
import sys
from pathlib import Path


project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.execution.confidence_portfolio_manager import ConfidencePortfolioManager


class TestConfidencePortfolioManager(unittest.TestCase):
    def setUp(self):
        self.pm = ConfidencePortfolioManager(min_trade_usd=10.0, cooldown_days=1)

    def test_extreme_bear_still_exits(self):
        scores = {
            "long_term": {"value": -80},
            "medium_term": {"value": -30},
        }
        order = self.pm.calculate_order(
            scores,
            current_cash=900.0,
            current_btc_value=100.0,
            current_debt=0.0,
        )

        self.assertIsNotNone(order)
        self.assertEqual(order.side, "SELL")
        self.assertGreaterEqual(order.amount_usd, 99.0)

    def test_reason_contains_confidence(self):
        scores = {
            "long_term": {"value": 65},
            "medium_term": {"value": 35},
        }
        order = self.pm.calculate_order(
            scores,
            current_cash=1000.0,
            current_btc_value=0.0,
            current_debt=0.0,
        )

        self.assertIsNotNone(order)
        self.assertIn("Confidence", order.reason)

    def test_confidence_signal_monotonicity(self):
        high = self.pm._signal_confidence(80, 70)
        low = self.pm._signal_confidence(20, -20)
        self.assertGreater(high, low)


if __name__ == "__main__":
    unittest.main()
