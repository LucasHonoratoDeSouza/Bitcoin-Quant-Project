import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")

def get_inflation_data():
    if not FRED_API_KEY:
        raise ValueError("FRED_API_KEY not found in environment variables")

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": "CPIAUCSL",
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "frequency": "m" 
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    r = response.json()
    
    if "observations" not in r:
        raise RuntimeError(f"Erro FRED: {r}")

    df = pd.DataFrame(r["observations"])
    df = df[df["value"] != "."]
    df["value"] = df["value"].astype(float)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    if df.empty:
        return None

    current_cpi = df.iloc[-1]["value"]

    one_year_df = df[df["date"] == df.iloc[-1]["date"] - pd.DateOffset(years=1)]
    
    if one_year_df.empty:
        if len(df) >= 13:
            one_year_cpi = df.iloc[-13]["value"]
            yoy_inflation = ((current_cpi - one_year_cpi) / one_year_cpi) * 100
        else:
            yoy_inflation = 0.0
    else:
        one_year_cpi = one_year_df["value"].iloc[0]
        yoy_inflation = ((current_cpi - one_year_cpi) / one_year_cpi) * 100

    prev_cpi = df.iloc[-2]["value"]
    prev_year_df = df[df["date"] == df.iloc[-2]["date"] - pd.DateOffset(years=1)]
    
    if prev_year_df.empty:
        if len(df) >= 14:
            prev_year_cpi = df.iloc[-14]["value"]
            prev_yoy_inflation = ((prev_cpi - prev_year_cpi) / prev_year_cpi) * 100
        else:
            prev_yoy_inflation = yoy_inflation # Assume flat if no data
    else:
        prev_year_cpi = prev_year_df["value"].iloc[0]
        prev_yoy_inflation = ((prev_cpi - prev_year_cpi) / prev_year_cpi) * 100

    inflation_trend = yoy_inflation - prev_yoy_inflation

    return {
        "current_cpi": current_cpi,
        "yoy_inflation_pct": yoy_inflation,
        "prev_yoy_inflation_pct": prev_yoy_inflation,
        "inflation_trend": inflation_trend # Positive = Rising, Negative = Falling (Cuts)
    }

if __name__ == "__main__":
    try:
        print(get_inflation_data())
    except Exception as e:
        print(f"Error: {e}")
