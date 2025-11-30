# Quantitative Evolution Roadmap: From Basic Bot to Institutional Algo

This document outlines the step-by-step evolution of the trading bot, moving from static heuristics to adaptive, statistical, and regime-aware logic.

## Phase 1: Statistical Normalization (The Foundation)
*Goal: Remove "magic numbers" and hardcoded thresholds.*
- [x] **Z-Score Implementation:** Replace absolute values (e.g., MVRV < 1.0) with standard deviations (Z-Score < -1.5).
- [ ] **Percentile Ranking:** Use historical percentiles (0-100%) for bounded metrics like RSI to ensure valid signals in all regimes.
- [ ] **Rolling Windows:** Implement dynamic lookback windows (e.g., 4-year Halving Cycle window) for all calculations.

## Phase 2: Risk Management (The Shield)
*Goal: Survive volatility and avoid ruin.*
- [ ] **Volatility Targeting (Vol Target):** Adjust position size inversely to volatility.
  - *Formula:* `Target Exposure = (Target Vol / Current Vol) * Equity`
- [ ] **Kelly Criterion (Fractional):** Mathematically optimal bet sizing based on win rate and payoff ratio.
- [ ] **Drawdown Control:** Hard stop-loss on equity curve (e.g., if Equity drops 10%, reduce all positions by 50%).

## Phase 3: Regime Detection (The Brain)
*Goal: Know WHEN to apply which strategy.*
- [ ] **Hurst Exponent:** Detect if market is Trending (Hurst > 0.5) or Mean Reverting (Hurst < 0.5).
- [ ] **ADX Filter:** Block Mean Reversion trades when Trend Strength (ADX) is > 50 (don't catch falling knives).
- [ ] **Correlation Matrix:** Monitor correlation between BTC and S&P500/DXY. If correlation breaks, potential regime shift.

## Phase 4: Microstructure & Order Flow (The Eyes)
*Goal: Precision entry/exit using real-time liquidity data.*
- [ ] **Funding Rate Arbitrage:** Use extreme negative funding as a strong contrarian buy signal (Short Squeeze).
- [ ] **Open Interest Divergence:** Price up + OI down = Weak Trend (Exit). Price down + OI up = Strong Bear (Short).
- [ ] **Liquidation Cascades:** Detect large liquidation clusters to enter after the "flush".

## Phase 5: Validation & Robustness (The Judge)
*Goal: Prove it works before risking money.*
- [ ] **Walk-Forward Analysis (WFA):** Optimization on past data -> Validation on "future" data. Sliding window approach.
- [ ] **Monte Carlo Simulation:** Shuffle trade order 10,000 times to estimate probability of max drawdown.
- [ ] **Parameter Stability Surface:** Visualize 3D surface of parameters. We want a "plateau" of good results, not a single "peak" (overfitting).

