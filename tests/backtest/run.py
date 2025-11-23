import sys
import os
from pathlib import Path

# Add project root to python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

from tests.backtest.data_loader import BacktestDataLoader
from tests.backtest.engine import BacktestEngine
import pandas as pd

def run_backtest():
    # 1. Load Data (2020 to Present for a good mix of Bull/Bear)
    loader = BacktestDataLoader(start_date="2020-01-01")
    loader.fetch_data()
    generator = loader.generator()
    
    # 2. Run Engine
    engine = BacktestEngine(initial_capital=10000.0)
    results_df = engine.run(generator)
    
    # 3. Generate Report
    engine.generate_report(results_df)
    
    # 4. Save Results
    results_df.to_csv("tests/backtest/results.csv", index=False)
    print("Detailed results saved to tests/backtest/results.csv")

if __name__ == "__main__":
    run_backtest()
