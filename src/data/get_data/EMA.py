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
    
    current_price = prices[-1]
    prev_price = prices[-2] if len(prices) > 1 else current_price
    daily_change_pct = ((current_price - prev_price) / prev_price) * 100
    
    # Weekly Change (7 days ago)
    price_7d = prices[-8] if len(prices) > 7 else prices[0]
    weekly_change_pct = ((current_price - price_7d) / price_7d) * 100
    
    # Monthly Change (30 days ago)
    price_30d = prices[-31] if len(prices) > 30 else prices[0]
    monthly_change_pct = ((current_price - price_30d) / price_30d) * 100
    
    return {
        "current_price": float(current_price),
        "ema_365": float(ema_365.iloc[-1]),
        "daily_change_pct": float(daily_change_pct),
        "weekly_change_pct": float(weekly_change_pct),
        "monthly_change_pct": float(monthly_change_pct)
    }

if __name__ == "__main__":
    try:
        print(get_ema())
    except Exception as e:
        print(f"Error: {e}")
