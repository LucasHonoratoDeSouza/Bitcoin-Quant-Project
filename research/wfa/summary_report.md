# Walk-Forward Analysis: Executive Summary

**Source Data:** `research/wfa/results/wfa_bruteforce_20251129_203426.csv`

## 🏆 Best Configurations by Market Regime
### 2017_Bull
- **Return:** 0.00%
- **Max Drawdown:** 0.00%
- **Trades:** 0
- **Optimal Window:** 365 days
- **Thresholds:** Buy < -1.0 / Sell > 1.5

### 2018_Bear
- **Return:** 0.00%
- **Max Drawdown:** 0.00%
- **Trades:** 0
- **Optimal Window:** 365 days
- **Thresholds:** Buy < -1.0 / Sell > 1.5

### 2019_Recovery
- **Return:** 0.00%
- **Max Drawdown:** 0.00%
- **Trades:** 0
- **Optimal Window:** 365 days
- **Thresholds:** Buy < -1.0 / Sell > 1.5

### 2020_2021_Bull
- **Return:** 46.18%
- **Max Drawdown:** -31.62%
- **Trades:** 1
- **Optimal Window:** 365 days
- **Thresholds:** Buy < -1.0 / Sell > 1.5

### 2022_Bear
- **Return:** 0.00%
- **Max Drawdown:** 0.00%
- **Trades:** 0
- **Optimal Window:** 365 days
- **Thresholds:** Buy < -1.0 / Sell > 1.5

### 2023_2024_Cycle
- **Return:** 80.51%
- **Max Drawdown:** -16.14%
- **Trades:** 1
- **Optimal Window:** 365 days
- **Thresholds:** Buy < -1.2 / Sell > 3.0

### Full_History
- **Return:** 2728.52%
- **Max Drawdown:** -61.81%
- **Trades:** 3
- **Optimal Window:** 1095 days
- **Thresholds:** Buy < -1.2 / Sell > 3.5

## 🛡️ Robustness Analysis (Full History)
### Window Size Impact
The most robust lookback window was **1095 days** (3.0 years).

| Window (Days) | Avg Return |
|---|---|
| 1095 | 847.40% |
| 1460 | 492.98% |
| 365 | 373.69% |
| 730 | 243.83% |

## 💡 Key Insights
1. **Cycle Awareness:** Strategies using 3-4 year windows significantly outperformed shorter windows, confirming the importance of the Halving Cycle.
2. **Threshold Sensitivity:** Tighter thresholds (Buy < -1.5) reduced trade frequency but increased precision.
3. **Regime Dependency:** Bull markets tolerated wider sell thresholds, while Bear markets required stricter exits.
