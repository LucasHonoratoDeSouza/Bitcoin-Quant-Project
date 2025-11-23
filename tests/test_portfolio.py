import unittest
import sys
import os
from pathlib import Path

# Add project root to python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.execution.portfolio_manager import PortfolioManager

class TestPortfolioManager(unittest.TestCase):
    
    def setUp(self):
        self.pm = PortfolioManager(min_trade_usd=10.0)

    def test_strong_buy_from_cash(self):
        # Scenario: 100% Cash, Strong Buy Signal
        scores = {
            "long_term": {"value": 60},
            "medium_term": {"value": 40}
        }
        order = self.pm.calculate_order(scores, current_cash=1000.0, current_btc_value=0.0)
        
        self.assertIsNotNone(order)
        self.assertEqual(order.side, "BUY")
        self.assertEqual(order.amount_usd, 1000.0) # All In
        self.assertEqual(order.reason, "Strong Buy (High Conviction)")

    def test_sell_everything(self):
        # Scenario: 100% BTC, Bear Market Signal
        scores = {
            "long_term": {"value": -60},
            "medium_term": {"value": -40}
        }
        order = self.pm.calculate_order(scores, current_cash=0.0, current_btc_value=1000.0)
        
        self.assertIsNotNone(order)
        self.assertEqual(order.side, "SELL")
        self.assertEqual(order.amount_usd, 1000.0) # Sell All
        self.assertEqual(order.reason, "Sell Everything (Bear Market)")

    def test_accumulate_dca(self):
        # Scenario: 50% BTC, Accumulate Signal (+10%)
        scores = {
            "long_term": {"value": 40},
            "medium_term": {"value": -40}
        }
        # Total Equity = 2000. Current Alloc = 0.5. Target = 0.6.
        # Target BTC = 1200. Diff = +200.
        order = self.pm.calculate_order(scores, current_cash=1000.0, current_btc_value=1000.0)
        
        self.assertIsNotNone(order)
        self.assertEqual(order.side, "BUY")
        self.assertEqual(order.amount_usd, 200.0)
        self.assertEqual(order.reason, "Accumulate (Dip Buying)")

    def test_sell_rally(self):
        # Scenario: 50% BTC, Sell Rally Signal (-20%)
        scores = {
            "long_term": {"value": -40},
            "medium_term": {"value": 40}
        }
        # Total Equity = 2000. Current Alloc = 0.5. Target = 0.3.
        # Target BTC = 600. Diff = -400.
        order = self.pm.calculate_order(scores, current_cash=1000.0, current_btc_value=1000.0)
        
        self.assertIsNotNone(order)
        self.assertEqual(order.side, "SELL")
        self.assertEqual(order.amount_usd, 400.0)
        self.assertEqual(order.reason, "Sell Rally (Exit Liquidity)")

    def test_buy_scalp_limit(self):
        # Scenario: 0% BTC, Scalp Signal (Max 30%)
        scores = {
            "long_term": {"value": 0},
            "medium_term": {"value": 60}
        }
        # Total Equity = 1000. Target = 0.2 (Current + 0.2).
        # Wait, logic says min(current + 0.20, 0.30).
        # If current is 0, target is 0.2.
        order = self.pm.calculate_order(scores, current_cash=1000.0, current_btc_value=0.0)
        
        self.assertIsNotNone(order)
        self.assertEqual(order.side, "BUY")
        self.assertEqual(order.amount_usd, 200.0) # 20%
        self.assertEqual(order.reason, "Buy Scalp (Tactical)")
        
        # Scenario: 20% BTC, Scalp Signal (Max 30%)
        # Total Equity = 1000. Cash 800, BTC 200.
        # Target = min(0.2 + 0.2, 0.3) = 0.3.
        # Target BTC = 300. Diff = +100.
        order2 = self.pm.calculate_order(scores, current_cash=800.0, current_btc_value=200.0)
        self.assertEqual(order2.amount_usd, 100.0)

    def test_min_trade_threshold(self):
        # Scenario: Small difference
        scores = {
            "long_term": {"value": 0},
            "medium_term": {"value": 0}
        }
        # Neutral -> Target = Current. No trade.
        order = self.pm.calculate_order(scores, current_cash=1000.0, current_btc_value=0.0)
        self.assertIsNone(order)

    def test_super_bull_leverage(self):
        # Scenario: 100% Cash, Super Bull Signal (>80, >60)
        scores = {
            "long_term": {"value": 85},
            "medium_term": {"value": 65}
        }
        # Equity = 1000. Target Alloc = 2.0. Target BTC = 2000.
        # Current BTC = 0. Diff = +2000.
        # Cash = 1000. Order = 2000 (Implies borrowing 1000).
        order = self.pm.calculate_order(scores, current_cash=1000.0, current_btc_value=0.0, current_debt=0.0)
        
        self.assertIsNotNone(order)
        self.assertEqual(order.side, "BUY")
        self.assertEqual(order.amount_usd, 2000.0)
        self.assertEqual(order.reason, "Super Bull (Leveraged Buy)")

    def test_de_leverage_safety(self):
        # Scenario: 200% BTC (Leveraged), Score drops to 79 (Below 80)
        scores = {
            "long_term": {"value": 79},
            "medium_term": {"value": 60}
        }
        # Equity = 1000 (Assets 2000 - Debt 1000).
        # Target Alloc for 79 is "Strong Buy" (1.0).
        # Target BTC = 1000 * 1.0 = 1000.
        # Current BTC = 2000. Diff = -1000.
        order = self.pm.calculate_order(scores, current_cash=0.0, current_btc_value=2000.0, current_debt=1000.0)
        
        self.assertIsNotNone(order)
        self.assertEqual(order.side, "SELL")
        self.assertEqual(order.amount_usd, 1000.0)
        # Reason might be Strong Buy because that's the active zone, but the action is selling to reduce to 1.0
        # The reason string comes from the target zone.
        self.assertEqual(order.reason, "Strong Buy (High Conviction)") 

if __name__ == '__main__':
    unittest.main()
