import requests
import pandas as pd
from datetime import datetime, timedelta

FRED_API_KEY = ""

def get_interest_rate():
    """
    Returns Fed Funds Rate (interest rate) levels and % changes.
    """
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": "FEDFUNDS",
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "frequency": "m" 
    }

    r = requests.get(url, params=params).json()
    if "observations" not in r:
        raise RuntimeError(f"Erro FRED: {r}")

    df = pd.DataFrame(r["observations"])
    df = df[df["value"] != "."]
    df["value"] = df["value"].astype(float)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    current = df.iloc[-1]["value"]
    one_month = df.iloc[-2]["value"]
    one_year = df[df["date"] == df.iloc[-1]["date"] - pd.DateOffset(years=1)]

    if one_year.empty:
        one_year = df.iloc[-13]["value"]
    else:
        one_year = one_year["value"].iloc[0]

    return {
        "current_rate": current,
        "monthly_change_pct": ((current - one_month) / one_month) * 100,
        "yearly_change_pct": ((current - one_year) / one_year) * 100,
    }

print(get_interest_rate())
