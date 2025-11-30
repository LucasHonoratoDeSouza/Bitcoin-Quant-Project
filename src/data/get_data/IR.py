import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")

def get_interest_rate():
    if not FRED_API_KEY:
        raise ValueError("FRED_API_KEY not found in environment variables")

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": "FEDFUNDS",
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

    current = df.iloc[-1]["value"]
    
    # Calculate changes safely
    try:
        one_month = df.iloc[-2]["value"]
        monthly_change = ((current - one_month) / one_month) * 100
    except IndexError:
        monthly_change = 0.0

    one_year_df = df[df["date"] == df.iloc[-1]["date"] - pd.DateOffset(years=1)]
    if one_year_df.empty:
        # Fallback to approx 12 months ago if exact date match fails
        if len(df) >= 13:
            one_year = df.iloc[-13]["value"]
            yearly_change = ((current - one_year) / one_year) * 100
        else:
            yearly_change = 0.0
    else:
        one_year = one_year_df["value"].iloc[0]
        yearly_change = ((current - one_year) / one_year) * 100

    return {
        "current_rate": current,
        "monthly_change_pct": monthly_change,
        "yearly_change_pct": yearly_change,
    }

if __name__ == "__main__":
    try:
        print(get_interest_rate())
    except Exception as e:
        print(f"Error: {e}")
