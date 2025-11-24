import pandas as pd
import pandas_datareader.data as web
from fredapi import Fred
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class RealDataFetcher:
    def __init__(self):
        self.fred_key = os.getenv("FRED_API_KEY")
        self.fred = Fred(api_key=self.fred_key) if self.fred_key else None

    def fetch_macro_data(self, start_date, end_date):
        """
        Fetches 10Y Yield (DGS10) and M2 Money Supply (M2SL) from FRED.
        """
        if not self.fred:
            print("⚠️ FRED_API_KEY not found. Using neutral macro data.")
            return None

        print("Fetching Macro Data from FRED...")
        try:
            # 10-Year Treasury Yield
            dgs10 = self.fred.get_series('DGS10', observation_start=start_date, observation_end=end_date)
            dgs10.name = "interest_rate"

            # M2 Money Supply (Monthly, need to forward fill)
            m2 = self.fred.get_series('M2SL', observation_start=start_date, observation_end=end_date)
            m2_yoy = m2.pct_change(periods=12) * 100 # YoY Growth
            m2_yoy.name = "m2_yoy"

            # Combine
            macro_df = pd.concat([dgs10, m2_yoy], axis=1)
            macro_df = macro_df.fillna(method='ffill') # Forward fill M2
            
            return macro_df
        except Exception as e:
            print(f"❌ Error fetching FRED data: {e}")
            return None

    def fetch_mvrv_data(self):
        """
        Fetches MVRV Z-Score or Ratio from a public source.
        For now, we will use a placeholder or try to fetch from a known public repo.
        If fails, returns None (triggering synthetic fallback).
        """
        # TODO: Implement actual scraping or API call to ChainExposed/Glassnode if key available.
        # For now, we return None to let the DataLoader use the synthetic proxy (Price/365SMA)
        # which is a very good approximation for MVRV Ratio.
        return None

if __name__ == "__main__":
    fetcher = RealDataFetcher()
    macro = fetcher.fetch_macro_data("2020-01-01", "2025-01-01")
    if macro is not None:
        print(macro.head())
        print(macro.tail())
