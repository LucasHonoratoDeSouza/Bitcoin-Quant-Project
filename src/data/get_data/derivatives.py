import requests
import pandas as pd

def get_binance_derivatives():
    """
    Fetches derivatives data from Binance Futures API:
    1. Open Interest (BTCUSDT)
    2. Long/Short Ratio (Global Accounts)
    3. Funding Rate (Proxy for Basis/Sentiment)
    """
    base_url = "https://fapi.binance.com"
    symbol = "BTCUSDT"
    
    metrics = {}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # 1. Open Interest
    try:
        url_oi = f"{base_url}/fapi/v1/openInterest"
        r_oi = requests.get(url_oi, params={"symbol": symbol}, headers=headers).json()
        metrics["open_interest"] = float(r_oi["openInterest"])
    except Exception as e:
        print(f"Error fetching Open Interest: {e}")
        metrics["open_interest"] = None

    # 2. Long/Short Ratio (Top Trader Account Ratio is often more reliable for API)
    # Trying topLongShortAccountRatio first as global might be restricted
    metrics["long_short_ratio"] = None
    for period in ["5m", "1h", "1d"]:
        try:
            url_lsr = f"{base_url}/fapi/v1/topLongShortAccountRatio"
            params_lsr = {"symbol": symbol, "period": period, "limit": 1}
            response_lsr = requests.get(url_lsr, params=params_lsr, headers=headers)
            
            if response_lsr.status_code == 200:
                r_lsr = response_lsr.json()
                if r_lsr:
                    metrics["long_short_ratio"] = float(r_lsr[0]["longShortRatio"])
                    metrics["long_account"] = float(r_lsr[0]["longAccount"])
                    metrics["short_account"] = float(r_lsr[0]["shortAccount"])
                    break # Success
        except Exception as e:
            print(f"Error fetching Long/Short Ratio ({period}): {e}")
    
    if metrics["long_short_ratio"] is None:
         print("Failed to fetch Long/Short Ratio after retries.")

    # 3. Funding Rate & Basis (Premium Index)
    try:
        url_premium = f"{base_url}/fapi/v1/premiumIndex"
        r_premium = requests.get(url_premium, params={"symbol": symbol}, headers=headers).json()
        
        # Funding Rate
        metrics["funding_rate"] = float(r_premium["lastFundingRate"])
        
        # Basis calculation (Mark Price - Index Price)
        mark_price = float(r_premium["markPrice"])
        index_price = float(r_premium["indexPrice"])
        basis = (mark_price - index_price) / index_price
        metrics["basis_pct"] = basis * 100
        
    except Exception as e:
        print(f"Error fetching Funding/Basis: {e}")
        metrics["funding_rate"] = None
        metrics["basis_pct"] = None

    return metrics

if __name__ == "__main__":
    import json
    print(json.dumps(get_binance_derivatives(), indent=4))
