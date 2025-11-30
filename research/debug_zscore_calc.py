import sys
import os
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tests.backtest.data_loader import BacktestDataLoader

loader = BacktestDataLoader(start_date="2015-01-01")
full_data = loader.fetch_data()

print(f"Data Start: {full_data.index.min()}")
print(f"Data End: {full_data.index.max()}")
print(f"Rows: {len(full_data)}")

# Calculate Z-Score
window = 365
rolling_mean = full_data['mvrv_proxy'].rolling(window=window, min_periods=365).mean()
rolling_std = full_data['mvrv_proxy'].rolling(window=window, min_periods=365).std()
full_data['zscore'] = (full_data['mvrv_proxy'] - rolling_mean) / rolling_std

print("\n--- Z-Score Check (Jan 2016) ---")
jan_2016 = full_data.loc['2016-01-01':'2016-01-10']
print(jan_2016[['price', 'mvrv_proxy', 'zscore']])

print("\n--- First Valid Z-Score ---")
valid_z = full_data.dropna(subset=['zscore'])
if not valid_z.empty:
    print(valid_z[['price', 'mvrv_proxy', 'zscore']].head())
else:
    print("No valid Z-Scores found.")
