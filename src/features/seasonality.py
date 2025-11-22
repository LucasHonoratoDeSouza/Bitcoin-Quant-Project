from datetime import datetime

class BitcoinSeasonality:
    """
    Provides historical seasonality data for Bitcoin.
    Based on average monthly returns (Approx. 2013-2023).
    """
    
    # Average Monthly Returns % (Simplified for heuristic)
    MONTHLY_AVG = {
        1: 1.5,   # Jan: Mixed
        2: 12.0,  # Feb: Strong
        3: -5.0,  # Mar: Bearish (Tax season)
        4: 15.0,  # Apr: Strong
        5: 5.0,   # May: Moderate
        6: 2.0,   # Jun: Mixed
        7: 8.0,   # Jul: Good
        8: -2.0,  # Aug: Weak
        9: -6.0,  # Sep: Rekt (Historically worst month)
        10: 20.0, # Oct: "Uptober" (Very Strong)
        11: 45.0, # Nov: Bull Run Peak month often
        12: 5.0   # Dec: Moderate
    }

    def get_seasonality(self, date_str: str):
        """
        Returns the seasonality stats for the month of the given date.
        """
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        month = dt.month
        avg_return = self.MONTHLY_AVG.get(month, 0.0)
        
        status = "NEUTRAL"
        if avg_return > 10.0:
            status = "VERY BULLISH"
        elif avg_return > 3.0:
            status = "BULLISH"
        elif avg_return < -3.0:
            status = "BEARISH"
            
        return {
            "month": month,
            "avg_return_pct": avg_return,
            "status": status
        }
