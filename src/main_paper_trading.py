from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

from src.execution.accounting import AccountingSystem
from src.execution.production_gate import build_live_components
from src.utils.project_paths import (
    LATEST_REPORT_PATH,
    REPORTS_DIR,
    SIGNALS_DIR,
    latest_processed_data_file,
)


LOGGER = logging.getLogger(__name__)


def upsert_score_history(
    date_str: str,
    long_term_score: float,
    medium_term_score: float,
    csv_path: Path | None = None,
) -> Path:
    csv_path = csv_path or SIGNALS_DIR / "score_history.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    if csv_path.exists():
        with csv_path.open("r", newline="", encoding="utf-8") as existing_file:
            rows = list(csv.DictReader(existing_file))

    # De-duplicate by date and keep the newest payload for each day.
    row_by_date = {
        row["Date"]: {
            "Date": row["Date"],
            "Long_Term_Score": row["Long_Term_Score"],
            "Medium_Term_Score": row["Medium_Term_Score"],
        }
        for row in rows
        if row.get("Date")
    }
    row_by_date[date_str] = {
        "Date": date_str,
        "Long_Term_Score": f"{long_term_score:.2f}",
        "Medium_Term_Score": f"{medium_term_score:.2f}",
    }

    rows = sorted(row_by_date.values(), key=lambda row: row["Date"])

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["Date", "Long_Term_Score", "Medium_Term_Score"],
        )
        writer.writeheader()
        writer.writerows(rows)

    return csv_path


def run_daily_paper_trading(processed_file_path: str | Path | None = None) -> dict:
    LOGGER.info("Starting daily paper trading routine.")

    processed_file_path = Path(processed_file_path) if processed_file_path else latest_processed_data_file()
    if processed_file_path is None:
        raise FileNotFoundError("No processed data found. Run 'python main.py process' first.")

    LOGGER.info("Loading processed data from %s", processed_file_path)
    
    with processed_file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        
    current_price = data["market_data"]["current_price"]
    date_str = data["timestamp"][:10]

    # 4. Resolve live model from objective OOS gate output.
    live_setup = build_live_components(min_trade_usd=20.0)
    scorer = live_setup["scorer"]
    pm = live_setup["manager"]
    LOGGER.info(
        "Live model resolved: %s (source=%s)",
        live_setup["model"],
        live_setup["source"],
    )

    analysis = scorer.calculate_scores(data)
    scores = analysis["scores"]
    
    lt_score = scores["long_term"]["value"]
    mt_score = scores["medium_term"]["value"]
    
    # --- LOG SCORES TO CSV ---
    csv_path = upsert_score_history(date_str, lt_score, mt_score)
    LOGGER.info("Scores logged to %s", csv_path)
    # -------------------------
    
    LOGGER.info(
        "Scores -> LT: %.2f | MT: %.2f",
        scores["long_term"]["value"],
        scores["medium_term"]["value"],
    )
    

    accounting = AccountingSystem()
    if accounting.state is None:
        accounting.initialize(current_price)
        
    state = accounting.get_state()
    
    # Retrieve last_trade_date and current_date for order calculation
    last_trade_date = state.get("last_trade_date")
    current_date = date_str

    order = pm.calculate_order(
        scores=scores,
        current_cash=state["cash"],
        current_btc_value=state["btc_amount"] * current_price,
        current_debt=state["debt"],
        last_trade_date=last_trade_date,
        current_date=current_date
    )

    if order:
        LOGGER.info("Executing order: %s $%.2f (%s)", order.side, order.amount_usd, order.reason)
        accounting.execute_order(order.side, order.amount_usd, current_price, executed_at=date_str)
    else:
        LOGGER.info("No trade needed. Allocation already within thresholds.")
        
    snapshot = accounting.update_daily(current_price, date_str)
    
    report = accounting.generate_report()
    LOGGER.info("Paper trading equity: $%.2f", snapshot["equity"])
    
    # Save to archive (reports/daily/report_YYYY-MM-DD.md)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"report_{date_str}.md"
    
    with report_path.open("w", encoding="utf-8") as f:
        f.write(report)
        
    LOGGER.info("Report archived to %s", report_path)
    
    # Save to latest_report.md for easy viewing
    with LATEST_REPORT_PATH.open("w", encoding="utf-8") as f:
        f.write(report)

    accounting.update_readme()
    return {
        "processed_file": processed_file_path,
        "report_path": report_path,
        "latest_report_path": LATEST_REPORT_PATH,
        "executed_order": order.side if order else None,
        "equity": snapshot["equity"],
        "active_model": live_setup["model"],
        "gate_source": live_setup["source"],
    }

if __name__ == "__main__":
    run_daily_paper_trading()
