import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.backtest.data_loader import BacktestDataLoader

class MediumTermResearch:
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

    def run_backtest(self, df, mode="current"):
        """
        mode:
            - "current": F&G (40%) + Trend Ext (30%) + Trend Dir (25%) + Season (5%)
            - "rsi_enhanced": Adds RSI (14) to the mix.
            - "trend_following": Increases weight of Trend Direction.
        """
        initial_capital = 10000.0
        cash = initial_capital
        btc = 0
        equity = []
        trades = 0
        
        # Pre-calculate Indicators
        df = df.copy()
        
        # RSI 14
        delta = df['price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Trend Extension (Price vs EMA 21 Weekly approx 140 days)
        # Using SMA 140 for simplicity as proxy for medium term trend
        df['sma_140'] = df['price'].rolling(window=140).mean()
        df['trend_ext'] = (df['price'] - df['sma_140']) / df['sma_140']
        
        # Trend Direction (Price > SMA 50)
        df['sma_50'] = df['price'].rolling(window=50).mean()
        df['is_bull_trend'] = df['price'] > df['sma_50']
        
        df = df.dropna()
        
        if df.empty: return {"return_pct": 0, "max_dd_pct": 0}

        for i, row in df.iterrows():
            price = row['price']
            
            # --- SCORING LOGIC ---
            
            # 1. Sentiment (F&G Proxy using RSI/Vol if real F&G missing, but loader has it)
            # Loader has 'fear_and_greed' column?
            fng = row['fear_and_greed'] if 'fear_and_greed' in row else row['rsi'] # Fallback
            fng_score = self._normalize(fng, 10, 90, invert=True) # Buy Fear
            
            # 2. Trend Extension
            # -30% to +100% range
            ext_score = self._normalize(row['trend_ext'] * 100, -30, 100, invert=True) # Buy Dip
            
            # 3. Trend Direction
            trend_score = 1.0 if row['is_bull_trend'] else -1.0
            
            # 4. RSI Score (New)
            # RSI < 30 (Bullish), RSI > 70 (Bearish)
            rsi_score = self._normalize(row['rsi'], 30, 70, invert=True)
            
            final_mt_score = 0
            
            if mode == "current":
                # Sentiment (40%), Trend Ext (30%), Trend Dir (30%) - ignoring seasonality for simplicity
                final_mt_score = (fng_score * 0.40) + (ext_score * 0.30) + (trend_score * 0.30)
                
            elif mode == "rsi_enhanced":
                # Add RSI, reduce others
                # Sentiment (30%), RSI (30%), Trend Ext (20%), Trend Dir (20%)
                final_mt_score = (fng_score * 0.30) + (rsi_score * 0.30) + (ext_score * 0.20) + (trend_score * 0.20)
                
            elif mode == "trend_following":
                # Focus on Trend Direction
                # Trend Dir (60%), Sentiment (20%), Trend Ext (20%)
                final_mt_score = (trend_score * 0.60) + (fng_score * 0.20) + (ext_score * 0.20)

            # --- TRADING LOGIC ---
            # MT Strategy is more active.
            # Buy > 0.3, Sell < -0.3
            
            buy_signal = final_mt_score > 0.3
            sell_signal = final_mt_score < -0.3
            
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
        print("Running Medium Term Strategy Optimization...")
        
        res_curr = self.run_backtest(self.full_data, mode="current")
        res_rsi = self.run_backtest(self.full_data, mode="rsi_enhanced")
        res_trend = self.run_backtest(self.full_data, mode="trend_following")
        
        print("\n--- RESULTS (2016-2025) ---")
        print(f"Strategy: Current (F&G + Ext + Trend)")
        print(f"Return: {res_curr['return_pct']:.2f}%")
        print(f"Max DD: {res_curr['max_drawdown_pct']:.2f}%")
        print(f"Trades: {res_curr['trades']}")
        
        print(f"\nStrategy: RSI Enhanced (Adds RSI)")
        print(f"Return: {res_rsi['return_pct']:.2f}%")
        print(f"Max DD: {res_rsi['max_drawdown_pct']:.2f}%")
        print(f"Trades: {res_rsi['trades']}")
        
        print(f"\nStrategy: Trend Following (Focus on Direction)")
        print(f"Return: {res_trend['return_pct']:.2f}%")
        print(f"Max DD: {res_trend['max_drawdown_pct']:.2f}%")
        print(f"Trades: {res_trend['trades']}")
        
        # Plot
        plt.figure(figsize=(12, 6))
        plt.plot(res_curr['equity_curve'], label=f"Current (Ret: {res_curr['return_pct']:.0f}%)")
        plt.plot(res_rsi['equity_curve'], label=f"RSI Enhanced (Ret: {res_rsi['return_pct']:.0f}%)")
        plt.plot(res_trend['equity_curve'], label=f"Trend Following (Ret: {res_trend['return_pct']:.0f}%)")
        
        plt.title("Medium Term Strategy Optimization")
        plt.yscale('log')
        plt.legend()
        plt.grid(True, which="both", ls="-", alpha=0.2)
        plt.savefig(f"{self.results_dir}/mt_optimization.png")
        print(f"\nChart saved to {self.results_dir}/mt_optimization.png")

if __name__ == "__main__":
    research = MediumTermResearch()
    research.load_data()
    research.run_comparison()
