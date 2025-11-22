import json
import os
from datetime import datetime
from pathlib import Path
import sys

# Add project root to python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

# Import all data fetchers
from src.data.get_data.EMA import get_ema
from src.data.get_data.IR import get_interest_rate
from src.data.get_data.GLI import get_m2_pct_changes
from src.data.get_data.MVRV import get_mvrv
from src.data.get_data.MVRVCrosses import get_mvrvc
from src.data.get_data.MayerMultiple import get_mm
from src.data.get_data.RUP import get_rup
from src.data.get_data.SOPR import get_sopr
from src.data.get_data.dollar_strength import get_dollar_strength
from src.data.get_data.inflation import get_inflation_data
from src.data.get_data.derivatives import get_binance_derivatives
from src.data.get_data.sentiment import get_fear_and_greed

def download_all_data():
    print("Starting daily data download...")
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "metrics": {}
    }

    # List of fetchers and their keys
    fetchers = [
        ("btc_price_ema_365", get_ema),
        ("interest_rate", get_interest_rate),
        ("m2_supply", get_m2_pct_changes),
        ("mvrv", get_mvrv),
        ("mvrv_crosses", get_mvrvc),
        ("mayer_multiple", get_mm),
        ("rup", get_rup),
        ("sopr", get_sopr),
        ("dollar_strength", get_dollar_strength),
        ("inflation", get_inflation_data),
        ("derivatives", get_binance_derivatives),
        ("fear_and_greed", get_fear_and_greed)
    ]

    for key, func in fetchers:
        try:
            print(f"Fetching {key}...")
            result = func()
            data["metrics"][key] = result
            print(f"✅ {key}: Success")
        except Exception as e:
            print(f"❌ {key}: Failed - {e}")
            data["metrics"][key] = None

    # Save to file
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"daily_data_{datetime.now().strftime('%Y-%m-%d')}.json"
    output_path = output_dir / filename
    
    with open(output_path, "w") as f:
        json.dump(data, f, indent=4)
    
    print(f"\nData saved to {output_path}")
    return data

if __name__ == "__main__":
    download_all_data()
