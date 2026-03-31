from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from src.utils.project_paths import ACCOUNTING_DIR, README_PATH


LOGGER = logging.getLogger(__name__)

LIVE_STATS_START = "<!-- live-stats:start -->"
LIVE_STATS_END = "<!-- live-stats:end -->"

class AccountingSystem:
    
    def __init__(self, state_file=ACCOUNTING_DIR / "portfolio_state.json"):
        self.state_file = Path(state_file)
        self.state = self._load_state()

    def _load_state(self):
        if self.state_file.exists():
            with self.state_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return None 

    def initialize(self, current_price):
        LOGGER.info("Initializing new portfolio state.")
        initial_cash = 1000.0
        initial_btc_value = 1000.0
        initial_btc_amount = initial_btc_value / current_price
        
        self.state = {
            "cash": initial_cash,
            "btc_amount": initial_btc_amount,
            "debt": 0.0,
            "initial_capital": initial_cash + initial_btc_value,
            "last_trade_date": None,
            "history": []
        }
        self._save_state()

    def update_daily(self, current_price, date_str):
        if self.state is None:
            self.initialize(current_price)
        daily_interest_rate = 0.01 / 30
        interest_cost = 0.0
        
        if self.state["debt"] > 0:
            interest_cost = self.state["debt"] * daily_interest_rate
            self.state["debt"] += interest_cost 

        btc_value = self.state["btc_amount"] * current_price
        total_assets = self.state["cash"] + btc_value
        total_equity = total_assets - self.state["debt"]
        
        snapshot = {
            "date": date_str,
            "price": current_price,
            "cash": round(self.state["cash"], 2),
            "btc_amount": self.state["btc_amount"],
            "btc_value": round(btc_value, 2),
            "debt": round(self.state["debt"], 2),
            "equity": round(total_equity, 2),
            "interest_paid": round(interest_cost, 2)
        }
        
        if self.state["history"] and self.state["history"][-1]["date"] == date_str:
            self.state["history"][-1] = snapshot
        else:
            self.state["history"].append(snapshot)
        self._save_state()
        return snapshot

    def execute_order(self, side, amount_usd, price, executed_at=None):
        """
        Updates Cash/BTC/Debt based on an executed order.
        """
        if side == "BUY":
            cost = amount_usd
            btc_bought = cost / price

            if cost > self.state["cash"]:
                borrow_amount = cost - self.state["cash"]
                self.state["debt"] += borrow_amount
                self.state["cash"] = 0.0 
            else:
                self.state["cash"] -= cost
                
            self.state["btc_amount"] += btc_bought
            
        elif side == "SELL":
            revenue = amount_usd
            btc_sold = revenue / price
            
            self.state["btc_amount"] = max(self.state["btc_amount"] - btc_sold, 0.0)
            self.state["cash"] += revenue

            if self.state["debt"] > 0 and self.state["cash"] > 0:
                repay_amount = min(self.state["debt"], self.state["cash"])
                self.state["debt"] -= repay_amount
                self.state["cash"] -= repay_amount

        if executed_at:
            date_str = executed_at if len(executed_at) > 10 else f"{executed_at} 00:00:00"
        else:
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.state["last_trade_date"] = date_str
        self._log_order_csv(side, amount_usd, price, date_str)
        self._save_state()

    def _log_order_csv(self, side, amount_usd, price, date_str):
        csv_file = ACCOUNTING_DIR / "order_book.csv"
        csv_file.parent.mkdir(parents=True, exist_ok=True)
        file_exists = csv_file.exists()
        
        btc_amount = amount_usd / price
        
        with csv_file.open("a", encoding="utf-8") as f:
            if not file_exists:
                f.write("Date,Side,Amount_USD,Price,BTC_Amount\n")
            
            f.write(f"{date_str},{side},{amount_usd:.2f},{price:.2f},{btc_amount:.8f}\n")

    def generate_report(self):
        if not self.state or not self.state["history"]:
            return "No history available."
            
        latest = self.state["history"][-1]
        initial = self.state["initial_capital"]
        current = latest["equity"]
        
        roi = ((current - initial) / initial) * 100

        first_price = self.state["history"][0]["price"]
        last_price = latest["price"]
        bnh_roi = ((last_price - first_price) / first_price) * 100
        
        cash_pct = (latest['cash'] / current) * 100
        btc_pct = (latest['btc_value'] / current) * 100
        
        debt_pct = (latest['debt'] / current) * 100 if current > 0 else 0.0
        
        report = f"""# 📊 Paper Trading Report: {latest['date']}

## 💰 Performance
| Metric | Value |
| :--- | :--- |
| **Total Equity** | **${current:,.2f}** |
| **ROI (Total)** | `{roi:+.2f}%` |
| **Alpha (vs B&H)** | `{roi - bnh_roi:+.2f}%` |

## 💼 Portfolio Composition
| Asset | Value | Allocation | Details |
| :--- | :--- | :--- | :--- |
| 💵 **Cash** | ${latest['cash']:,.2f} | **{cash_pct:.1f}%** | - |
| 🟠 **Bitcoin** | ${latest['btc_value']:,.2f} | **{btc_pct:.1f}%** | `{latest['btc_amount']:.6f} BTC` |
| 🔴 **Debt** | ${latest['debt']:,.2f} | {debt_pct:.1f}% | Interest: `${latest['interest_paid']:.2f}` |

---
*Generated by Bitcoin Quant Bot*
"""
        return report

    def _calculate_win_rate(self):
        csv_file = ACCOUNTING_DIR / "order_book.csv"
        if not csv_file.exists():
            return 0.0, 0
            
        wins = 0
        losses = 0
        total_trades = 0
        
        inventory = [] 
        
        try:
            with csv_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()[1:] 
                
            for line in lines:
                parts = line.strip().split(",")
                if len(parts) < 5: continue
                
                side = parts[1]
                price = float(parts[3])
                amount_btc = float(parts[4])
                
                if side == "BUY":
                    inventory.append({"price": price, "amount": amount_btc})
                elif side == "SELL":
                    sold_amount = amount_btc
                    cost_basis = 0.0
                    matched_amount = 0.0
                    
                    while sold_amount > 0 and inventory:
                        batch = inventory[0]
                        take = min(batch["amount"], sold_amount)
                        
                        cost_basis += take * batch["price"]
                        matched_amount += take
                        sold_amount -= take
                        batch["amount"] -= take
                        
                        if batch["amount"] <= 1e-9: # Floating point tolerance
                            inventory.pop(0)
                            
                    if matched_amount > 0:
                        revenue = matched_amount * price
                        profit = revenue - cost_basis
                        
                        if profit > 0: wins += 1
                        else: losses += 1
                        total_trades += 1
                        
            if total_trades == 0: return 0.0, 0
            return (wins / total_trades) * 100, total_trades
            
        except Exception as e:
            LOGGER.warning("Error calculating win rate: %s", e)
            return 0.0, 0

    def _calculate_monthly_return(self):
        if not self.state or not self.state["history"]:
            return None
            
        first_entry = self.state["history"][0]
        last_entry = self.state["history"][-1]
        
        start_date = datetime.strptime(first_entry["date"], "%Y-%m-%d")
        end_date = datetime.strptime(last_entry["date"], "%Y-%m-%d")
        
        days_passed = (end_date - start_date).days
        
        if days_passed < 1:
            return None
            
        initial_equity = self.state["initial_capital"]
        current_equity = last_entry["equity"]
        
        total_return = (current_equity - initial_equity) / initial_equity

        try:
            monthly_return = ((1 + total_return) ** (30 / days_passed)) - 1
            return monthly_return * 100
        except:
            return 0.0

    def update_readme(self):
        """
        Updates the 'Live Paper Trading' section in README.md with the latest stats.
        """
        if not README_PATH.exists():
            LOGGER.info("README.md not found. Skipping update.")
            return

        if not self.state or not self.state["history"]:
            return

        latest = self.state["history"][-1]
        initial = self.state["initial_capital"]
        current = latest["equity"]
        profit = current - initial
        roi = (profit / initial) * 100
        
        # Calculate Real Win Rate
        win_rate, trade_count = self._calculate_win_rate()
        
        status_icon = "🟢" if profit >= 0 else "🔴"
        status_text = "Profitable" if profit >= 0 else "Drawdown"
        
        # Calculate Monthly Return
        monthly_return = self._calculate_monthly_return()
        monthly_str = f"{monthly_return:+.2f}%" if monthly_return is not None else "TBD"
        monthly_desc = "Projected (30-day)" if monthly_return is not None else "*Collecting data...*"
        
        live_stats_block = f"""{LIVE_STATS_START}
## Live Paper Trading
*Forward testing since Nov 23, 2025.*

| Metric | Value | Description |
| :--- | :--- | :--- |
| **Initial Capital** | `$2,000.00` | Starting Equity (Cash + BTC) |
| **Current Equity** | `${current:,.2f}` | Updated from the latest paper trading snapshot |
| **Net Profit** | `${profit:,.2f}` | **{roi:+.2f}%** |
| **Avg. Monthly Return** | `{monthly_str}` | {monthly_desc} |
| **Win Rate** | `{win_rate:.1f}%` | {trade_count} Trades Executed |

> **Status**: {status_icon} **Active** & **{status_text}** (Capital Preserved).
{LIVE_STATS_END}"""

        content = README_PATH.read_text(encoding="utf-8")
        if LIVE_STATS_START not in content or LIVE_STATS_END not in content:
            LOGGER.info("README.md live stats markers not found. Skipping update.")
            return

        start_index = content.index(LIVE_STATS_START)
        end_index = content.index(LIVE_STATS_END) + len(LIVE_STATS_END)
        updated_content = content[:start_index] + live_stats_block + content[end_index:]

        README_PATH.write_text(updated_content, encoding="utf-8")
        LOGGER.info("README.md updated with latest metrics.")

    def _save_state(self):
        # Ensure dir exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with self.state_file.open("w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=4)

    def get_state(self):
        return self.state
