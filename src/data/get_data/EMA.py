import requests
import pandas as pd

def get_ema():
    """
    Fetches 365 days of BTC prices from CoinGecko API and returns
    the most recent 365-day EMA value.
    """
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    
    params = {
        "vs_currency": "usd",
        "days": "365",
        "interval": "daily"
    }

    response = requests.get(url, params=params)
    data = response.json()
    
    prices = [p[1] for p in data["prices"]]
    
    series = pd.Series(prices)

    ema_365 = series.ewm(span=365, adjust=False).mean()
    
    return float(ema_365.iloc[-1])
