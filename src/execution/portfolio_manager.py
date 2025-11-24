from dataclasses import dataclass
from typing import Optional

@dataclass
class Order:
    side: str # "BUY" or "SELL"
    amount_usd: float
    reason: str

class PortfolioManager:
    """
    Translates QuantScorer outputs into concrete trading orders.
    Manages Risk and Capital Allocation.
    """
    
    def __init__(self, min_trade_usd=20.0, cooldown_days=3):
        self.min_trade_usd = min_trade_usd
        self.cooldown_days = cooldown_days

    def calculate_order(self, scores: dict, current_cash: float, current_btc_value: float, current_debt: float = 0.0, last_trade_date=None, current_date=None) -> Optional[Order]:
        """
        Determines the necessary order to reach the target allocation.
        Supports Margin/Leverage if conditions are met.
        Implements Smart Execution: Cooldowns & Dynamic Thresholds.
        """
        # Net Equity = Assets - Liabilities
        total_assets = current_cash + current_btc_value
        net_equity = total_assets - current_debt
        
        if net_equity <= 0: return None # Bankrupt or error
        
        current_allocation = current_btc_value / net_equity
        
        lt_score = scores["long_term"]["value"]
        mt_score = scores["medium_term"]["value"]
        
        target_allocation = self._get_target_allocation(lt_score, mt_score, current_allocation)
        reason = self._get_reason(lt_score, mt_score)
        
        # Calculate Target BTC Value based on Equity
        target_btc_value = net_equity * target_allocation
        
        diff_usd = target_btc_value - current_btc_value
        
        print(f"DEBUG: Equity={net_equity:.2f}, TargetAlloc={target_allocation:.2f}, TargetBTC={target_btc_value:.2f}, CurrentBTC={current_btc_value:.2f}, Diff={diff_usd:.2f}")

        # --- SMART EXECUTION LOGIC ---
        
        # 1. Dynamic Threshold (Hysteresis)
        # Minimum trade size is max(Fixed Min, 2% of Equity)
        # Example: $2000 Equity -> $40 Threshold.
        dynamic_threshold = max(self.min_trade_usd, net_equity * 0.02)
        
        if abs(diff_usd) < dynamic_threshold:
            print(f"💤 Trade skipped: Diff ${diff_usd:.2f} < Threshold ${dynamic_threshold:.2f}")
            return None

        # 2. Cooldown Mechanism
        # Urgent signals bypass cooldown: Super Bull, Strong Buy, Sell Everything
        is_urgent = "Super Bull" in reason or "Strong Buy" in reason or "Sell Everything" in reason or "Stay Cash" in reason
        
        if not is_urgent and last_trade_date and current_date:
            from datetime import datetime
            # Ensure dates are datetime objects
            if isinstance(last_trade_date, str):
                last_trade_date = datetime.strptime(last_trade_date.split(" ")[0], "%Y-%m-%d")
            if isinstance(current_date, str):
                current_date = datetime.strptime(current_date.split(" ")[0], "%Y-%m-%d")
                
            days_since = (current_date - last_trade_date).days
            
            if days_since < self.cooldown_days:
                print(f"⏳ Cooldown Active: {days_since} days since last trade. Waiting {self.cooldown_days} days.")
                return None

        # --- END SMART EXECUTION ---
            
        if diff_usd > 0:
            # Buy
            amount = diff_usd
            # Check if we have enough cash or need to borrow (handled by execution engine)
            return Order(side="BUY", amount_usd=amount, reason=reason)
        else:
            # Sell
            amount = min(abs(diff_usd), current_btc_value) # Can't sell more than holdings
            if amount < dynamic_threshold: return None # Double check
            return Order(side="SELL", amount_usd=amount, reason=reason)

    def _get_target_allocation(self, lt, mt, current):
        # 0. Super Bull (Leveraged) -> Scales from 1.0x to 2.0x
        # Trigger: LT > 75 AND MT > 50
        if lt > 75 and mt > 50:
            leverage = 1.0 + ((lt - 75) / 25)
            return min(leverage, 2.0)
            
        # 1. Strong Buy (High Conviction) -> 100%
        if lt > 40 and mt > 0:
            return 1.0
            
        # 2. Extreme Bear / Overheated (Exit All) -> 0%
        # Trigger: LT < -60 (Crash Risk)
        if lt < -60:
            return 0.0
            
        # 3. Bear Market (Defensive) -> 10% Floor (Moonbag)
        # Trigger: LT < -40 (but > -60)
        if lt < -40:
            return 0.10
            
        # 4. Accumulate (Dip Buying) -> Dynamic DCA
        # Trigger: LT > 20 AND MT < -20
        if lt > 20 and mt < -20:
            addition = abs(mt) / 200
            return min(current + addition, 1.0)
            
        # 5. Sell Rally (Trim) -> Dynamic Trimming with 10% Floor
        # Trigger: LT < 20 AND MT > 20
        if lt < 20 and mt > 20:
            reduction = mt / 200
            target = current - reduction
            return max(target, 0.10) # Floor at 10%
            
        # 6. Buy Scalp (Tactical) -> Max 30%
        # Trigger: Any LT, MT > 50
        if mt > 50:
            return min(current + 0.20, 0.30)
            
        # 7. Neutral / No Signal -> Baseline 30%
        # If we are below 30%, we buy up to 30%.
        # If we are above 30%, we hold (or trim? No, let's hold current if > 30).
        # Actually, user said "never stay at 0% in neutral".
        # Let's set a soft target of 0.30.
        # If current < 0.30, return 0.30.
        # If current >= 0.30, return current (Hold).
        return max(current, 0.30)

    def _get_reason(self, lt, mt):
        if lt > 75 and mt > 50: return f"Super Bull (Leverage {1.0 + ((lt - 75) / 25):.2f}x)"
        if lt > 40 and mt > 0: return "Strong Buy (High Conviction)"
        if lt < -60: return "Extreme Bear (Exit All)"
        if lt < -40: return "Bear Market (Moonbag 10%)"
        if lt > 20 and mt < -20: return f"Accumulate (Dip Intensity {abs(mt)})"
        if lt < 20 and mt > 20: return f"Sell Rally (Heat {mt})"
        if mt > 50: return "Buy Scalp (Tactical)"
        return "Neutral (Baseline 30%)"
