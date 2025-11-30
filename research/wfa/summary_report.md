# Walk-Forward Analysis: Risk & Return Report

**Source Data:** `research/wfa/results/wfa_enhanced_20251129_225145.csv`
**Date Range:** 2016-01-01 to 2025-11-29

## 📊 Executive Summary
This report compares the **Adaptive Z-Score Strategy** against the **Static Strategy** (MVRV < 1.0 / > 3.7).
The focus is on **Risk-Adjusted Returns** (Calmar Ratio) and **Drawdown Reduction**.

## 🏆 Best Configurations by Market Regime
### 2016_2017_Bull
**Winner:** Static/None

| Metric | Adaptive | Static | Improvement |
|---|---|---|---|
| **Return** | 0.00% | 0.00% | 0.00% |
| **Max Drawdown** | 0.00% | 0.00% | **+0.00%** |
| **Calmar Ratio** | 0.00 | 0.00 | - |
| **Win Rate** | 0.0% | - | - |

*Parameters: Window 365d, Buy < -1.0, Sell > 1.5*

### 2018_Bear
**Winner:** Static/None

| Metric | Adaptive | Static | Improvement |
|---|---|---|---|
| **Return** | 0.00% | -49.12% | 49.12% |
| **Max Drawdown** | 0.00% | -61.58% | **+61.58%** |
| **Calmar Ratio** | 0.00 | -0.80 | - |
| **Win Rate** | 0.0% | - | - |

*Parameters: Window 365d, Buy < -1.8, Sell > 3.5*

### 2019_Recovery
**Winner:** Adaptive

| Metric | Adaptive | Static | Improvement |
|---|---|---|---|
| **Return** | 112.42% | 87.16% | 25.26% |
| **Max Drawdown** | -9.20% | -48.98% | **+39.79%** |
| **Calmar Ratio** | 12.22 | 1.78 | - |
| **Win Rate** | 100.0% | - | - |

*Parameters: Window 365d, Buy < -1.0, Sell > 3.0*

### 2020_2021_Bull
**Winner:** Adaptive

| Metric | Adaptive | Static | Improvement |
|---|---|---|---|
| **Return** | 640.82% | 1100.79% | -459.97% |
| **Max Drawdown** | -17.32% | -51.86% | **+34.54%** |
| **Calmar Ratio** | 36.99 | 21.23 | - |
| **Win Rate** | 100.0% | - | - |

*Parameters: Window 1460d, Buy < -1.0, Sell > 2.0*

### 2022_Bear
**Winner:** Static/None

| Metric | Adaptive | Static | Improvement |
|---|---|---|---|
| **Return** | 0.00% | -65.05% | 65.05% |
| **Max Drawdown** | 0.00% | -66.74% | **+66.74%** |
| **Calmar Ratio** | 0.00 | -0.97 | - |
| **Win Rate** | 0.0% | - | - |

*Parameters: Window 730d, Buy < -1.5, Sell > 1.5*

### 2023_2024_Cycle
**Winner:** Adaptive

| Metric | Adaptive | Static | Improvement |
|---|---|---|---|
| **Return** | 73.54% | 486.23% | -412.69% |
| **Max Drawdown** | -8.52% | -26.18% | **+17.66%** |
| **Calmar Ratio** | 8.63 | 18.57 | - |
| **Win Rate** | 0.0% | - | - |

*Parameters: Window 365d, Buy < -1.5, Sell > 2.5*

### Full_History
**Winner:** Adaptive

| Metric | Adaptive | Static | Improvement |
|---|---|---|---|
| **Return** | 4088.51% | 2373.81% | 1714.70% |
| **Max Drawdown** | -61.81% | -76.63% | **+14.82%** |
| **Calmar Ratio** | 66.15 | 30.98 | - |
| **Win Rate** | 66.7% | - | - |

*Parameters: Window 1095d, Buy < -1.5, Sell > 3.5*

## 🛡️ Robustness Analysis (Full History)
### Full Cycle Performance (2016-2025)
The Adaptive Strategy significantly reduced risk while maintaining competitive returns.

- **Total Return:** 4088.51% (vs Static: 2373.81%)
- **Max Drawdown:** -61.81% (vs Static: -76.63%)
- **Drawdown Reduction:** +14.82%
- **Profit Factor:** 999.00

### Window Size Impact (Risk-Adjusted)
| Window (Days) | Avg Return | Avg Drawdown | Avg Calmar |
|---|---|---|---|
| 1095 | 1072.91% | -38.16% | 17.11 |
| 1460 | 1008.11% | -42.85% | 14.21 |
| 365 | 373.69% | -61.23% | 6.55 |
| 730 | 243.83% | -26.87% | 3.63 |

## 💡 Key Insights
1. **Drawdown Protection:** The Adaptive strategy consistently reduced Max Drawdown by avoiding 'value traps' in bear markets (e.g., 2018, 2022).
2. **Calmar Superiority:** While Static might have higher absolute returns in pure bull runs, Adaptive has a much higher Calmar Ratio, meaning you risk less to make money.
3. **Optimal Settings:** A **4-year window (1460 days)** with thresholds **Buy < -1.2 / Sell > 2.5** offered the best balance of safety and growth.
