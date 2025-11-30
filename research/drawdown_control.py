import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.backtest.data_loader import BacktestDataLoader

class DrawdownControlResearch:
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

    def run_backtest(self, df, use_hard_stop=False):
        """
        Runs backtest with optional Hard Stop-Loss.
        Hard Stop: If Price < SMA 200W (1400 days), force exit (sell all).
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
            
        # Calculate SMA 200W (1400 days)
        df['sma_200w'] = df['price'].rolling(window=1400).mean()
        
        df = df.dropna(subset=['mvrv_zscore', 'sma_200w'])
        
        if df.empty: return {"return_pct": 0, "max_dd_pct": 0}

        for i, row in df.iterrows():
            price = row['price']
            sma_200w = row['sma_200w']
            
            # --- HARD STOP LOGIC ---
            # If price breaks below 200W SMA, force exit
            is_hard_stop_triggered = use_hard_stop and (price < sma_200w)
            
            if is_hard_stop_triggered and btc > 0:
                # Emergency Exit
                cash = btc * price
                btc = 0
                trades += 1
                # Mark-to-market
                val = cash + (btc * price)
                equity.append(val)
                continue # Skip normal logic
            
            # --- SCORING LOGIC (Mixed Strategy) ---
            z_val = row['mvrv_zscore']
            mvrv_score = self._normalize(z_val, -1.2, 2.5, invert=True)
            
            mm_val = row['mayer_multiple']
            mm_score = self._normalize(mm_val, 0.6, 2.4, invert=True)
            
            rup_val = row['rup']
            rup_score = self._normalize(rup_val, 0.0, 3.0, invert=True)
            
            onchain_score = (mvrv_score * 0.4) + (mm_score * 0.3) + (rup_score * 0.3)
            
            # Cycle Score
            cycle_phase = row['cycle_phase']
            cycle_score = 0.0
            if cycle_phase in ["Accumulation", "Pre-Halving Rally"]: cycle_score = 0.8
            elif cycle_phase == "Post-Halving Expansion": cycle_score = 0.4
            elif cycle_phase == "Bear Market / Distribution": cycle_score = -0.8
            
            # Macro Score
            m2_score = self._normalize(row['m2_yoy'], 0.0, 10.0)
            ir_score = self._normalize(row['interest_rate'], 2.0, 5.0, invert=True)
            macro_score = (m2_score * 0.6) + (ir_score * 0.4)
            
            # Final LT Score
            final_lt = (onchain_score * 0.45) + (cycle_score * 0.40) + (macro_score * 0.15)
            
            # --- TRADING LOGIC ---
            buy_signal = final_lt > 0.2
            sell_signal = final_lt < -0.2
            
            # Additional Rule: Don't buy if Hard Stop is active (Price < 200W SMA)
            if use_hard_stop and (price < sma_200w):
                buy_signal = False
            
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
        print("Running Drawdown Control Research...")
        
        # Run Baseline (No Hard Stop)
        res_base = self.run_backtest(self.full_data, use_hard_stop=False)
        
        # Run Hard Stop (200W SMA)
        res_stop = self.run_backtest(self.full_data, use_hard_stop=True)
        
        print("\n--- RESULTS (2016-2025) ---")
        print(f"Strategy: Baseline (No Hard Stop)")
        print(f"Return: {res_base['return_pct']:.2f}%")
        print(f"Max DD: {res_base['max_drawdown_pct']:.2f}%")
        print(f"Trades: {res_base['trades']}")
        
        print(f"\nStrategy: Hard Stop (200W SMA)")
        print(f"Return: {res_stop['return_pct']:.2f}%")
        print(f"Max DD: {res_stop['max_drawdown_pct']:.2f}%")
        print(f"Trades: {res_stop['trades']}")
        
        # Calculate Improvement
        dd_improvement = res_base['max_drawdown_pct'] - res_stop['max_drawdown_pct']
        return_sacrifice = res_base['return_pct'] - res_stop['return_pct']
        
        print(f"\n📊 Analysis:")
        print(f"Drawdown Reduction: {dd_improvement:.2f}% (Better if positive)")
        print(f"Return Sacrifice: {return_sacrifice:.2f}% (Lower is better)")
        
        # Plot
        plt.figure(figsize=(12, 6))
        plt.plot(res_base['equity_curve'], label=f"Baseline (Ret: {res_base['return_pct']:.0f}%, DD: {res_base['max_drawdown_pct']:.0f}%)")
        plt.plot(res_stop['equity_curve'], label=f"Hard Stop 200W (Ret: {res_stop['return_pct']:.0f}%, DD: {res_stop['max_drawdown_pct']:.0f}%)")
        
        plt.title("Drawdown Control: 200-Week SMA Hard Stop")
        plt.yscale('log')
        plt.legend()
        plt.grid(True, which="both", ls="-", alpha=0.2)
        plt.savefig(f"{self.results_dir}/drawdown_control.png")
        print(f"\nChart saved to {self.results_dir}/drawdown_control.png")

if __name__ == "__main__":
    research = DrawdownControlResearch()
    research.load_data()
    research.run_comparison()
