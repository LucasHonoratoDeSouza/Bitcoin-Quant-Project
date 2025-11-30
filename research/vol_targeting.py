import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.backtest.data_loader import BacktestDataLoader

class VolatilityTargetingResearch:
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

    def run_backtest(self, df, use_vol_target=False, target_vol_annual=0.40):
        """
        Runs backtest with optional Volatility Targeting.
        target_vol_annual: Desired annualized volatility (e.g., 0.40 = 40%)
        """
        initial_capital = 10000.0
        cash = initial_capital
        btc = 0
        equity = []
        exposures = [] # Track exposure %
        
        # Pre-calculate Indicators
        window = 1460
        rolling_mean = df['mvrv_proxy'].rolling(window=window, min_periods=365).mean()
        rolling_std = df['mvrv_proxy'].rolling(window=window, min_periods=365).std()
        df = df.copy()
        df['mvrv_zscore'] = (df['mvrv_proxy'] - rolling_mean) / rolling_std
        
        if 'rup' not in df.columns:
            df['rup'] = df['mvrv_proxy'] * 0.5
            
        # Calculate Volatility (20-day rolling std of returns)
        df['returns'] = df['price'].pct_change()
        df['vol_20d'] = df['returns'].rolling(window=20).std() * np.sqrt(365) # Annualized
        
        df = df.dropna(subset=['mvrv_zscore', 'vol_20d'])
        
        if df.empty: return {"return_pct": 0, "max_dd_pct": 0}

        entry_price = 0
        
        for i, row in df.iterrows():
            price = row['price']
            vol = row['vol_20d']
            
            # --- SCORING LOGIC (Mixed Strategy) ---
            z_val = row['mvrv_zscore']
            mvrv_score = self._normalize(z_val, -1.2, 2.5, invert=True)
            
            mm_val = row['mayer_multiple']
            mm_score = self._normalize(mm_val, 0.6, 2.4, invert=True)
            
            rup_val = row['rup']
            rup_score = self._normalize(rup_val, 0.0, 3.0, invert=True)
            
            final_score = (mvrv_score * 0.4) + (mm_score * 0.3) + (rup_score * 0.3)
            
            # --- POSITION SIZING ---
            # Base Signal: Buy > 0.2, Sell < -0.2
            signal = 0 # 0 = Cash, 1 = Long
            if final_score > 0.2: signal = 1
            elif final_score < -0.2: signal = 0
            else:
                # Hold previous state logic not implemented for simplicity, 
                # strictly following score zones here implies:
                # If between -0.2 and 0.2, what do we do? 
                # Let's assume we hold previous signal for realism, 
                # but for this test let's be strict: Neutral = Cash (Safety)
                # OR better: Hysteresis. Let's use simple zones.
                signal = 1 if final_score > 0 else 0 # Simple > 0 is Bullish
            
            # Volatility Targeting Logic
            position_size = 1.0 # Default 100%
            
            if use_vol_target and signal == 1:
                # Formula: Target Vol / Current Vol
                # Cap leverage at 1.0 (no leverage)
                # If Vol is low (e.g. 20%), and Target is 40%, ratio is 2.0 -> Cap at 1.0
                # If Vol is high (e.g. 80%), and Target is 40%, ratio is 0.5 -> 50% Cash
                
                if vol > 0:
                    vol_scalar = target_vol_annual / vol
                    position_size = min(1.0, vol_scalar)
                else:
                    position_size = 1.0
            
            exposures.append(position_size if signal == 1 else 0)
            
            # Execution
            # Total Value = Cash + BTC Value
            total_val = cash + (btc * price)
            
            target_btc_val = total_val * position_size * signal
            current_btc_val = btc * price
            
            diff = target_btc_val - current_btc_val
            
            # Rebalance if diff is significant (e.g. > 1% of equity) to avoid noise
            if abs(diff) > total_val * 0.01:
                if diff > 0: # Buy
                    amount_to_buy = diff
                    if cash >= amount_to_buy:
                        btc += amount_to_buy / price
                        cash -= amount_to_buy
                else: # Sell
                    amount_to_sell = abs(diff)
                    btc -= amount_to_sell / price
                    cash += amount_to_sell
            
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
            "avg_exposure": np.mean(exposures)
        }

    def run_comparison(self):
        print("Running Volatility Targeting Research...")
        
        # Run Baseline (No Vol Target)
        res_base = self.run_backtest(self.full_data, use_vol_target=False)
        
        # Run Vol Target (Target 40% Vol - Conservative)
        res_vol40 = self.run_backtest(self.full_data, use_vol_target=True, target_vol_annual=0.40)
        
        # Run Vol Target (Target 60% Vol - Aggressive)
        res_vol60 = self.run_backtest(self.full_data, use_vol_target=True, target_vol_annual=0.60)
        
        print("\n--- RESULTS (2016-2025) ---")
        print(f"Strategy: Baseline (100% Exposure)")
        print(f"Return: {res_base['return_pct']:.2f}%")
        print(f"Max DD: {res_base['max_drawdown_pct']:.2f}%")
        print(f"Avg Exposure: {res_base['avg_exposure']*100:.1f}%")
        
        print(f"\nStrategy: Vol Target 60% (Aggressive)")
        print(f"Return: {res_vol60['return_pct']:.2f}%")
        print(f"Max DD: {res_vol60['max_drawdown_pct']:.2f}%")
        print(f"Avg Exposure: {res_vol60['avg_exposure']*100:.1f}%")
        
        print(f"\nStrategy: Vol Target 40% (Conservative)")
        print(f"Return: {res_vol40['return_pct']:.2f}%")
        print(f"Max DD: {res_vol40['max_drawdown_pct']:.2f}%")
        print(f"Avg Exposure: {res_vol40['avg_exposure']*100:.1f}%")
        
        # Plot
        plt.figure(figsize=(12, 6))
        plt.plot(res_base['equity_curve'], label=f"Baseline (Ret: {res_base['return_pct']:.0f}%, DD: {res_base['max_drawdown_pct']:.0f}%)", linewidth=1)
        plt.plot(res_vol60['equity_curve'], label=f"Vol Target 60% (Ret: {res_vol60['return_pct']:.0f}%, DD: {res_vol60['max_drawdown_pct']:.0f}%)", linewidth=1.5)
        plt.plot(res_vol40['equity_curve'], label=f"Vol Target 40% (Ret: {res_vol40['return_pct']:.0f}%, DD: {res_vol40['max_drawdown_pct']:.0f}%)", linewidth=1.5)
        
        plt.title("Volatility Targeting: Impact on Returns & Drawdowns")
        plt.yscale('log')
        plt.legend()
        plt.grid(True, which="both", ls="-", alpha=0.2)
        plt.savefig(f"{self.results_dir}/vol_targeting_comparison.png")
        print(f"\nChart saved to {self.results_dir}/vol_targeting_comparison.png")

if __name__ == "__main__":
    research = VolatilityTargetingResearch()
    research.load_data()
    research.run_comparison()
