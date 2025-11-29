import sys
import os
import pandas as pd
import numpy as np
import itertools
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.backtest.data_loader import BacktestDataLoader

class BruteForceWFA:
    def __init__(self):
        self.loader = BacktestDataLoader(start_date="2015-01-01")
        self.full_data = None
        self.results_dir = "research/wfa/results"
        
    def load_data(self):
        print("Loading full dataset...")
        self.full_data = self.loader.fetch_data()
        print(f"Loaded {len(self.full_data)} rows.")

    def run_backtest(self, df, buy_threshold, sell_threshold, window):
        """
        Runs a single backtest on the provided dataframe slice.
        Returns metrics dict.
        """
        # Calculate Z-Score for this specific window
        # Note: In a real WFA, we should calculate Z-Score on the fly to avoid lookahead bias.
        # However, for 'rolling' z-score, it only looks at past data anyway, so it's safe-ish 
        # as long as the window is fully contained in the past relative to the decision point.
        
        # We need to calculate z-score on the slice provided? 
        # No, we should calculate z-score on the full dataset first (rolling), 
        # then slice the dataframe for the test period.
        # The rolling calculation itself respects causality.
        
        initial_capital = 10000.0
        cash = initial_capital
        btc = 0
        equity = []
        trades = 0
        
        # We assume 'mvrv_zscore' is already in df for the specific window being tested
        # But wait, the Z-Score depends on the window size parameter.
        # So we must calculate it here.
        
        rolling_mean = df['mvrv_proxy'].rolling(window=window).mean()
        rolling_std = df['mvrv_proxy'].rolling(window=window).std()
        df = df.copy()
        df['zscore'] = (df['mvrv_proxy'] - rolling_mean) / rolling_std
        
        # Drop NaN from initial rolling window
        df = df.dropna()
        
        if df.empty:
            return None

        for i, row in df.iterrows():
            price = row['price']
            
            # Logic
            if row['zscore'] < buy_threshold and cash > 0:
                btc = cash / price
                cash = 0
                trades += 1
            elif row['zscore'] > sell_threshold and btc > 0:
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
            "final_equity": final_equity
        }

    def run_wfa(self):
        """
        Brute Force Walk-Forward Analysis
        """
        # Parameters to Test
        windows = [365, 730, 1095, 1460] # 1y, 2y, 3y, 4y
        buy_thresholds = [-1.0, -1.2, -1.5, -1.8, -2.0]
        sell_thresholds = [1.5, 2.0, 2.5, 3.0, 3.5]
        
        # Walk-Forward Periods (Train on X, Test on Y is the standard, 
        # but for Brute Force we often just want to see performance across different fixed periods 
        # to check robustness).
        # Let's define specific market regimes to test robustness:
        periods = [
            {"name": "2017_Bull", "start": "2017-01-01", "end": "2017-12-31"},
            {"name": "2018_Bear", "start": "2018-01-01", "end": "2018-12-31"},
            {"name": "2019_Recovery", "start": "2019-01-01", "end": "2019-12-31"},
            {"name": "2020_2021_Bull", "start": "2020-01-01", "end": "2021-12-31"},
            {"name": "2022_Bear", "start": "2022-01-01", "end": "2022-12-31"},
            {"name": "2023_2024_Cycle", "start": "2023-01-01", "end": "2024-11-29"},
            {"name": "Full_History", "start": "2016-01-01", "end": "2024-11-29"}
        ]
        
        all_results = []
        
        total_combinations = len(windows) * len(buy_thresholds) * len(sell_thresholds) * len(periods)
        print(f"Starting Brute Force WFA. Total combinations: {total_combinations}")
        
        count = 0
        for period in periods:
            # Slice Data
            mask = (self.full_data.index >= period["start"]) & (self.full_data.index <= period["end"])
            period_data = self.full_data.loc[mask]
            
            if period_data.empty:
                continue
                
            for w, buy, sell in itertools.product(windows, buy_thresholds, sell_thresholds):
                res = self.run_backtest(period_data, buy, sell, w)
                
                if res:
                    all_results.append({
                        "period": period["name"],
                        "window_days": w,
                        "buy_thresh": buy,
                        "sell_thresh": sell,
                        "return_pct": res["return_pct"],
                        "max_dd_pct": res["max_drawdown_pct"],
                        "trades": res["trades"]
                    })
                
                count += 1
                if count % 100 == 0:
                    print(f"Processed {count}/{total_combinations}...")

        # Save Results
        df_results = pd.DataFrame(all_results)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.results_dir}/wfa_bruteforce_{timestamp}.csv"
        df_results.to_csv(filename, index=False)
        print(f"Results saved to {filename}")
        
        # Analysis: Best Parameters per Period
        print("\nTop 3 Configurations per Period (by Return):")
        for period in periods:
            print(f"\n--- {period['name']} ---")
            period_res = df_results[df_results['period'] == period['name']]
            if not period_res.empty:
                top = period_res.sort_values(by='return_pct', ascending=False).head(3)
                print(top[['window_days', 'buy_thresh', 'sell_thresh', 'return_pct', 'max_dd_pct', 'trades']])

if __name__ == "__main__":
    wfa = BruteForceWFA()
    wfa.load_data()
    wfa.run_wfa()
