import json
import os
import math
from datetime import datetime

class QuantScorer:
    """
    Advanced Quantitative Scoring Engine.
    Uses normalized z-scores, sigmoid activation functions, and dynamic regime weighting
    to generate precise Long-Term and Medium-Term signals.
    """
    
    def __init__(self):
        pass

    def _sigmoid(self, x, k=1.0):
        """
        Sigmoid activation function to squash values between -1 and 1.
        k controls the steepness.
        """
        return 2 / (1 + math.exp(-k * x)) - 1

    def _normalize(self, value, min_val, max_val, invert=False):
        """
        Normalizes a value to a -1.0 to 1.0 range based on historical bounds.
        """
        if value is None: return 0.0
        
        # Clamp value
        clamped = max(min_val, min(value, max_val))
        
        # Scale to 0 to 1
        normalized = (clamped - min_val) / (max_val - min_val)
        
        # Scale to -1 to 1
        score = (normalized * 2) - 1
        
        if invert:
            score = -score
            
        return score

    def _calc_long_term_quant(self, data: dict) -> dict:
        """
        Calculates Long Term Score using continuous functions.
        """
        metrics = data.get("metrics", {})
        cycle = data.get("market_cycle_phase", "Unknown")
        
        # 1. On-Chain Valuation (Continuous)
        # MVRV: Low (0.8) is Buy, High (3.5) is Sell.
        mvrv_score = self._normalize(metrics.get("mvrv"), 0.8, 3.5, invert=True)
        
        # Mayer Multiple: Low (0.6) is Buy, High (2.4) is Sell.
        mm_score = self._normalize(metrics.get("mayer_multiple"), 0.6, 2.4, invert=True)
        
        # RUP: Low (0.0) is Buy, High (5.0) is Sell. (Assuming RUP scale)
        rup_score = self._normalize(metrics.get("rup"), 0.0, 5.0, invert=True)
        
        onchain_score = (mvrv_score * 0.4) + (mm_score * 0.3) + (rup_score * 0.3)
        
        # 2. Macro Liquidity (Continuous)
        # M2 YoY: < 0% is Bad (-1), > 10% is Good (+1)
        m2_score = self._normalize(metrics.get("m2_yoy"), 0.0, 10.0)
        
        # Interest Rate: < 2% is Good (+1), > 5% is Bad (-1)
        ir_score = self._normalize(metrics.get("interest_rate"), 2.0, 5.0, invert=True)
        
        macro_score = (m2_score * 0.6) + (ir_score * 0.4)
        
        # 3. Cycle Bias (Discrete Step Function)
        cycle_score = 0.0
        if cycle in ["Accumulation", "Pre-Halving Rally"]: cycle_score = 0.8
        elif cycle == "Post-Halving Expansion": cycle_score = 0.4
        elif cycle == "Bear Market / Distribution": cycle_score = -0.8
        
        # Weighted Sum for Long Term
        # On-Chain is the truth (50%), Cycle is the map (30%), Macro is the weather (20%)
        final_lt = (onchain_score * 0.50) + (cycle_score * 0.30) + (macro_score * 0.20)
        
        return {
            "score": round(final_lt * 100, 2),
            "components": {
                "onchain": round(onchain_score, 2),
                "macro": round(macro_score, 2),
                "cycle": round(cycle_score, 2)
            }
        }

    def _calc_medium_term_quant(self, data: dict) -> dict:
        """
        Calculates Medium Term Score using continuous functions.
        """
        metrics = data.get("metrics", {})
        market = data.get("market_data", {})
        flags = data.get("flags", {})
        
        # 1. Sentiment (Fear & Greed)
        # 10 is Buy (+1), 90 is Sell (-1)
        fng = metrics.get("fear_and_greed")
        fng_score = self._normalize(fng, 10, 90, invert=True)
        
        # 2. Trend Extension (Price vs EMA)
        # -30% is Buy (+1), +100% is Sell (-1)
        ext_pct = market.get("price_vs_ema_pct")
        trend_ext_score = self._normalize(ext_pct, -30, 100, invert=True)
        
        # 3. Momentum (Weekly Change)
        # -15% is Oversold (+1), +20% is Overbought (-1) for mean reversion? 
        # Or trend following? Let's use Trend Following for MT.
        # Actually, MT is often mean reversion within trend.
        # Let's use the boolean flag for Trend Direction (+/- 1)
        trend_dir = 1.0 if flags.get("is_bull_trend") else -1.0
        
        # 4. Seasonality (Discrete)
        season_score = 1.0 if flags.get("is_positive_seasonality") else 0.0
        
        # Weighted Sum for Medium Term
        # Sentiment (40%), Trend Extension (30%), Trend Direction (20%), Seasonality (10%)
        final_mt = (fng_score * 0.40) + (trend_ext_score * 0.30) + (trend_dir * 0.20) + (season_score * 0.10)
        
        return {
            "score": round(final_mt * 100, 2),
            "components": {
                "sentiment": round(fng_score, 2),
                "extension": round(trend_ext_score, 2),
                "trend_dir": round(trend_dir, 2)
            }
        }

    def calculate_scores(self, data: dict) -> dict:
        lt = self._calc_long_term_quant(data)
        mt = self._calc_medium_term_quant(data)
        
        lt_score = lt["score"]
        mt_score = mt["score"]
        
        return {
            "scores": {
                "long_term": {
                    "value": lt_score,
                    "components": lt["components"],
                    "description": self._describe_score(lt_score)
                },
                "medium_term": {
                    "value": mt_score,
                    "components": mt["components"],
                    "description": self._describe_score(mt_score)
                }
            },
            "metadata": {
                "range": {
                    "min": -100,
                    "max": 100,
                    "neutral": 0
                },
                "interpretation": {
                    "-100": "Maximum Bearish / Overvalued / Extreme Risk",
                    "0": "Neutral / Fair Value",
                    "100": "Maximum Bullish / Undervalued / Extreme Opportunity"
                }
            }
        }

    def _describe_score(self, score):
        if score >= 80: return "Extreme Bullish (Max Opportunity)"
        if score >= 50: return "Bullish (Favorable)"
        if score >= 20: return "Mildly Bullish"
        if score > -20: return "Neutral"
        if score > -50: return "Mildly Bearish"
        if score > -80: return "Bearish (Unfavorable)"
        return "Extreme Bearish (Max Risk)"

if __name__ == "__main__":
    import glob
    list_of_files = glob.glob('data/processed/*.json') 
    if list_of_files:
        latest_file = max(list_of_files, key=os.path.getctime)
        print(f"Quant Analysis for: {latest_file}")
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
            
        scorer = QuantScorer()
        scores = scorer.calculate_scores(data)
        
        print(json.dumps(scores, indent=4))
