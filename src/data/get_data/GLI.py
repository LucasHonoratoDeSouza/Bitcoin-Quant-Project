import requests
import pandas as pd

FRED_API_KEY = ""

def get_m2_pct_changes():
    url = (
        f"https://api.stlouisfed.org/fred/series/observations?"
        f"series_id=M2SL&api_key={FRED_API_KEY}&file_type=json"
    )

    r = requests.get(url).json()
    if "observations" not in r:
        raise RuntimeError(f"Erro FRED: {r}")

    df = pd.DataFrame(r["observations"])
    df = df[df["value"] != "."]
    df["value"] = df["value"].astype(float)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    df["m2_monthly_pct"] = df["value"].pct_change() * 100

    df["m2_quarter_pct"] = df["value"].pct_change(3) * 100

    df["m2_year_pct"] = df["value"].pct_change(12) * 100

    latest = df.iloc[-1][["m2_monthly_pct", "m2_quarter_pct", "m2_year_pct"]]

    return latest.to_dict()
