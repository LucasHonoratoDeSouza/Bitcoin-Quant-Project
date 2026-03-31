from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from src.data.get_data.EMA import get_ema
from src.data.get_data.GLI import get_m2_pct_changes
from src.data.get_data.IR import get_interest_rate
from src.data.get_data.MVRV import get_mvrv
from src.data.get_data.MVRVCrosses import get_mvrvc
from src.data.get_data.MayerMultiple import get_mm
from src.data.get_data.RUP import get_rup
from src.data.get_data.SOPR import get_sopr
from src.data.get_data.correlations import get_macro_correlations
from src.data.get_data.derivatives import get_binance_derivatives
from src.data.get_data.dollar_strength import get_dollar_strength
from src.data.get_data.inflation import get_inflation_data
from src.data.get_data.sentiment import get_fear_and_greed
from src.utils.project_paths import RAW_DATA_DIR


LOGGER = logging.getLogger(__name__)


def build_fetchers():
    return [
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
        ("fear_and_greed", get_fear_and_greed),
        ("macro_correlations", get_macro_correlations),
    ]


def download_all_data(output_path: Path | None = None, strict: bool = False) -> dict:
    LOGGER.info("Starting daily data download.")

    output_path = output_path or RAW_DATA_DIR / f"daily_data_{datetime.now():%Y-%m-%d}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "timestamp": f"{output_path.stem.replace('daily_data_', '')}T00:00:00",
        "metrics": {},
        "meta": {
            "failed_fetches": [],
        },
    }

    for key, fetcher in build_fetchers():
        try:
            LOGGER.info("Fetching %s", key)
            data["metrics"][key] = fetcher()
        except Exception as exc:
            LOGGER.warning("Fetcher '%s' failed: %s", key, exc)
            data["metrics"][key] = None
            data["meta"]["failed_fetches"].append({"metric": key, "error": str(exc)})

    data["meta"]["success_count"] = sum(value is not None for value in data["metrics"].values())
    data["meta"]["failed_count"] = len(data["meta"]["failed_fetches"])

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    LOGGER.info("Raw data saved to %s", output_path)

    if strict and data["meta"]["failed_fetches"]:
        failed_metrics = ", ".join(item["metric"] for item in data["meta"]["failed_fetches"])
        raise RuntimeError(f"Daily download completed with failed fetchers: {failed_metrics}")

    return {
        "data": data,
        "output_path": output_path,
        "failed_fetches": data["meta"]["failed_fetches"],
    }


if __name__ == "__main__":
    download_all_data()
