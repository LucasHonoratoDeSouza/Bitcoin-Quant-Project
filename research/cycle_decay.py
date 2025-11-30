import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.backtest.data_loader import BacktestDataLoader

class CycleDecayResearch:
    def __init__(self):
        self.loader = BacktestDataLoader(start_date="2014-09-17")
        self.full_data = None
        self.results_dir = "research/wfa/results"
        os.makedirs(self.results_dir, exist_ok=True)
        
    def load_data(self):
        print("Loading full dataset...")
        self.full_data = self.loader.fetch_data()
        print(f"Loaded {len(self.full_data)} rows.")

    def _normalize(self, value, min_val, max_val, invert=False):
        if pd.isna(value): return 0.0
        clamped = max(min_val, min(value, max_val))
        normalized = (clamped - min_val) / (max_val - min_val)
        score = (normalized * 2) - 1
        if invert: score = -score
        return score

    def run_backtest(self, df, cycle_weight=0.40):
        """
        Runs backtest with varying Cycle Weights.
        Weights are redistributed to OnChain (Z-Score) proportionally.
        """
        initial_capital = 10000.0
        cash = initial_capital
        btc = 0
        equity = []
        trades = 0
        
        # Pre-calculate Indicators
        window = 1460
        rolling_mean = df['mvrv_proxy'].rolling(window=window, min_periods=365).mean()
        rolling_std = df['mvrv_proxy'].rolling(window=window, min_periods=365).std()
        df = df.copy()
        df['mvrv_zscore'] = (df['mvrv_proxy'] - rolling_mean) / rolling_std
        
        if 'rup' not in df.columns:
            df['rup'] = df['mvrv_proxy'] * 0.5
            
        df = df.dropna(subset=['mvrv_zscore'])
        
        if df.empty: return {"return_pct": 0, "max_dd_pct": 0}

        # Define Weights
        # Baseline: OnChain 45%, Cycle 40%, Macro 15%
        # If Cycle reduces, where does it go? Let's put it into OnChain (Data Driven)
        
        w_cycle = cycle_weight
        w_macro = 0.15
        w_onchain = 1.0 - w_cycle - w_macro
        
        for i, row in df.iterrows():
            price = row['price']
            
            # --- SCORING LOGIC ---
            
            # 1. OnChain Score (Mixed)
            z_val = row['mvrv_zscore']
            mvrv_score = self._normalize(z_val, -1.2, 2.5, invert=True)
            mm_val = row['mayer_multiple']
            mm_score = self._normalize(mm_val, 0.6, 2.4, invert=True)
            rup_val = row['rup']
            rup_score = self._normalize(rup_val, 0.0, 3.0, invert=True)
            
            onchain_score = (mvrv_score * 0.4) + (mm_score * 0.3) + (rup_score * 0.3)
            
            # 2. Cycle Score
            cycle_phase = row['cycle_phase']
            cycle_score = 0.0
            if cycle_phase in ["Accumulation", "Pre-Halving Rally"]: cycle_score = 0.8
            elif cycle_phase == "Post-Halving Expansion": cycle_score = 0.4
            elif cycle_phase == "Bear Market / Distribution": cycle_score = -0.8
            
            # 3. Macro Score (Simplified)
            m2_score = self._normalize(row['m2_yoy'], 0.0, 10.0)
            ir_score = self._normalize(row['interest_rate'], 2.0, 5.0, invert=True)
            macro_score = (m2_score * 0.6) + (ir_score * 0.4)
            
            # Final LT Score
            final_lt = (onchain_score * w_onchain) + (cycle_score * w_cycle) + (macro_score * w_macro)
            
            # --- TRADING LOGIC ---
            # Buy > 0.2, Sell < -0.2
            
            buy_signal = final_lt > 0.2
            sell_signal = final_lt < -0.2
            
            if buy_signal and cash > 0:
                btc = cash / price
                cash = 0
                trades += 1
            elif sell_signal and btc > 0:
                cash = btc * price
                btc = 0
                trades += 1
            
            # Mark-to-market
            val = cash + (btc * price)
            equity.append(val)
            
        final_equity = equity[-1] if equity else initial_capital
        total_return = ((final_equity - initial_capital) / initial_capital) * 100
        
        # Max Drawdown
        peak = initial_capital
        max_dd = 0
        for val in equity:
            if val > peak: peak = val
            dd = (val - peak) / peak
            if dd < max_dd: max_dd = dd
            
        return {
            "return_pct": total_return,
            "max_drawdown_pct": max_dd * 100,
            "trades": trades,
            "equity_curve": equity
        }

    def run_comparison(self):
        print("Running Cycle Decay Research...")
        
        # Run Baseline (40% Cycle)
        res_base = self.run_backtest(self.full_data, cycle_weight=0.40)
        
        # Run Reduced Cycle (20% Cycle, 65% OnChain)
        res_reduced = self.run_backtest(self.full_data, cycle_weight=0.20)
        
        # Run No Cycle (0% Cycle, 85% OnChain)
        res_none = self.run_backtest(self.full_data, cycle_weight=0.00)
        
        print("\n--- RESULTS (2016-2025) ---")
        print(f"Strategy: Baseline (40% Cycle)")
        print(f"Return: {res_base['return_pct']:.2f}%")
        print(f"Max DD: {res_base['max_drawdown_pct']:.2f}%")
        
        print(f"\nStrategy: Reduced Cycle (20% Cycle)")
        print(f"Return: {res_reduced['return_pct']:.2f}%")
        print(f"Max DD: {res_reduced['max_drawdown_pct']:.2f}%")
        
        print(f"\nStrategy: No Cycle (0% Cycle - Pure Data)")
        print(f"Return: {res_none['return_pct']:.2f}%")
        print(f"Max DD: {res_none['max_drawdown_pct']:.2f}%")
        
        # Plot
        plt.figure(figsize=(12, 6))
        plt.plot(res_base['equity_curve'], label=f"Baseline (40% Cycle)")
        plt.plot(res_reduced['equity_curve'], label=f"Reduced (20% Cycle)")
        plt.plot(res_none['equity_curve'], label=f"No Cycle (0% Cycle)")
        
        plt.title("Impact of Reducing Cycle Weight")
        plt.yscale('log')
        plt.legend()
        plt.grid(True, which="both", ls="-", alpha=0.2)
        plt.savefig(f"{self.results_dir}/cycle_decay_comparison.png")
        print(f"\nChart saved to {self.results_dir}/cycle_decay_comparison.png")

if __name__ == "__main__":
    research = CycleDecayResearch()
    research.load_data()
    research.run_comparison()
