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
        # Use earliest possible date for BTC to maximize data availability
        self.loader = BacktestDataLoader(start_date="2014-09-17")
        self.full_data = None
        self.results_dir = "research/wfa/results"
        
    def load_data(self):
        print("Loading full dataset...")
        self.full_data = self.loader.fetch_data()
        print(f"Loaded {len(self.full_data)} rows.")

    # ... (run_backtest remains unchanged) ...
    def run_backtest(self, df, buy_threshold, sell_threshold, window, strategy_type="adaptive"):
        """
        Runs a single backtest on the provided dataframe slice.
        Returns metrics dict.
        """
        initial_capital = 10000.0
        cash = initial_capital
        btc = 0
        equity = []
        trades = 0
        wins = 0
        gross_profit = 0
        gross_loss = 0
        
        # Calculate Z-Score if adaptive
        if strategy_type == "adaptive":
            rolling_mean = df['mvrv_proxy'].rolling(window=window).mean()
            rolling_std = df['mvrv_proxy'].rolling(window=window).std()
            df = df.copy()
            df['zscore'] = (df['mvrv_proxy'] - rolling_mean) / rolling_std
            df = df.dropna()
        elif strategy_type == "adaptive_precalc":
            # Z-Score already in df['zscore'], just ensure no NaNs
            df = df.dropna(subset=['zscore'])
        else:
            # Static Strategy: MVRV < 1.0 Buy, > 3.7 Sell
            df = df.copy()
            # No zscore needed, just use raw mvrv
        
        if df.empty:
            return None

        entry_price = 0
        
        for i, row in df.iterrows():
            price = row['price']
            
            # Logic
            buy_signal = False
            sell_signal = False
            
            if strategy_type == "adaptive" or strategy_type == "adaptive_precalc":
                if row['zscore'] < buy_threshold: buy_signal = True
                elif row['zscore'] > sell_threshold: sell_signal = True
            else:
                if row['mvrv_proxy'] < 1.0: buy_signal = True
                elif row['mvrv_proxy'] > 3.7: sell_signal = True
            
            if buy_signal and cash > 0:
                btc = cash / price
                cash = 0
                entry_price = price
                trades += 1
            elif sell_signal and btc > 0:
                cash = btc * price
                btc = 0
                trades += 1
                
                # Trade Result
                pnl = (price - entry_price) / entry_price
                if pnl > 0:
                    wins += 1
                    gross_profit += pnl
                else:
                    gross_loss += abs(pnl)
            
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
            
        # Win Rate & Profit Factor
        win_rate = (wins / (trades/2)) * 100 if trades > 0 else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 999 if gross_profit > 0 else 0
        
        # Calmar Ratio (Annualized Return / Max DD)
        # Simplified: Total Return / Max DD (Absolute)
        calmar = (total_return / abs(max_dd * 100)) if max_dd != 0 else 0
            
        return {
            "return_pct": total_return,
            "max_drawdown_pct": max_dd * 100,
            "trades": trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "calmar": calmar,
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
        
        periods = [
            {"name": "2016_2017_Bull", "start": "2016-01-01", "end": "2017-12-31"},
            {"name": "2018_Bear", "start": "2018-01-01", "end": "2018-12-31"},
            {"name": "2019_Recovery", "start": "2019-01-01", "end": "2019-12-31"},
            {"name": "2020_2021_Bull", "start": "2020-01-01", "end": "2021-12-31"},
            {"name": "2022_Bear", "start": "2022-01-01", "end": "2022-12-31"},
            {"name": "2023_2024_Cycle", "start": "2023-01-01", "end": "2024-11-29"},
            {"name": "Full_History", "start": "2016-01-01", "end": "2024-11-29"}
        ]
        
        all_results = []
        
        total_combinations = len(windows) * len(buy_thresholds) * len(sell_thresholds) * len(periods)
        print(f"Starting Enhanced Brute Force WFA. Total combinations: {total_combinations}")
        
        count = 0
        
        # 1. Iterate over Windows first to calculate Z-Score globally
        for w in windows:
            # Calculate Z-Score on FULL DATA to preserve history
            # Using min_periods=30 to allow signals quickly after data start
            df_with_z = self.full_data.copy()
            rolling_mean = df_with_z['mvrv_proxy'].rolling(window=w, min_periods=30).mean()
            rolling_std = df_with_z['mvrv_proxy'].rolling(window=w, min_periods=30).std()
            df_with_z['zscore'] = (df_with_z['mvrv_proxy'] - rolling_mean) / rolling_std
            
            # 2. Iterate over Periods
            for period in periods:
                # Slice Data (now contains valid Z-Scores)
                mask = (df_with_z.index >= period["start"]) & (df_with_z.index <= period["end"])
                period_data = df_with_z.loc[mask]
                
                if period_data.empty:
                    continue
                
                # Run Static Strategy Baseline (only once per period)
                # We pass strategy_type="static" so it ignores the zscore column we added
                static_res = self.run_backtest(period_data, 0, 0, 0, strategy_type="static")
                
                # 3. Iterate over Thresholds
                for buy, sell in itertools.product(buy_thresholds, sell_thresholds):
                    # Pass strategy_type="adaptive" and the pre-calculated zscore data
                    # Note: run_backtest needs to be adjusted to NOT re-calculate zscore if it's already there
                    # OR we just pass the window=0 or something to signal "use existing zscore"
                    # Actually, let's modify run_backtest to accept pre-calculated zscore
                    
                    res = self.run_backtest(period_data, buy, sell, w, strategy_type="adaptive_precalc")
                    
                    if res:
                        all_results.append({
                            "period": period["name"],
                            "window_days": w,
                            "buy_thresh": buy,
                            "sell_thresh": sell,
                            "return_pct": res["return_pct"],
                            "max_dd_pct": res["max_drawdown_pct"],
                            "trades": res["trades"],
                            "win_rate": res["win_rate"],
                            "profit_factor": res["profit_factor"],
                            "calmar": res["calmar"],
                            "static_return_pct": static_res["return_pct"] if static_res else 0,
                            "static_max_dd_pct": static_res["max_drawdown_pct"] if static_res else 0,
                            "outperformance": res["return_pct"] - (static_res["return_pct"] if static_res else 0)
                        })
                    
                    count += 1
                    if count % 100 == 0:
                        print(f"Processed {count}/{total_combinations}...")

        # Save Results
        df_results = pd.DataFrame(all_results)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.results_dir}/wfa_enhanced_{timestamp}.csv"
        df_results.to_csv(filename, index=False)
        print(f"Results saved to {filename}")
        
        # Analysis: Best Parameters per Period
        print("\nTop 3 Configurations per Period (by Calmar Ratio - Risk Adjusted Return):")
        for period in periods:
            print(f"\n--- {period['name']} ---")
            period_res = df_results[df_results['period'] == period['name']]
            if not period_res.empty:
                top = period_res.sort_values(by='calmar', ascending=False).head(3)
                print(top[['window_days', 'buy_thresh', 'sell_thresh', 'return_pct', 'max_dd_pct', 'calmar', 'static_max_dd_pct']])

if __name__ == "__main__":
    wfa = BruteForceWFA()
    wfa.load_data()
    wfa.run_wfa()
