import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")

def get_dollar_strength():
    if not FRED_API_KEY:
        raise ValueError("FRED_API_KEY not found in environment variables")

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": "DTWEXBGS",
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "frequency": "d" 
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

    current_index = df.iloc[-1]["value"]
    

    try:
        one_month = df[df["date"] <= df.iloc[-1]["date"] - pd.DateOffset(months=1)].iloc[-1]["value"]
        monthly_change = ((current_index - one_month) / one_month) * 100
    except IndexError:
        monthly_change = 0.0

    return {
        "current_index": current_index,
        "monthly_change_pct": monthly_change
    }

if __name__ == "__main__":
    try:
        print(get_dollar_strength())
    except Exception as e:
        print(f"Error: {e}")
