import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.backtest.data_loader import BacktestDataLoader

class OnChainComparison:
    def __init__(self):
        # Use earliest possible date
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

    def run_backtest(self, df, strategy_type="mixed"):
        """
        strategy_type:
            - "mixed": Current logic (40% MVRV Z-Score, 30% MM, 30% RUP)
            - "pure_zscore": 100% MVRV Z-Score
        """
        initial_capital = 10000.0
        cash = initial_capital
        btc = 0
        equity = []
        trades = 0
        
        # Pre-calculate indicators if not present
        # We assume df already has 'mvrv_proxy', 'mayer_multiple', 'rup' (proxy)
        # We need to calculate Z-Score for MVRV
        
        window = 1460 # 4 years optimal from WFA
        rolling_mean = df['mvrv_proxy'].rolling(window=window, min_periods=365).mean()
        rolling_std = df['mvrv_proxy'].rolling(window=window, min_periods=365).std()
        df = df.copy()
        df['mvrv_zscore'] = (df['mvrv_proxy'] - rolling_mean) / rolling_std
        
        # Ensure RUP exists (Proxy)
        if 'rup' not in df.columns:
            df['rup'] = df['mvrv_proxy'] * 0.5
        
        # Drop initial NaNs from Z-Score calculation
        df = df.dropna(subset=['mvrv_zscore'])
        
        if df.empty: return {"return_pct": 0, "max_dd_pct": 0}

        entry_price = 0
        
        for i, row in df.iterrows():
            price = row['price']
            
            # --- SCORING LOGIC ---
            
            # 1. MVRV Score (Adaptive Z-Score)
            # Z < -1.2 (Bullish +1), Z > 2.5 (Bearish -1)
            z_val = row['mvrv_zscore']
            mvrv_score = self._normalize(z_val, -1.2, 2.5, invert=True)
            
            final_score = 0
            
            if strategy_type == "pure_zscore":
                final_score = mvrv_score
                
            elif strategy_type == "mixed":
                # 2. Mayer Multiple (Static)
                # 0.6 (Bullish) to 2.4 (Bearish)
                mm_val = row['mayer_multiple']
                mm_score = self._normalize(mm_val, 0.6, 2.4, invert=True)
                
                # 3. RUP (Proxy)
                # 0.0 (Bullish) to 3.0 (Bearish)
                rup_val = row['rup'] # In data_loader, rup is mvrv * 0.5 proxy
                rup_score = self._normalize(rup_val, 0.0, 3.0, invert=True)
                
                # Weighted Average (Current Logic)
                final_score = (mvrv_score * 0.4) + (mm_score * 0.3) + (rup_score * 0.3)
            
            # --- TRADING LOGIC ---
            # Buy if Score > 0.2 (Mildly Bullish)
            # Sell if Score < -0.2 (Mildly Bearish)
            # We use a threshold on the final score to simulate the "Long Term Score" impact
            
            buy_signal = final_score > 0.2
            sell_signal = final_score < -0.2
            
            if buy_signal and cash > 0:
                btc = cash / price
                cash = 0
                entry_price = price
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
            "final_equity": final_equity,
            "equity_curve": equity
        }

    def run_comparison(self):
        print("Running Comparison: Mixed (Current) vs Pure Z-Score...")
        
        # Run on Full History (post-2016 due to window)
        res_mixed = self.run_backtest(self.full_data, strategy_type="mixed")
        res_pure = self.run_backtest(self.full_data, strategy_type="pure_zscore")
        
        print("\n--- RESULTS (2016-2025) ---")
        print(f"Strategy: Mixed (MVRV+MM+RUP)")
        print(f"Return: {res_mixed['return_pct']:.2f}%")
        print(f"Max DD: {res_mixed['max_drawdown_pct']:.2f}%")
        print(f"Trades: {res_mixed['trades']}")
        
        print(f"\nStrategy: Pure Z-Score (MVRV Only)")
        print(f"Return: {res_pure['return_pct']:.2f}%")
        print(f"Max DD: {res_pure['max_drawdown_pct']:.2f}%")
        print(f"Trades: {res_pure['trades']}")
        
        # Plot
        plt.figure(figsize=(12, 6))
        plt.plot(res_mixed['equity_curve'], label=f"Mixed (Ret: {res_mixed['return_pct']:.0f}%)")
        plt.plot(res_pure['equity_curve'], label=f"Pure Z-Score (Ret: {res_pure['return_pct']:.0f}%)")
        plt.title("OnChain Composition Comparison: Mixed vs Pure Z-Score")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{self.results_dir}/comparison_onchain.png")
        print(f"\nChart saved to {self.results_dir}/comparison_onchain.png")

if __name__ == "__main__":
    comp = OnChainComparison()
    comp.load_data()
    comp.run_comparison()
