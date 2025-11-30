import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.backtest.data_loader import BacktestDataLoader

class ZScoreResearch:
    def __init__(self):
        self.loader = BacktestDataLoader(start_date="2016-01-01")
        self.data = None
        
    def load_data(self):
        print("Loading data...")
        self.data = self.loader.fetch_data()
        print(f"Data loaded: {len(self.data)} rows")
        
    def calculate_zscores(self, window=1460):
        """
        Calculate Rolling Z-Scores for key metrics.
        Using a 4-year rolling window (1460 days) to capture the full Halving Cycle context.
        Using min_periods=365 to allow signals to start generating after 1 year of data.
        """
        df = self.data.copy()
        
        # Metric: MVRV Proxy
        rolling_mean = df['mvrv_proxy'].rolling(window=window, min_periods=365).mean()
        rolling_std = df['mvrv_proxy'].rolling(window=window, min_periods=365).std()
        
        df['mvrv_zscore'] = (df['mvrv_proxy'] - rolling_mean) / rolling_std
        
        self.data = df.dropna()
        
    def run_comparison(self):
        # ... (Same logic as before, just ensuring we use the updated data) ...
        df = self.data.copy()
        initial_capital = 10000.0
        
        # --- Strategy A: Static ---
        cash = initial_capital
        btc = 0
        equity_static = []
        trades_static = 0
        buy_signals_static = []
        sell_signals_static = []
        
        for i, row in df.iterrows():
            price = row['price']
            val = cash + (btc * price)
            equity_static.append(val)
            
            if row['mvrv_proxy'] < 1.0 and cash > 0:
                btc = cash / price
                cash = 0
                trades_static += 1
                buy_signals_static.append((row.name, price))
            elif row['mvrv_proxy'] > 3.7 and btc > 0: # Tuned to 3.7 to match historical tops better
                cash = btc * price
                btc = 0
                trades_static += 1
                sell_signals_static.append((row.name, price))
                
        df['equity_static'] = equity_static
        final_static = equity_static[-1]
        
        # --- Strategy B: Adaptive Z-Scores ---
        cash = initial_capital
        btc = 0
        equity_adaptive = []
        trades_adaptive = 0
        buy_signals_adaptive = []
        sell_signals_adaptive = []
        
        for i, row in df.iterrows():
            price = row['price']
            val = cash + (btc * price)
            equity_adaptive.append(val)
            
            # Adaptive Logic: Buy < -1.2, Sell > 2.0
            if row['mvrv_zscore'] < -1.2 and cash > 0:
                btc = cash / price
                cash = 0
                trades_adaptive += 1
                buy_signals_adaptive.append((row.name, price))
            elif row['mvrv_zscore'] > 2.0 and btc > 0:
                cash = btc * price
                btc = 0
                trades_adaptive += 1
                sell_signals_adaptive.append((row.name, price))
                
        df['equity_adaptive'] = equity_adaptive
        final_adaptive = equity_adaptive[-1]
        
        # --- Strategy C: Adaptive + Trend Filter (The "Smart" Way) ---
        # Buy: Cheap (Z-Score < -1.2)
        # Sell: Expensive (Z-Score > 2.0) AND Trend Weakening (Price < SMA 50)
        # This prevents selling early in a parabolic run.
        cash = initial_capital
        btc = 0
        equity_trend = []
        trades_trend = 0
        buy_signals_trend = []
        sell_signals_trend = []
        
        # Calculate SMA 50 for trend filter
        df['sma_50'] = df['price'].rolling(window=50).mean()
        
        for i, row in df.iterrows():
            price = row['price']
            val = cash + (btc * price)
            equity_trend.append(val)
            
            # Entry: Pure Value (Buy when cheap)
            if row['mvrv_zscore'] < -1.2 and cash > 0:
                btc = cash / price
                cash = 0
                trades_trend += 1
                buy_signals_trend.append((row.name, price))
                
            # Exit: Value + Trend (Sell when expensive AND trend breaks)
            # If Z-Score is high (> 2.0) BUT Price is still above SMA 50, we HOLD.
            # We only sell if it's expensive AND the price drops below SMA 50.
            elif row['mvrv_zscore'] > 2.0 and price < row['sma_50'] and btc > 0:
                cash = btc * price
                btc = 0
                trades_trend += 1
                sell_signals_trend.append((row.name, price))
                
        df['equity_trend'] = equity_trend
        final_trend = equity_trend[-1]
        
        # --- Plotting ---
        plt.figure(figsize=(12, 10))
        
        # Plot 1: Price & Signals
        plt.subplot(2, 1, 1)
        plt.plot(df.index, df['price'], label='BTC Price', color='black', alpha=0.5)
        plt.plot(df.index, df['sma_50'], label='SMA 50 (Trend)', color='orange', linestyle='--', alpha=0.5)
        plt.yscale('log')
        plt.title('Strategy Comparison: Static vs Adaptive vs Trend-Enhanced')
        
        # Static Signals (Small dots)
        # for date, price in buy_signals_static:
        #     plt.scatter(date, price, color='red', marker='.', s=20)
            
        # Adaptive Signals (Blue)
        for date, price in buy_signals_adaptive:
            plt.scatter(date, price, color='blue', marker='^', s=50, label='Adaptive Buy' if date==buy_signals_adaptive[0][0] else "")
        for date, price in sell_signals_adaptive:
            plt.scatter(date, price, color='blue', marker='v', s=50, label='Adaptive Sell' if date==sell_signals_adaptive[0][0] else "")

        # Trend Signals (Green/Red Large)
        for date, price in buy_signals_trend:
            plt.scatter(date, price, color='green', marker='^', s=100, label='Trend Buy' if date==buy_signals_trend[0][0] else "")
        for date, price in sell_signals_trend:
            plt.scatter(date, price, color='red', marker='v', s=100, label='Trend Sell' if date==sell_signals_trend[0][0] else "")
            
        plt.legend()
        
        # Plot 2: Z-Score
        plt.subplot(2, 1, 2)
        plt.plot(df.index, df['mvrv_zscore'], label='MVRV Z-Score', color='purple')
        plt.axhline(y=-1.2, color='green', linestyle='--')
        plt.axhline(y=2.2, color='red', linestyle='--')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig('research/zscore_trend_analysis.png')
        print("Plot saved to research/zscore_trend_analysis.png")
        
        # --- Debug Info ---
        print("\nDEBUG INFO:")
        print(f"Max MVRV Proxy: {df['mvrv_proxy'].max():.2f}")
        print(f"Max MVRV Z-Score: {df['mvrv_zscore'].max():.2f}")
        print(f"Min MVRV Z-Score: {df['mvrv_zscore'].min():.2f}")
        
        if buy_signals_adaptive:
            print(f"First Buy Date: {buy_signals_adaptive[0][0]}")
        else:
            print("No Buys triggered.")
            
        if sell_signals_adaptive:
            print(f"First Sell Date: {sell_signals_adaptive[0][0]}")
        else:
            print("No Sells triggered.")

        # --- Results ---
        print("\n" + "="*60)
        print("RESEARCH RESULTS: STATIC vs ADAPTIVE vs TREND-ENHANCED")
        print("="*60)
        print(f"Initial Capital: ${initial_capital:,.2f}")
        print("-" * 30)
        print(f"Strategy A (Static MVRV):")
        print(f"Final Equity: ${final_static:,.2f}")
        print(f"Return: {((final_static - initial_capital)/initial_capital)*100:.2f}%")
        print("-" * 30)
        print(f"Strategy B (Adaptive Z-Score):")
        print(f"Final Equity: ${final_adaptive:,.2f}")
        print(f"Return: {((final_adaptive - initial_capital)/initial_capital)*100:.2f}%")
        print("-" * 30)
        print(f"Strategy C (Adaptive + Trend Filter):")
        print(f"Final Equity: ${final_trend:,.2f}")
        print(f"Return: {((final_trend - initial_capital)/initial_capital)*100:.2f}%")
        print(f"Trades: {trades_trend}")
        print("="*60)
        
        return df

if __name__ == "__main__":
    research = ZScoreResearch()
    research.load_data()
    research.calculate_zscores()
    research.run_comparison()
