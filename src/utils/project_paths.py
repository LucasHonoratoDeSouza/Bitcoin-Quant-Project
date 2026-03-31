from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SIGNALS_DIR = DATA_DIR / "signals"
ACCOUNTING_DIR = DATA_DIR / "accounting"
REPORTS_DIR = PROJECT_ROOT / "reports" / "daily"
LATEST_REPORT_PATH = PROJECT_ROOT / "latest_report.md"
README_PATH = PROJECT_ROOT / "README.md"


def ensure_directories(paths: Iterable[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def normalize_date(target_date: date | datetime | str | None = None) -> date:
    if target_date is None:
        return datetime.now().date()
    if isinstance(target_date, datetime):
        return target_date.date()
    if isinstance(target_date, date):
        return target_date
    return datetime.strptime(target_date, "%Y-%m-%d").date()


def dated_json_path(directory: Path, prefix: str, target_date: date | datetime | str) -> Path:
    normalized = normalize_date(target_date)
    return directory / f"{prefix}_{normalized.isoformat()}.json"


def dated_report_path(target_date: date | datetime | str) -> Path:
    normalized = normalize_date(target_date)
    return REPORTS_DIR / f"report_{normalized.isoformat()}.md"


def latest_matching_file(directory: Path, pattern: str) -> Path | None:
    candidates = sorted(directory.glob(pattern))
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: candidate.name)


def latest_raw_data_file() -> Path | None:
    return latest_matching_file(RAW_DATA_DIR, "daily_data_*.json")


def latest_processed_data_file() -> Path | None:
    return latest_matching_file(PROCESSED_DATA_DIR, "processed_data_*.json")


def latest_report_file() -> Path | None:
    return latest_matching_file(REPORTS_DIR, "report_*.md")


def relative_to_root(path: Path | None) -> str | None:
    if path is None:
        return None
    return str(path.relative_to(PROJECT_ROOT))


def collect_project_status() -> dict:
    raw_files = list(RAW_DATA_DIR.glob("daily_data_*.json"))
    processed_files = list(PROCESSED_DATA_DIR.glob("processed_data_*.json"))
    report_files = list(REPORTS_DIR.glob("report_*.md"))

    latest_raw = latest_raw_data_file()
    latest_processed = latest_processed_data_file()
    latest_report = latest_report_file()

    return {
        "project_root": str(PROJECT_ROOT),
        "latest_raw_data": relative_to_root(latest_raw),
        "latest_processed_data": relative_to_root(latest_processed),
        "latest_report": relative_to_root(latest_report),
        "raw_file_count": len(raw_files),
        "processed_file_count": len(processed_files),
        "report_count": len(report_files),
        "has_latest_report": LATEST_REPORT_PATH.exists(),
        "has_readme": README_PATH.exists(),
    }
