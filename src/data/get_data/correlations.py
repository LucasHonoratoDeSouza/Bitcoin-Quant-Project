import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_macro_correlations():

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365) # Get 1 year of data
    
    tickers = {
        "BTC": "BTC-USD",
        "SPX": "^GSPC",
        "GOLD": "GC=F"
    }
    
    try:

        data = yf.download(list(tickers.values()), start=start_date, end=end_date, progress=False)["Close"]
        
        returns = data.pct_change().dropna()

        if len(returns) < 90:
            return None

        corr_spx = returns[tickers["BTC"]].rolling(window=90).corr(returns[tickers["SPX"]]).iloc[-1]

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
