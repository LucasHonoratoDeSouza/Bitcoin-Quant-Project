import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class BacktestDataLoader:
    """
    Loads historical BTC data and generates synthetic indicators 
    to mimic the production environment for backtesting.
    """
    
    def __init__(self, start_date="2015-01-01", end_date=None):
        self.start_date = start_date
        self.end_date = end_date if end_date else datetime.now().strftime("%Y-%m-%d")
        self.data = None

    def fetch_data(self):
        print(f"Fetching historical data ({self.start_date} to {self.end_date})...")
        self.data = yf.download("BTC-USD", start=self.start_date, end=self.end_date, progress=False)
        
        # Flatten MultiIndex columns if present (yfinance update)
        if isinstance(self.data.columns, pd.MultiIndex):
            self.data.columns = self.data.columns.get_level_values(0)
            
        self.data = self.data.rename(columns={"Close": "price", "High": "high", "Low": "low", "Open": "open", "Volume": "volume"})
        self._calculate_synthetic_indicators()
        return self.data

    def _calculate_synthetic_indicators(self):
        df = self.data
        
        # 1. Trend & MVRV Proxy
        # MVRV Proxy = Price / 365 SMA (Realized Price proxy)
        df["sma_365"] = df["price"].rolling(window=365).mean()
        df["mvrv_proxy"] = df["price"] / df["sma_365"]
        
        # 2. Mayer Multiple (Same as MVRV proxy logic but typically 200d, we use 200 here for variety)
        df["sma_200"] = df["price"].rolling(window=200).mean()
        df["mayer_multiple"] = df["price"] / df["sma_200"]
        
        # 3. Sentiment Proxy (RSI + Volatility)
        # RSI 14
        delta = df["price"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))
        
        # Fear & Greed Proxy: RSI (0-100) is a decent proxy. 
        # We can add volatility to make it more robust.
        df["volatility"] = df["price"].pct_change().rolling(window=30).std()
        # Simple proxy: RSI is the main driver for F&G in this sim
        df["fear_and_greed"] = df["rsi"] 
        
        # 4. Macro Proxy (Yield 10Y - simplified constant or random walk if needed, 
        # but for now we assume neutral macro to test alpha of crypto logic, 
        # or we can fetch ^TNX if we want)
        # Let's assume neutral macro (0.0 score) to isolate crypto strategy performance
        df["interest_rate"] = 2.5 # Neutral
        df["m2_yoy"] = 5.0 # Neutral
        
        # 5. Cycle Phase
        # Hardcoded Halving Dates
        halvings = [
            datetime(2012, 11, 28),
            datetime(2016, 7, 9),
            datetime(2020, 5, 11),
            datetime(2024, 4, 20)
        ]
        
        def get_phase(date):
            # Simple logic: 
            # 0-1.5 years after halving: Expansion
            # 1.5-2.5 years after: Bear
            # 2.5-4.0 years after: Accumulation
            
            # Find last halving
            last_halving = halvings[0]
            for h in halvings:
                if date >= h:
                    last_halving = h
                else:
                    break
            
            days_since = (date - last_halving).days
            years_since = days_since / 365.25
            
            if years_since < 1.5: return "Post-Halving Expansion"
            if years_since < 2.5: return "Bear Market / Distribution"
            return "Accumulation" # Includes Pre-Halving

        df["cycle_phase"] = df.index.map(lambda d: get_phase(d))
        
        # Drop NaN (initial rolling windows)
        self.data = df.dropna()

    def generator(self):
        """
        Yields a dictionary mimicking the production JSON format for each day.
        """
        for date, row in self.data.iterrows():
            # Construct the 'metrics' dict expected by QuantScorer
            metrics = {
                "mvrv": row["mvrv_proxy"], # Using proxy
                "mayer_multiple": row["mayer_multiple"],
                "rup": row["mvrv_proxy"] * 0.5, # Rough proxy for RUP
                "sopr": 1.0, # Hard to simulate without UTXO set, assume neutral
                "fear_and_greed": row["fear_and_greed"],
                "interest_rate": row["interest_rate"],
                "m2_yoy": row["m2_yoy"],
                "inflation": {"yoy_inflation_pct": 2.0}, # Neutral
                "derivatives": {"funding_rate": 0.01} # Neutral
            }
            
            # Construct 'market_data'
            market_data = {
                "current_price": row["price"],
                "daily_change_pct": (row["price"] - row["open"]) / row["open"] * 100, # Approx
                "ema_365": row["sma_365"], # Using SMA as EMA proxy for simplicity or calc EMA
                "price_vs_ema_pct": ((row["price"] - row["sma_365"]) / row["sma_365"]) * 100
            }
            
            # Construct 'flags' (QuantScorer uses raw metrics mostly, but flags help)
            flags = {
                "is_bull_trend": row["price"] > row["sma_365"],
                "is_fear_extreme": row["fear_and_greed"] < 30,
                "is_greed_extreme": row["fear_and_greed"] > 70,
                "is_positive_seasonality": True # Simplify
            }
            
            yield {
                "timestamp": date.isoformat(),
                "market_cycle_phase": row["cycle_phase"],
                "metrics": metrics,
                "market_data": market_data,
                "flags": flags
            }

if __name__ == "__main__":
    loader = BacktestDataLoader(start_date="2020-01-01")
    data = loader.fetch_data()
    print(f"Loaded {len(data)} days of data.")
    
    # Test generator
    gen = loader.generator()
    print("Sample Day:", next(gen))
