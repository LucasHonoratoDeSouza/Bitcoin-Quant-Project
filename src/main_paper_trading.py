import sys
import os
from pathlib import Path
import json
from datetime import datetime

project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.strategy.score import QuantScorer
from src.execution.portfolio_manager import PortfolioManager
from src.execution.accounting import AccountingSystem

def run_daily_paper_trading():
    print("🚀 Starting Daily Paper Trading Routine...")

    import glob
    list_of_files = glob.glob('data/processed/*.json') 
    if not list_of_files:
        print("❌ No processed data found. Run 'make run' first.")
        return

    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"📂 Loading data from: {latest_file}")
    
    with open(latest_file, 'r') as f:
        data = json.load(f)
        
    current_price = data["market_data"]["current_price"]
    date_str = data["timestamp"][:10]

    # 4. Calculate Scores
    scorer = QuantScorer()
    analysis = scorer.calculate_scores(data)
    scores = analysis["scores"]
    
    lt_score = scores["long_term"]["value"]
    mt_score = scores["medium_term"]["value"]
    
    # --- LOG SCORES TO CSV ---
    signals_dir = "data/signals"
    os.makedirs(signals_dir, exist_ok=True)
    csv_path = os.path.join(signals_dir, "score_history.csv")
    
    file_exists = os.path.isfile(csv_path)
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    with open(csv_path, "a") as f:
        if not file_exists:
            f.write("Date,Long_Term_Score,Medium_Term_Score\n")
        f.write(f"{current_date},{lt_score:.2f},{mt_score:.2f}\n")
    
    print(f"Scores logged to {csv_path}")
    # -------------------------
    
    print(f"Scores -> LT: {scores['long_term']['value']} | MT: {scores['medium_term']['value']}")
    

    accounting = AccountingSystem()
    if accounting.state is None:
        accounting.initialize(current_price)
        
    state = accounting.get_state()
    
    pm = PortfolioManager()
    
    # Retrieve last_trade_date and current_date for order calculation
    last_trade_date = state.get("last_trade_date")
    current_date = datetime.now().strftime("%Y-%m-%d")

    order = pm.calculate_order(
        scores=scores,
        current_cash=state["cash"],
        current_btc_value=state["btc_amount"] * current_price,
        current_debt=state["debt"],
        last_trade_date=last_trade_date,
        current_date=current_date
    )

    if order:
        print(f"⚡ Executing Order: {order.side} ${order.amount_usd:.2f} ({order.reason})")
        accounting.execute_order(order.side, order.amount_usd, current_price)
    else:
        print("💤 No trade needed (Allocation within thresholds).")
        
    snapshot = accounting.update_daily(current_price, date_str)
    
    report = accounting.generate_report()
    print(report)
    
    # Save to archive (reports/daily/report_YYYY-MM-DD.md)
    report_dir = Path("reports/daily")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"report_{date_str}.md"
    
    with open(report_path, "w") as f:
        f.write(report)
        
    print(f"📄 Report archived to: {report_path}")
    
    # Save to latest_report.md for easy viewing
    with open("latest_report.md", "w") as f:
        f.write(report)

    # 8. Update README.md
    accounting.update_readme()

if __name__ == "__main__":
    run_daily_paper_trading()
