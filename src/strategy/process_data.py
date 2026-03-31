from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

from src.features.cycle import BitcoinCycle
from src.features.seasonality import BitcoinSeasonality
from src.utils.project_paths import PROCESSED_DATA_DIR, latest_raw_data_file


LOGGER = logging.getLogger(__name__)

# --- Helper Functions ---

def fetch_historical_context(end_date_str, window_days=1460):
    """
    Fetches historical BTC price data to calculate long-term rolling metrics (Z-Score).
    """
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    start_date = end_date - timedelta(days=window_days + 365) # Buffer for MA calculation
    
    LOGGER.info(
        "Fetching historical context from %s to %s",
        start_date.strftime("%Y-%m-%d"),
        end_date_str,
    )
    
    try:
        df = yf.download("BTC-USD", start=start_date.strftime('%Y-%m-%d'), end=end_date_str, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = df.rename(columns={"Close": "price"})
        
        # Calculate MVRV Proxy (Price / 365 SMA)
        df['sma_365'] = df['price'].rolling(window=365).mean()
        df['mvrv_proxy'] = df['price'] / df['sma_365']
        
        # Calculate Z-Score (4-year window)
        # We use the last available value as the current Z-Score
        rolling_mean = df['mvrv_proxy'].rolling(window=window_days, min_periods=365).mean()
        rolling_std = df['mvrv_proxy'].rolling(window=window_days, min_periods=365).std()
        
        df['mvrv_zscore'] = (df['mvrv_proxy'] - rolling_mean) / rolling_std
        
        last_z = df['mvrv_zscore'].iloc[-1]
        
        if pd.isna(last_z):
            LOGGER.warning("Z-Score is NaN, defaulting to 0.")
            return 0.0
            
        return float(last_z)
        
    except Exception as e:
        LOGGER.warning("Error fetching historical context: %s", e)
        return 0.0

# --- Logic Functions ---

def check_cycle_phase(date_str):
    cycle = BitcoinCycle()
    return cycle.get_phase(date_str)

def check_seasonality(date_str):
    seasonality = BitcoinSeasonality()
    stats = seasonality.get_seasonality(date_str)
    return stats["status"] in ["BULLISH", "VERY BULLISH"]

def check_correlations(data):
    """
    Returns True if BTC is highly correlated with Risk Assets (SPX) > 0.5
    or acting as Safe Haven (Gold) > 0.5.
    """
    corr_data = data["metrics"].get("macro_correlations")
    if not corr_data: 
        return {"is_high_corr_spx": False, "is_high_corr_gold": False}
    
    return {
        "is_high_corr_spx": corr_data["corr_spx_90d"] > 0.5,
        "is_high_corr_gold": corr_data["corr_gold_90d"] > 0.5
    }

def is_accumulation_zone(data):
    # Logic: RUP < 0.2 AND MVRV < 1.2 AND SOPR < 1
    mvrv = data["metrics"].get("mvrv")
    rup = data["metrics"].get("rup")
    sopr = data["metrics"].get("sopr")
    
    if mvrv is None or rup is None or sopr is None:
        return None
    
    is_acc = (rup < 0.2) and (mvrv < 1.2) and (sopr < 1.0)
    return is_acc

def is_overheated(data):
    # Logic: (Mayer Multiple > 2.5 AND SOPR > 1) OR (RUP > 2.5)
    mm = data["metrics"].get("mayer_multiple")
    sopr = data["metrics"].get("sopr")
    rup = data["metrics"].get("rup")
    
    if rup is not None and rup > 2.5:
        return True
        
    if mm is not None and sopr is not None:
        if mm > 2.5 and sopr > 1.0:
            return True
            
    return False

def is_fear_extreme(data):
    fng = data["metrics"].get("fear_and_greed")
    if not fng: return None
    return fng["value"] < 20

def is_greed_extreme(data):
    fng = data["metrics"].get("fear_and_greed")
    if not fng: return None
    return fng["value"] > 70

def check_liquidity(data):
    """
    Returns True if Liquidity is favorable (Good), False otherwise.
    """
    ir_data = data["metrics"].get("interest_rate")
    m2_data = data["metrics"].get("m2_supply")
    
    if not ir_data or not m2_data:
        return False
        
    ir_val = ir_data["current_rate"]
    m2_yoy = m2_data["m2_year_pct"]
    
    # 1. M2 Booming (> 5% YoY) -> Good
    if m2_yoy > 5.0:
        return True
        
    # 2. Low Rates (< 2%) -> Good
    if ir_val < 2.0:
        return True
        
    return False

def check_inflation_flags(data):
    """
    Returns boolean flags for inflation.
    """
    inf_data = data["metrics"].get("inflation")
    if not inf_data: 
        return {"is_inflation_high": False, "is_inflation_falling": False}
    
    cpi_yoy = inf_data["yoy_inflation_pct"]
    trend = inf_data.get("inflation_trend", 0.0)
    
    return {
        "is_inflation_high": cpi_yoy > 3.0,
        "is_inflation_falling": trend < 0
    }

def check_trend(data):
    """
    Returns True if Price > EMA 365 (Long Term Bull Trend).
    """
    price_data = data["metrics"].get("btc_price_ema_365")
    if not price_data or isinstance(price_data, float): return False # Handle legacy float format if needed
    
    # Support both old float format and new dict format for backward compatibility
    if isinstance(price_data, dict):
        return price_data["current_price"] > price_data["ema_365"]
    return False

def check_derivatives_risk(data):
    """
    Returns True if Derivatives show High Risk (Cascading Liquidation Risk).
    Logic: High Funding Rate (> 0.01%) AND High Open Interest (Contextual check needed, but simplified here).
    For now, we check if Funding is very positive (Over-leveraged Longs).
    """
    deriv_data = data["metrics"].get("derivatives")
    if not deriv_data: return False
    
    funding = deriv_data.get("funding_rate")
    if funding is None: return False
    
    # Funding > 0.01% (Standard baseline) is normal bullish.
    # Funding > 0.03% starts getting overheated.
    return funding > 0.03

def check_volatility_opportunity(data):
    """
    Returns True if there is a sharp drop in a Bull Trend (Buy the Dip).
    Logic: Daily Drop < -5% AND Price > EMA 365.
    """
    price_data = data["metrics"].get("btc_price_ema_365")
    if not price_data or not isinstance(price_data, dict): return False
    
    is_bullish = price_data["current_price"] > price_data["ema_365"]
    is_sharp_drop = price_data["daily_change_pct"] < -5.0
    
    return is_bullish and is_sharp_drop

def get_market_context(data):
    """
    Extracts raw market data and calculates extension from EMA.
    """
    price_data = data["metrics"].get("btc_price_ema_365")
    if not price_data or not isinstance(price_data, dict):
        return None
        
    current_price = price_data["current_price"]
    ema = price_data["ema_365"]
    
    # Calculate extension from EMA (How stretched is the move?)
    extension_pct = ((current_price - ema) / ema) * 100
    
    return {
        "current_price": current_price,
        "daily_change_pct": price_data["daily_change_pct"],
        "weekly_change_pct": price_data.get("weekly_change_pct", 0.0),
        "monthly_change_pct": price_data.get("monthly_change_pct", 0.0),
        "ema_365": ema,
        "price_vs_ema_pct": extension_pct # > 100% is usually top territory, < -30% is bottom
    }

# --- Main Processing ---

def process_daily_data(raw_file_path: str | Path, output_path: Path | None = None) -> dict:
    raw_file_path = Path(raw_file_path)
    LOGGER.info("Processing %s", raw_file_path)

    with raw_file_path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)
        
    # 0. Fetch Historical Context for Z-Score
    # We need the date from the timestamp
    date_str = raw_data["timestamp"][:10]
    z_score = fetch_historical_context(date_str)
    LOGGER.info("Calculated MVRV Z-Score: %.2f", z_score)

    processed = {
        "timestamp": raw_data["timestamp"],
        "raw_source": str(raw_file_path),
        "market_data": get_market_context(raw_data),
        "metrics": {
            "mvrv": raw_data["metrics"].get("mvrv"),
            "mvrv_zscore": z_score, # NEW: Dynamic Metric
            "sopr": raw_data["metrics"].get("sopr"),
            "rup": raw_data["metrics"].get("rup"),
            "mayer_multiple": raw_data["metrics"].get("mayer_multiple"),
            "fear_and_greed": raw_data["metrics"].get("fear_and_greed", {}).get("value"),
            "interest_rate": raw_data["metrics"].get("interest_rate", {}).get("current_rate"),
            "m2_yoy": raw_data["metrics"].get("m2_supply", {}).get("m2_year_pct"),
            "inflation_yoy": raw_data["metrics"].get("inflation", {}).get("yoy_inflation_pct"),
            "funding_rate": raw_data["metrics"].get("derivatives", {}).get("funding_rate")
        },
        "flags": {}
    }
    
    # 1. Cycle Analysis
    # We keep the phase name as it's not a boolean, but useful context
    processed["market_cycle_phase"] = check_cycle_phase(raw_data["timestamp"][:10])["phase"]
    
    # 2. On-Chain States (Booleans)
    processed["flags"]["is_accumulation"] = is_accumulation_zone(raw_data)
    processed["flags"]["is_overheated"] = is_overheated(raw_data)
    
    # 3. Sentiment (Booleans)
    processed["flags"]["is_fear_extreme"] = is_fear_extreme(raw_data)
    processed["flags"]["is_greed_extreme"] = is_greed_extreme(raw_data)
    
    # 4. Macro (Booleans)
    processed["flags"]["is_liquidity_good"] = check_liquidity(raw_data)
    
    inf_flags = check_inflation_flags(raw_data)
    processed["flags"]["is_inflation_high"] = inf_flags["is_inflation_high"]
    processed["flags"]["is_inflation_falling"] = inf_flags["is_inflation_falling"]
    
    # 5. Advanced Market Structure (Booleans)
    processed["flags"]["is_bull_trend"] = check_trend(raw_data)
    processed["flags"]["is_derivatives_risk"] = check_derivatives_risk(raw_data)
    processed["flags"]["is_volatility_opportunity"] = check_volatility_opportunity(raw_data)
    
    # 6. New Metrics (Seasonality & Correlations)
    processed["flags"]["is_positive_seasonality"] = check_seasonality(raw_data["timestamp"][:10])
    
    corr_flags = check_correlations(raw_data)
    processed["flags"]["is_high_corr_spx"] = corr_flags["is_high_corr_spx"]
    processed["flags"]["is_high_corr_gold"] = corr_flags["is_high_corr_gold"]
    
    # Save to processed folder
    output_path = output_path or PROCESSED_DATA_DIR / f"processed_data_{date_str}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(processed, f, indent=4)
        
    LOGGER.info("Processed data saved to %s", output_path)
    return {
        "data": processed,
        "output_path": output_path,
    }

if __name__ == "__main__":
    raw_path = latest_raw_data_file()

    if raw_path:
        process_daily_data(raw_path)
    else:
        raise FileNotFoundError("No raw data found. Run 'python main.py download' first.")
