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
        self.assertEqual(order.reason, "Bear Market (Defensive)")

    def test_accumulate_dca(self):
        # Scenario: 50% BTC, Accumulate Signal (MT -25)
        # Logic: LT > 20 and MT < -20.
        # Addition = 25/200 = 0.125 (12.5%).
        scores = {
            "long_term": {"value": 40},
            "medium_term": {"value": -25}
        }
        # Total Equity = 2000. Current Alloc = 0.5. Target = 0.625.
        # Target BTC = 1250. Diff = +250.
        order = self.pm.calculate_order(scores, current_cash=1000.0, current_btc_value=1000.0)
        
        self.assertIsNotNone(order)
        self.assertEqual(order.side, "BUY")
        self.assertEqual(order.amount_usd, 250.0)
        self.assertIn("Accumulate", order.reason)

    def test_sell_rally(self):
        # Scenario: 50% BTC, Sell Rally Signal (-20% approx)
        # Old test used fixed -20%. New logic uses MT/200.
        # Let's use MT = 40. Reduction = 40/200 = 0.20 (20%).
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
        self.assertIn("Sell Rally", order.reason)

    def test_buy_scalp_limit(self):
        # Scenario: 0% BTC, Scalp Signal (Max 30%)
        # Note: LT must be > 20 to avoid "Sell Rally" logic.
        scores = {
            "long_term": {"value": 25},
            "medium_term": {"value": 60}
        }
        # Total Equity = 1000. Target = 0.2 (Current + 0.2).
        # Logic: min(current + 0.20, 0.30).
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

    def test_super_bull_leverage_scaling(self):
        # Scenario: Score 87.5 (Midpoint between 75 and 100) -> Should be 1.5x
        scores = {
            "long_term": {"value": 87.5},
            "medium_term": {"value": 60}
        }
        # Equity = 1000. Target = 1.5. Target BTC = 1500.
        order = self.pm.calculate_order(scores, current_cash=1000.0, current_btc_value=0.0, current_debt=0.0)
        
        self.assertIsNotNone(order)
        self.assertEqual(order.side, "BUY")
        self.assertEqual(order.amount_usd, 1500.0)
        self.assertIn("1.50x", order.reason)

    def test_accumulate_dynamic(self):
        # Scenario: Dip Intensity 40 (MT -40). Should buy +20% (40/200).
        scores = {
            "long_term": {"value": 30},
            "medium_term": {"value": -40}
        }
        # Current Alloc 0.5. Target 0.7.
        # Equity 2000. Target BTC 1400. Current BTC 1000. Diff +400.
        order = self.pm.calculate_order(scores, current_cash=1000.0, current_btc_value=1000.0)
        
        self.assertIsNotNone(order)
        self.assertEqual(order.side, "BUY")
        self.assertEqual(order.amount_usd, 400.0)
        self.assertIn("Dip Intensity 40", order.reason)

    def test_sell_rally_dynamic(self):
        # Scenario: Rally Heat 60 (MT 60). Should sell -30% (60/200).
        # Note: LT must be < 20 for Sell Rally.
        scores = {
            "long_term": {"value": 10},
            "medium_term": {"value": 60}
        }
        # Current Alloc 0.8. Target 0.5 (0.8 - 0.3).
        # Equity 2000. Target BTC 1000. Current BTC 1600. Diff -600.
        order = self.pm.calculate_order(scores, current_cash=400.0, current_btc_value=1600.0)
        
        self.assertIsNotNone(order)
        self.assertEqual(order.side, "SELL")
        self.assertEqual(order.amount_usd, 600.0)
        self.assertIn("Heat 60", order.reason)
        
    def test_neutral_baseline(self):
        # Scenario: Neutral Score (0, 0). Current 0% BTC.
        # Should buy up to 30% (Baseline).
        scores = {
            "long_term": {"value": 0},
            "medium_term": {"value": 0}
        }
        # Equity 1000. Target 0.3. Target BTC 300. Current 0. Diff 300.
        order = self.pm.calculate_order(scores, current_cash=1000.0, current_btc_value=0.0)
        
        self.assertIsNotNone(order)
        self.assertEqual(order.side, "BUY")
        self.assertEqual(order.amount_usd, 300.0)
        self.assertIn("Baseline 30%", order.reason)

    def test_bear_market_moonbag(self):
        # Scenario: Bear Market (LT -50). Current 100% BTC.
        # Should sell down to 10% (Moonbag), not 0%.
        scores = {
            "long_term": {"value": -50},
            "medium_term": {"value": -20}
        }
        # Equity 1000. Target 0.1. Target BTC 100. Current 1000. Diff -900.
        order = self.pm.calculate_order(scores, current_cash=0.0, current_btc_value=1000.0)
        
        self.assertIsNotNone(order)
        self.assertEqual(order.side, "SELL")
        self.assertEqual(order.amount_usd, 900.0)
        self.assertIn("Moonbag 10%", order.reason)

    def test_extreme_bear_exit(self):
        # Scenario: Extreme Bear (LT -70). Current 10% BTC.
        # Should sell everything (0%).
        scores = {
            "long_term": {"value": -70},
            "medium_term": {"value": -20}
        }
        # Equity 1000. Target 0.0. Target BTC 0. Current 100. Diff -100.
        order = self.pm.calculate_order(scores, current_cash=900.0, current_btc_value=100.0)
        
        self.assertIsNotNone(order)
        self.assertEqual(order.side, "SELL")
        self.assertEqual(order.amount_usd, 100.0)
        self.assertIn("Extreme Bear", order.reason)

    def test_sell_rally_floor(self):
        # Scenario: Sell Rally (MT 60 -> -30%). Current 20%.
        # Target = 0.20 - 0.30 = -0.10.
        # Should floor at 0.10 (10%).
        scores = {
            "long_term": {"value": 10},
            "medium_term": {"value": 60}
        }
        # Equity 1000. Target 0.1. Target BTC 100. Current 200. Diff -100.
        order = self.pm.calculate_order(scores, current_cash=800.0, current_btc_value=200.0)
        
        self.assertIsNotNone(order)
        self.assertEqual(order.side, "SELL")
        self.assertEqual(order.amount_usd, 100.0)
        # Reason check might fail if I didn't update the string in PM.
        # Let's check PM code. It says "Sell Rally (Heat 60)".
        self.assertIn("Sell Rally", order.reason)

    def test_bear_market_defensive(self):
        # LT < -40 -> 10% Floor (Moonbag)
        scores = {
            "long_term": {"value": -45},
            "medium_term": {"value": 0}
        }
        # Equity 1000. Target 0.1. Target BTC 100. Current 1000. Diff -900.
        order = self.pm.calculate_order(scores, current_cash=0.0, current_btc_value=1000.0)
        self.assertEqual(order.side, "SELL")
        self.assertEqual(order.amount_usd, 900.0)
        self.assertEqual(order.reason, "Bear Market (Moonbag 10%)")

    def test_dynamic_threshold_skip(self):
        # Equity 2000. Threshold = max(20, 40) = 40.
        # Target Alloc change small.
        scores = {
            "long_term": {"value": 0},
            "medium_term": {"value": 0}
        }
        # Current Alloc 0.5. Target 0.5. No change.
        # Let's force a small diff.
        # Say Target is 0.51. Target BTC 1020. Current 1000. Diff 20.
        # 20 < 40. Should return None.
        
        # Mocking internal method to force small diff? 
        # Easier: Use Neutral scores but slightly off current alloc.
        # Neutral returns current. So diff is 0.
        
        # Let's use "Accumulate" with very small dip.
        # MT -1. Addition = 1/200 = 0.005 (0.5%).
        scores = {
            "long_term": {"value": 30},
            "medium_term": {"value": -21} # Just inside accumulate
        }
        # Addition = 21/200 = 0.105.
        # Wait, that's 10%. That's huge.
        
        # Let's use "Buy Scalp". Min is +20%. That's huge too.
        
        # Let's use "Rebalance" scenario where we are slightly off target?
        # The logic returns "current" for Neutral. So it won't trade.
        
        # Let's manually call calculate_order with a scenario where target is fixed but current is drifted.
        # Strong Buy -> Target 1.0.
        # Current Alloc 0.99.
        # Equity 10000. Target BTC 10000. Current BTC 9900. Diff 100.
        # Threshold = 10000 * 0.02 = 200.
        # Diff 100 < 200. Should skip.
        
        scores = {
            "long_term": {"value": 60},
            "medium_term": {"value": 40}
        }
        # Target 1.0.
        order = self.pm.calculate_order(
            scores, 
            current_cash=100.0, 
            current_btc_value=9900.0,
            current_debt=0.0
        )
        # Equity 10000. Threshold 200.
        # Target BTC 10000. Current 9900. Diff 100.
        # 100 < 200 -> None.
        self.assertIsNone(order)

    def test_cooldown_active(self):
        # Scenario: Valid trade signal, but within cooldown.
        scores = {
            "long_term": {"value": 30},
            "medium_term": {"value": -40} # Accumulate
        }
        # Last trade: Yesterday.
        last_date = "2025-11-23"
        curr_date = "2025-11-24" # 1 day diff.
        
        order = self.pm.calculate_order(
            scores,
            current_cash=1000.0,
            current_btc_value=1000.0,
            last_trade_date=last_date,
            current_date=curr_date
        )
        self.assertIsNone(order)

    def test_cooldown_bypass_urgent(self):
        # Scenario: Strong Buy (Urgent) should ignore cooldown.
        scores = {
            "long_term": {"value": 60},
            "medium_term": {"value": 40} # Strong Buy
        }
        last_date = "2025-11-23"
        curr_date = "2025-11-24"
        
        order = self.pm.calculate_order(
            scores,
            current_cash=1000.0,
            current_btc_value=0.0,
            last_trade_date=last_date,
            current_date=curr_date
        )
        self.assertIsNotNone(order)
        self.assertEqual(order.side, "BUY")
