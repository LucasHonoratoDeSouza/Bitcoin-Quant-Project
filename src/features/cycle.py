from datetime import datetime, timedelta
import pandas as pd

class BitcoinCycle:
    """
    Analyzes the Bitcoin 4-Year Cycle based on Halving events.
    """
    
    # Historic and projected Halving dates
    HALVINGS = [
        datetime(2012, 11, 28),
        datetime(2016, 7, 9),
        datetime(2020, 5, 11),
        datetime(2024, 4, 20), # Approx
        datetime(2028, 4, 1),  # Projected
    ]

    def __init__(self):
        pass

    def get_nearest_halving(self, date: datetime):
        """
        Returns the nearest halving date (past or future) and the type ('past' or 'future').
        """
        # Sort halvings
        sorted_halvings = sorted(self.HALVINGS)
        
        # Find the last halving before date and first halving after date
        past_halving = None
        next_halving = None
        
        for h in sorted_halvings:
            if h <= date:
                past_halving = h
            else:
                next_halving = h
                break
        
        return past_halving, next_halving

    def get_phase(self, date_str: str) -> dict:
        """
        Determines the market cycle phase based on the date.
        
        Phases:
        1. Accumulation: ~12-18 months before Halving
        2. Pre-Halving Rally: ~6-9 months before Halving
        3. Post-Halving Expansion: ~0-18 months after Halving
        4. Bear Market: ~18-30 months after Halving (or >18 months until next)
        """
        date = pd.to_datetime(date_str).to_pydatetime()
        past_h, next_h = self.get_nearest_halving(date)
        
        phase = "Unknown"
        days_since = (date - past_h).days if past_h else 9999
        days_until = (next_h - date).days if next_h else 9999
        
        # Logic based on docs
        # 1. Expansion: 0 to 18 months (approx 540 days) after Halving
        if past_h and days_since <= 540:
            phase = "Post-Halving Expansion"
            
        # 2. Accumulation: 12-18 months before Halving (365 to 540 days before)
        elif next_h and 365 < days_until <= 540:
            phase = "Accumulation"
            
        # 3. Pre-Halving Rally: < 9 months before Halving (approx 270 days)
        # Note: There is a gap between Accumulation and Pre-Halving in the simple logic above.
        # Let's refine:
        # Accumulation: > 270 days until halving (and not in Bear of previous)
        # Pre-Halving: <= 270 days until halving
        
        elif next_h and days_until <= 270:
            phase = "Pre-Halving Rally"
            
        elif next_h and 270 < days_until <= 540:
             phase = "Accumulation"

        # 4. Bear Market / Distribution: Everything else (usually > 540 days since last halving)
        else:
            phase = "Bear Market / Distribution"

        return {
            "date": date_str,
            "phase": phase,
            "days_since_halving": days_since,
            "days_until_halving": days_until,
            "current_cycle_halving": past_h.strftime("%Y-%m-%d") if past_h else None
        }

if __name__ == "__main__":
    cycle = BitcoinCycle()
    print(cycle.get_phase("2023-11-22")) # Should be Accumulation/Pre-Halving for 2024
    print(cycle.get_phase("2024-05-22")) # Post-Halving
    print(cycle.get_phase("2025-11-22")) # Post-Halving
