import json
import os
from datetime import datetime
from pathlib import Path

class AccountingSystem:
    """
    Manages the persistent state of the Paper Trading Portfolio.
    Tracks Cash, BTC, Debt, and Historical Performance.
    """
    
    def __init__(self, state_file="data/accounting/portfolio_state.json"):
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                return json.load(f)
        else:
            return None # Will be initialized on first update if needed

    def initialize(self, current_price):
        """
        Initializes the portfolio with $1000 Cash and $1000 worth of BTC.
        """
        print("Initializing new Portfolio State...")
        initial_cash = 1000.0
        initial_btc_value = 1000.0
        initial_btc_amount = initial_btc_value / current_price
        
        self.state = {
            "cash": initial_cash,
            "btc_amount": initial_btc_amount,
            "debt": 0.0,
            "initial_capital": initial_cash + initial_btc_value,
            "history": []
        }
        self._save_state()

    def update_daily(self, current_price, date_str):
        """
        Updates the portfolio state for the day:
        - Accrues Interest on Debt.
        - Records Snapshot.
        """
        if self.state is None:
            self.initialize(current_price)
            
        # 1. Accrue Interest (1% per month = 0.01 / 30 per day)
        daily_interest_rate = 0.01 / 30
        interest_cost = 0.0
        
        if self.state["debt"] > 0:
            interest_cost = self.state["debt"] * daily_interest_rate
            self.state["debt"] += interest_cost # Add to debt pile
            
        # 2. Calculate Equity
        btc_value = self.state["btc_amount"] * current_price
        total_assets = self.state["cash"] + btc_value
        total_equity = total_assets - self.state["debt"]
        
        # 3. Record History
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
        
        self.state["history"].append(snapshot)
        self._save_state()
        return snapshot

    def execute_order(self, side, amount_usd, price):
        """
        Updates Cash/BTC/Debt based on an executed order.
        """
        if side == "BUY":
            cost = amount_usd
            btc_bought = cost / price
            
            # If cost > cash, we are borrowing
            if cost > self.state["cash"]:
                borrow_amount = cost - self.state["cash"]
                self.state["debt"] += borrow_amount
                self.state["cash"] = 0.0 # Used all cash
            else:
                self.state["cash"] -= cost
                
            self.state["btc_amount"] += btc_bought
            
        elif side == "SELL":
            revenue = amount_usd
            btc_sold = revenue / price
            
            self.state["btc_amount"] -= btc_sold
            self.state["cash"] += revenue
            
            # Repay Debt automatically if we have cash and debt
            if self.state["debt"] > 0 and self.state["cash"] > 0:
                repay_amount = min(self.state["debt"], self.state["cash"])
                self.state["debt"] -= repay_amount
                self.state["cash"] -= repay_amount

        self._save_state()

    def generate_report(self):
        if not self.state or not self.state["history"]:
            return "No history available."
            
        latest = self.state["history"][-1]
        initial = self.state["initial_capital"]
        current = latest["equity"]
        
        roi = ((current - initial) / initial) * 100
        
        # Buy & Hold Benchmark
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

    def _save_state(self):
        # Ensure dir exists
        Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=4)

    def get_state(self):
        return self.state
