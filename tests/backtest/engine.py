import pandas as pd
from src.strategy.score import QuantScorer

class BacktestEngine:
    """
    Simulates the execution of the strategy over historical data.
    Tracks Portfolio Value, Cash, and BTC Holdings.
    """
    
    def __init__(self, initial_capital=10000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.btc = 0.0
        self.portfolio_history = []
        self.scorer = QuantScorer()
        
    def run(self, data_generator):
        print("Starting Backtest Simulation...")
        
        for day_data in data_generator:
            price = day_data["market_data"]["current_price"]
            date = day_data["timestamp"]
            
            # 1. Get Strategy Signal
            analysis = self.scorer.calculate_scores(day_data)
            lt_score = analysis["scores"]["long_term"]["value"]
            mt_score = analysis["scores"]["medium_term"]["value"]
            
            recommendation = self._decide_action(lt_score, mt_score)
            
            # 2. Execute Logic (Spot Only)
            self._execute_trade(recommendation, price, date)
            
            # 3. Track Performance
            total_value = self.cash + (self.btc * price)
            self.portfolio_history.append({
                "date": date,
                "price": price,
                "total_value": total_value,
                "cash": self.cash,
                "btc": self.btc,
                "action": recommendation,
                "lt_score": lt_score,
                "mt_score": mt_score
            })
            
        return pd.DataFrame(self.portfolio_history)

    def _decide_action(self, lt_score, mt_score):
        # 1. Strong Confluence (Both Bullish) -> Go All In
        if lt_score > 50 and mt_score > 30:
            return "STRONG_BUY"
            
        # 2. Strong Confluence (Both Bearish) -> Cash is King
        elif lt_score < -50 and mt_score < -30:
            return "SELL_EVERYTHING"
            
        # 3. Divergence (LT Bull, MT Bear) -> Buy the Dip
        elif lt_score > 30 and mt_score < -30:
            return "ACCUMULATE"
            
        # 4. Divergence (LT Bear, MT Bull) -> Sell the Rip
        elif lt_score < -30 and mt_score > 30:
            return "SELL_RALLY"
            
        # 5. Neutral / Weak Zones
        else:
            if mt_score > 50: return "BUY_SCALP"
            elif mt_score < -50: return "STAY_CASH"
            else: return "WAIT"
            
        return pd.DataFrame(self.portfolio_history)

    def _execute_trade(self, action, price, date):
        # Simple logic: Fixed % allocation changes for testing
        # In production, this would be more complex (Kelly Criterion, etc.)
        
        total_value = self.cash + (self.btc * price)
        current_btc_value = self.btc * price
        current_allocation = current_btc_value / total_value if total_value > 0 else 0
        
        target_allocation = current_allocation # Default: No change
        
        if action == "STRONG_BUY":
            target_allocation = 1.0 # 100% BTC
        elif action == "ACCUMULATE":
            target_allocation = min(current_allocation + 0.10, 1.0) # Add 10%
        elif action == "BUY_SCALP":
            target_allocation = min(current_allocation + 0.20, 0.50) # Max 50% for scalps
        elif action == "SELL_RALLY":
            target_allocation = max(current_allocation - 0.20, 0.0) # Reduce 20%
        elif action == "SELL_EVERYTHING" or action == "STAY_CASH":
            target_allocation = 0.0 # 0% BTC
            
        # Rebalance to Target
        diff = target_allocation - current_allocation
        
        if abs(diff) > 0.01: # 1% threshold to avoid dust
            amount_to_move = diff * total_value
            
            if amount_to_move > 0: # Buy
                cost = amount_to_move
                if self.cash >= cost:
                    self.cash -= cost
                    self.btc += cost / price
            else: # Sell
                sell_value = abs(amount_to_move)
                btc_to_sell = sell_value / price
                if self.btc >= btc_to_sell:
                    self.btc -= btc_to_sell
                    self.cash += sell_value

    def generate_report(self, df):
        initial = self.initial_capital
        final = df.iloc[-1]["total_value"]
        total_return = ((final - initial) / initial) * 100
        
        # Buy & Hold Comparison
        initial_price = df.iloc[0]["price"]
        final_price = df.iloc[-1]["price"]
        bnh_return = ((final_price - initial_price) / initial_price) * 100
        
        print("\n--- Backtest Results ---")
        print(f"Period: {df.iloc[0]['date'][:10]} to {df.iloc[-1]['date'][:10]}")
        print(f"Initial Capital: ${initial:,.2f}")
        print(f"Final Capital:   ${final:,.2f}")
        print(f"Total Return:    {total_return:.2f}%")
        print(f"Buy & Hold:      {bnh_return:.2f}%")
        print(f"Alpha:           {total_return - bnh_return:.2f}%")
        print("------------------------")
