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
    
    def __init__(self, min_trade_usd=10.0):
        self.min_trade_usd = min_trade_usd

    def calculate_order(self, scores: dict, current_cash: float, current_btc_value: float, current_debt: float = 0.0) -> Optional[Order]:
        """
        Determines the necessary order to reach the target allocation.
        Supports Margin/Leverage if conditions are met.
        """
        # Net Equity = Assets - Liabilities
        total_assets = current_cash + current_btc_value
        net_equity = total_assets - current_debt
        
        if net_equity <= 0: return None # Bankrupt or error
        
        current_allocation = current_btc_value / net_equity
        
        lt_score = scores["long_term"]["value"]
        mt_score = scores["medium_term"]["value"]
        
        target_allocation = self._get_target_allocation(lt_score, mt_score, current_allocation)
        
        # Calculate Target BTC Value based on Equity
        # e.g. Equity 10k, Target 2.0 -> Target BTC 20k
        target_btc_value = net_equity * target_allocation
        
        diff_usd = target_btc_value - current_btc_value
        
        print(f"DEBUG: Equity={net_equity}, TargetAlloc={target_allocation}, TargetBTC={target_btc_value}, CurrentBTC={current_btc_value}, Diff={diff_usd}")

        # Check Threshold
        if abs(diff_usd) < self.min_trade_usd:
            return None
            
        if diff_usd > 0:
            # Buy
            # Available buying power = Cash + Max Borrowable
            # But we just try to execute the difference.
            # If diff_usd > current_cash, we are borrowing.
            
            amount = diff_usd
            reason = self._get_reason(lt_score, mt_score)
            
            # Check if we have enough cash or need to borrow
            if amount > current_cash:
                # Borrowing logic is implicit here: we return a BUY order larger than cash.
                # The execution engine must handle the loan creation.
                # But wait, we should probably flag it.
                # For now, let's assume the order amount is the total BTC to buy.
                pass
                
            return Order(side="BUY", amount_usd=amount, reason=reason)
        else:
            # Sell
            amount = min(abs(diff_usd), current_btc_value) # Can't sell more than holdings
            if amount < self.min_trade_usd: return None
            return Order(side="SELL", amount_usd=amount, reason=self._get_reason(lt_score, mt_score))

    def _get_target_allocation(self, lt, mt, current):
        # 0. Super Bull (Leveraged) -> Scales from 1.0x to 2.0x
        # Trigger: LT > 75 AND MT > 50
        if lt > 75 and mt > 50:
            # Linear scale: 75 -> 1.0, 100 -> 2.0
            # Formula: 1.0 + ((LT - 75) / 25)
            leverage = 1.0 + ((lt - 75) / 25)
            return min(leverage, 2.0) # Cap at 2.0
            
        # 1. Strong Buy (High Conviction) -> 100%
        if lt > 40 and mt > 0:
            return 1.0
            
        # 2. Bear Market (Defensive) -> 0%
        if lt < -40:
            return 0.0
            
        # 3. Accumulate (Dip Buying) -> Dynamic DCA
        # Trigger: LT > 20 AND MT < -20
        if lt > 20 and mt < -20:
            # Buy more as dip deepens.
            # Example: MT -20 -> +10%. MT -60 -> +30%.
            # Formula: Current + (abs(MT) / 200)
            addition = abs(mt) / 200
            return min(current + addition, 1.0)
            
        # 4. Sell Rally (Trim) -> Dynamic Trimming
        # Trigger: LT < 20 AND MT > 20
        if lt < 20 and mt > 20:
            # Sell more as rally heats up.
            # Example: MT 20 -> -10%. MT 60 -> -30%.
            # Formula: Current - (MT / 200)
            reduction = mt / 200
            return max(current - reduction, 0.0)
            
        # 5. Buy Scalp (Tactical) -> Max 30%
        # Trigger: Any LT, MT > 50
        if mt > 50:
            return min(current + 0.20, 0.30)
            
        # 6. Neutral / No Signal
        return current

    def _get_reason(self, lt, mt):
        if lt > 75 and mt > 50: return f"Super Bull (Leverage {1.0 + ((lt - 75) / 25):.2f}x)"
        if lt > 40 and mt > 0: return "Strong Buy (High Conviction)"
        if lt < -40: return "Bear Market (Defensive)"
        if lt > 20 and mt < -20: return f"Accumulate (Dip Intensity {abs(mt)})"
        if lt < 20 and mt > 20: return f"Sell Rally (Heat {mt})"
        if mt > 50: return "Buy Scalp (Tactical)"
        return "Rebalance (Neutral)"
