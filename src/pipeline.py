from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from src.utils.project_paths import (
    LATEST_REPORT_PATH,
    collect_project_status,
    dated_json_path,
    latest_processed_data_file,
    latest_raw_data_file,
    normalize_date,
)


def run_download(target_date: date | datetime | str | None = None, strict: bool = False) -> dict:
    from src.data.download import download_all_data
    from src.utils.project_paths import RAW_DATA_DIR

    normalized = normalize_date(target_date)
    output_path = dated_json_path(RAW_DATA_DIR, "daily_data", normalized)
    return download_all_data(output_path=output_path, strict=strict)


def run_processing(raw_file: str | Path | None = None) -> dict:
    from src.strategy.process_data import process_daily_data

    target_file = Path(raw_file) if raw_file else latest_raw_data_file()
    if target_file is None:
        raise FileNotFoundError("No raw data file available to process.")
    return process_daily_data(target_file)


def run_paper(processed_file: str | Path | None = None) -> dict:
    from src.main_paper_trading import run_daily_paper_trading

    target_file = Path(processed_file) if processed_file else latest_processed_data_file()
    if target_file is None:
        raise FileNotFoundError("No processed data file available for paper trading.")
    return run_daily_paper_trading(target_file)


def run_full_pipeline(target_date: date | datetime | str | None = None, strict: bool = False) -> dict:
    download_result = run_download(target_date=target_date, strict=strict)
    process_result = run_processing(download_result["output_path"])
    paper_result = run_paper(process_result["output_path"])

    return {
        "download": download_result,
        "process": process_result,
        "paper": paper_result,
        "status": collect_project_status(),
        "latest_report": str(LATEST_REPORT_PATH) if LATEST_REPORT_PATH.exists() else None,
    }
