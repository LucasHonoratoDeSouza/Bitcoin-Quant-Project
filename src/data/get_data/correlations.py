import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_macro_correlations():
    """
    Fetches historical data for BTC, S&P 500, and Gold, 
    and calculates the 90-day rolling correlation.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365) # Get 1 year of data
    
    tickers = {
        "BTC": "BTC-USD",
        "SPX": "^GSPC",
        "GOLD": "GC=F"
    }
    
    try:
        # Download data
        data = yf.download(list(tickers.values()), start=start_date, end=end_date, progress=False)["Close"]
        
        # Rename columns for clarity
        # yfinance might return MultiIndex if multiple tickers, or Series if one. 
        # With multiple, it's a DataFrame with ticker columns.
        # Note: yfinance column names match the ticker symbols.
        
        # Calculate returns
        returns = data.pct_change().dropna()
        
        # Calculate 90-day rolling correlation
        # We want correlation of BTC with others
        
        # Check if we have enough data
        if len(returns) < 90:
            return None

        # Correlation with SPX
        corr_spx = returns[tickers["BTC"]].rolling(window=90).corr(returns[tickers["SPX"]]).iloc[-1]
        
        # Correlation with Gold
        corr_gold = returns[tickers["BTC"]].rolling(window=90).corr(returns[tickers["GOLD"]]).iloc[-1]
        
        return {
            "corr_spx_90d": float(corr_spx),
            "corr_gold_90d": float(corr_gold)
        }
        
    except Exception as e:
        print(f"Error fetching correlations: {e}")
        return None

if __name__ == "__main__":
    print(get_macro_correlations())
