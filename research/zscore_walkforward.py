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
        """
        df = self.data.copy()
        
        # Metric: MVRV Proxy
        rolling_mean = df['mvrv_proxy'].rolling(window=window).mean()
        rolling_std = df['mvrv_proxy'].rolling(window=window).std()
        
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
            
            # Adaptive Logic: Buy when 1.2 sigma below mean, Sell when 2.2 sigma above
            if row['mvrv_zscore'] < -1.2 and cash > 0:
                btc = cash / price
                cash = 0
                trades_adaptive += 1
                buy_signals_adaptive.append((row.name, price))
            elif row['mvrv_zscore'] > 2.2 and btc > 0:
                cash = btc * price
                btc = 0
                trades_adaptive += 1
                sell_signals_adaptive.append((row.name, price))
                
        df['equity_adaptive'] = equity_adaptive
        final_adaptive = equity_adaptive[-1]
        
        # --- Plotting ---
        plt.figure(figsize=(12, 8))
        
        # Plot 1: Price & Signals
        plt.subplot(2, 1, 1)
        plt.plot(df.index, df['price'], label='BTC Price', color='black', alpha=0.6)
        plt.yscale('log')
        plt.title('Strategy Comparison: Static (Red/Green) vs Adaptive (Blue/Orange)')
        
        # Static Signals
        for date, price in buy_signals_static:
            plt.scatter(date, price, color='green', marker='^', s=100, label='Static Buy' if date==buy_signals_static[0][0] else "")
        for date, price in sell_signals_static:
            plt.scatter(date, price, color='red', marker='v', s=100, label='Static Sell' if date==sell_signals_static[0][0] else "")
            
        # Adaptive Signals
        for date, price in buy_signals_adaptive:
            plt.scatter(date, price, color='blue', marker='^', s=60, label='Adaptive Buy' if date==buy_signals_adaptive[0][0] else "")
        for date, price in sell_signals_adaptive:
            plt.scatter(date, price, color='orange', marker='v', s=60, label='Adaptive Sell' if date==sell_signals_adaptive[0][0] else "")
            
        plt.legend()
        
        # Plot 2: Z-Score
        plt.subplot(2, 1, 2)
        plt.plot(df.index, df['mvrv_zscore'], label='MVRV Z-Score (4y Window)', color='purple')
        plt.axhline(y=-1.2, color='green', linestyle='--', label='Buy Threshold (-1.2)')
        plt.axhline(y=2.2, color='red', linestyle='--', label='Sell Threshold (2.2)')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig('research/zscore_analysis.png')
        print("Plot saved to research/zscore_analysis.png")
        
        # --- Results ---
        print("\n" + "="*40)
        print("RESEARCH RESULTS: STATIC vs ADAPTIVE (4-Year Window)")
        print("="*40)
        print(f"Initial Capital: ${initial_capital:,.2f}")
        print("-" * 20)
        print(f"Strategy A (Static MVRV < 1.0 / > 3.7):")
        print(f"Final Equity: ${final_static:,.2f}")
        print(f"Return: {((final_static - initial_capital)/initial_capital)*100:.2f}%")
        print(f"Trades: {trades_static}")
        print("-" * 20)
        print(f"Strategy B (Adaptive Z-Score < -1.2 / > 2.2):")
        print(f"Final Equity: ${final_adaptive:,.2f}")
        print(f"Return: {((final_adaptive - initial_capital)/initial_capital)*100:.2f}%")
        print(f"Trades: {trades_adaptive}")
        print("="*40)
        
        return df

if __name__ == "__main__":
    research = ZScoreResearch()
    research.load_data()
    research.calculate_zscores()
    research.run_comparison()
