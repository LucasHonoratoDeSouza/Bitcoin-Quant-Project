import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.backtest.data_loader import BacktestDataLoader

class HurstResearch:
    def __init__(self):
        self.loader = BacktestDataLoader(start_date="2014-09-17")
        self.full_data = None
        self.results_dir = "research/wfa/results"
        os.makedirs(self.results_dir, exist_ok=True)
        
    def load_data(self):
        print("Loading full dataset...")
        self.full_data = self.loader.fetch_data()
        print(f"Loaded {len(self.full_data)} rows.")

    def get_hurst_exponent(self, time_series, max_lag=20):
        """Returns the Hurst Exponent of the time series"""
        lags = range(2, max_lag)
        tau = [np.std(np.subtract(time_series[lag:], time_series[:-lag])) for lag in lags]
        poly = np.polyfit(np.log(lags), np.log(tau), 1)
        return poly[0] * 2.0

    def _normalize(self, value, min_val, max_val, invert=False):
        if pd.isna(value): return 0.0
        clamped = max(min_val, min(value, max_val))
        normalized = (clamped - min_val) / (max_val - min_val)
        score = (normalized * 2) - 1
        if invert: score = -score
        return score

    def run_backtest(self, df, use_hurst_filter=False):
        """
        Runs backtest with optional Hurst Filter.
        Filter: Block BUYs if Hurst > 0.6 (Strong Trend) AND Price < SMA_50 (Downtrend).
        """
        initial_capital = 10000.0
        cash = initial_capital
        btc = 0
        equity = []
        
        # Pre-calculate Indicators
        window = 1460
        rolling_mean = df['mvrv_proxy'].rolling(window=window, min_periods=365).mean()
        rolling_std = df['mvrv_proxy'].rolling(window=window, min_periods=365).std()
        df = df.copy()
        df['mvrv_zscore'] = (df['mvrv_proxy'] - rolling_mean) / rolling_std
        
        if 'rup' not in df.columns:
            df['rup'] = df['mvrv_proxy'] * 0.5
            
        # Calculate Hurst Exponent (Rolling 100 days)
        # This is slow, so we optimize or accept the wait
        print("Calculating Rolling Hurst Exponent (this may take a moment)...")
        
        # Vectorized approach is hard for Hurst, using apply
        # Using Log Prices for Hurst
        df['log_price'] = np.log(df['price'])
        
        # We'll use a simplified rolling Hurst or just iterate
        # For speed in this test, let's just iterate and calc only when needed? 
        # No, we need it for the whole series.
        # Let's use a faster approximation or just wait. 3000 rows is fine.
        
        hurst_values = []
        prices = df['log_price'].values
        window_size = 100
        
        for i in range(len(prices)):
            if i < window_size:
                hurst_values.append(0.5) # Default
            else:
                series = prices[i-window_size:i]
                h = self.get_hurst_exponent(series)
                hurst_values.append(h)
                
        df['hurst'] = hurst_values
        
        # SMA 50 for Trend Direction
        df['sma_50'] = df['price'].rolling(window=50).mean()
        
        df = df.dropna(subset=['mvrv_zscore', 'sma_50'])
        
        if df.empty: return {"return_pct": 0, "max_dd_pct": 0}

        entry_price = 0
        trades = 0
        
        for i, row in df.iterrows():
            price = row['price']
            hurst = row['hurst']
            sma = row['sma_50']
            
            # --- SCORING LOGIC (Mixed Strategy) ---
            z_val = row['mvrv_zscore']
            mvrv_score = self._normalize(z_val, -1.2, 2.5, invert=True)
            
            mm_val = row['mayer_multiple']
            mm_score = self._normalize(mm_val, 0.6, 2.4, invert=True)
            
            rup_val = row['rup']
            rup_score = self._normalize(rup_val, 0.0, 3.0, invert=True)
            
            final_score = (mvrv_score * 0.4) + (mm_score * 0.3) + (rup_score * 0.3)
            
            # --- SIGNAL GENERATION ---
            buy_signal = final_score > 0.2
            sell_signal = final_score < -0.2
            
            # --- HURST FILTER ---
            # If we want to BUY (Mean Reversion), check if we are catching a falling knife
            # Falling Knife = Strong Trend (Hurst > 0.6) + Price Dropping (Price < SMA)
            
            is_falling_knife = (hurst > 0.6) and (price < sma)
            
            if use_hurst_filter and buy_signal and is_falling_knife:
                buy_signal = False # BLOCK TRADE
            
            # Execution
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
            "final_equity": final_equity,
            "equity_curve": equity,
            "trades": trades
        }

    def run_comparison(self):
        print("Running Hurst Regime Research...")
        
        # Run Baseline
        res_base = self.run_backtest(self.full_data, use_hurst_filter=False)
        
        # Run Hurst Filter
        res_hurst = self.run_backtest(self.full_data, use_hurst_filter=True)
        
        print("\n--- RESULTS (2016-2025) ---")
        print(f"Strategy: Baseline (No Filter)")
        print(f"Return: {res_base['return_pct']:.2f}%")
        print(f"Max DD: {res_base['max_drawdown_pct']:.2f}%")
        print(f"Trades: {res_base['trades']}")
        
        print(f"\nStrategy: Hurst Filter (Avoid Falling Knives)")
        print(f"Return: {res_hurst['return_pct']:.2f}%")
        print(f"Max DD: {res_hurst['max_drawdown_pct']:.2f}%")
        print(f"Trades: {res_hurst['trades']}")
        
        # Plot
        plt.figure(figsize=(12, 6))
        plt.plot(res_base['equity_curve'], label=f"Baseline (Ret: {res_base['return_pct']:.0f}%, DD: {res_base['max_drawdown_pct']:.0f}%)")
        plt.plot(res_hurst['equity_curve'], label=f"Hurst Filter (Ret: {res_hurst['return_pct']:.0f}%, DD: {res_hurst['max_drawdown_pct']:.0f}%)")
        
        plt.title("Hurst Regime Filter: Avoiding Falling Knives")
        plt.yscale('log')
        plt.legend()
        plt.grid(True, which="both", ls="-", alpha=0.2)
        plt.savefig(f"{self.results_dir}/hurst_comparison.png")
        print(f"\nChart saved to {self.results_dir}/hurst_comparison.png")

if __name__ == "__main__":
    research = HurstResearch()
    research.load_data()
    research.run_comparison()
