from __future__ import annotations

import argparse
import json
import logging
import logging.config
import os
import sys
from pathlib import Path

from src.utils.project_paths import (
    ACCOUNTING_DIR,
    LATEST_REPORT_PATH,
    PROCESSED_DATA_DIR,
    PROJECT_ROOT,
    RAW_DATA_DIR,
    REPORTS_DIR,
    SIGNALS_DIR,
    collect_project_status,
)


LOGGER = logging.getLogger("bitcoin_quant")
LOGGING_CONFIG_PATH = PROJECT_ROOT / "logging.conf"


def configure_logging() -> None:
    if logging.getLogger().handlers:
        return

    if LOGGING_CONFIG_PATH.exists() and LOGGING_CONFIG_PATH.read_text(encoding="utf-8").strip():
        logging.config.fileConfig(
            LOGGING_CONFIG_PATH,
            defaults={"sys": sys},
            disable_existing_loggers=False,
        )
    else:
        logging.basicConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bitcoin Quant project command line interface.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    download_parser = subparsers.add_parser("download", help="Fetch raw market data.")
    download_parser.add_argument("--date", help="Override output date (YYYY-MM-DD).")
    download_parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail the command if any data source cannot be fetched.",
    )

    process_parser = subparsers.add_parser("process", help="Build processed features from raw data.")
    process_parser.add_argument("--raw-file", help="Specific raw JSON file to process.")

    paper_parser = subparsers.add_parser("paper", help="Run the paper trading routine.")
    paper_parser.add_argument("--processed-file", help="Specific processed JSON file to use.")

    full_parser = subparsers.add_parser("full", help="Run download, processing and paper trading.")
    full_parser.add_argument("--date", help="Override output date (YYYY-MM-DD).")
    full_parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail the pipeline if any data source cannot be fetched.",
    )

    dashboard_parser = subparsers.add_parser("dashboard", help="Serve the local dashboard.")
    dashboard_parser.add_argument("--host", default="0.0.0.0")
    dashboard_parser.add_argument("--port", default=5000, type=int)
    dashboard_parser.add_argument("--debug", action="store_true")

    status_parser = subparsers.add_parser("status", help="Show project status and latest artifacts.")
    status_parser.add_argument("--json", action="store_true", dest="json_output")

    return parser


def command_download(args: argparse.Namespace) -> int:
    from src.pipeline import run_download

    result = run_download(target_date=args.date, strict=args.strict)
    LOGGER.info("Raw data written to %s", result["output_path"])
    return 0


def command_process(args: argparse.Namespace) -> int:
    from src.pipeline import run_processing

    result = run_processing(raw_file=args.raw_file)
    LOGGER.info("Processed data written to %s", result["output_path"])
    return 0


def command_paper(args: argparse.Namespace) -> int:
    from src.pipeline import run_paper

    result = run_paper(processed_file=args.processed_file)
    LOGGER.info("Paper trading report written to %s", result["report_path"])
    return 0


def command_full(args: argparse.Namespace) -> int:
    from src.pipeline import run_full_pipeline

    result = run_full_pipeline(target_date=args.date, strict=args.strict)
    LOGGER.info("Pipeline completed successfully.")
    LOGGER.info("Latest report: %s", result["paper"]["report_path"])
    return 0


def command_dashboard(args: argparse.Namespace) -> int:
    from webapp.app import app

    LOGGER.info("Dashboard available at http://%s:%s", args.host, args.port)
    app.run(debug=args.debug, host=args.host, port=args.port)
    return 0


def command_status(args: argparse.Namespace) -> int:
    status = collect_project_status()
    status.update(
        {
            "raw_data_dir": str(RAW_DATA_DIR.relative_to(PROJECT_ROOT)),
            "processed_data_dir": str(PROCESSED_DATA_DIR.relative_to(PROJECT_ROOT)),
            "signals_dir": str(SIGNALS_DIR.relative_to(PROJECT_ROOT)),
            "accounting_dir": str(ACCOUNTING_DIR.relative_to(PROJECT_ROOT)),
            "reports_dir": str(REPORTS_DIR.relative_to(PROJECT_ROOT)),
            "latest_report_path": str(LATEST_REPORT_PATH.relative_to(PROJECT_ROOT))
            if LATEST_REPORT_PATH.exists()
            else None,
            "fred_api_key_configured": bool(os.getenv("FRED_API_KEY")),
        }
    )

    if args.json_output:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        for key, value in status.items():
            print(f"{key}: {value}")
    return 0


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        "download": command_download,
        "process": command_process,
        "paper": command_paper,
        "full": command_full,
        "dashboard": command_dashboard,
        "status": command_status,
    }

    try:
        return handlers[args.command](args)
    except Exception as exc:
        LOGGER.exception("Command '%s' failed: %s", args.command, exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
