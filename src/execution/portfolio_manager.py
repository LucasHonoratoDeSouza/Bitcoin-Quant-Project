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
        # 0. Super Bull (Leveraged) -> 2.0x
        if lt > 80 and mt > 60:
            return 2.0
            
        # 1. Strong Buy (All In)
        if lt > 50 and mt > 30:
            return 1.0
            
        # 2. Sell Everything (Capital Preservation)
        if lt < -50 and mt < -30:
            return 0.0
            
        # 3. Stay Cash (Don't catch falling knives)
        if lt < -50 and mt < -50:
            return 0.0
            
        # 4. Accumulate (DCA into dip)
        if lt > 30 and mt < -30:
            return min(current + 0.10, 1.0)
            
        # 5. Sell Rally (Reduce exposure)
        if lt < -30 and mt > 30:
            return max(current - 0.20, 0.0)
            
        # 6. Buy Scalp (Tactical, limited exposure)
        if mt > 50:
            return min(current + 0.20, 0.30)
            
        # 7. Neutral / No Signal
        return current

    def _get_reason(self, lt, mt):
        if lt > 80 and mt > 60: return "Super Bull (Leveraged Buy)"
        if lt > 50 and mt > 30: return "Strong Buy (High Conviction)"
        if lt < -50 and mt < -30: return "Sell Everything (Bear Market)"
        if lt < -50 and mt < -50: return "Stay Cash (Extreme Risk)"
        if lt > 30 and mt < -30: return "Accumulate (Dip Buying)"
        if lt < -30 and mt > 30: return "Sell Rally (Exit Liquidity)"
        if mt > 50: return "Buy Scalp (Tactical)"
        return "Rebalance"
