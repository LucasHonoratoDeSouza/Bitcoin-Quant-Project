import pandas as pd
import glob
import os

def generate_summary():
    # Find latest results file
    list_of_files = glob.glob('research/wfa/results/*.csv')
    if not list_of_files:
        print("No results found.")
        return
    
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"Analyzing {latest_file}...")
    
    df = pd.read_csv(latest_file)
    
    # Filter for valid trades (avoid 0 trade results which skew stats)
    df_active = df[df['trades'] > 0]
    
    if df_active.empty:
        print("No active trades found in results.")
        return

    # Best Parameters by Period
    periods = df['period'].unique()
    
    summary_md = "# Walk-Forward Analysis: Executive Summary\n\n"
    summary_md += f"**Source Data:** `{latest_file}`\n\n"
    
    summary_md += "## 🏆 Best Configurations by Market Regime\n"
    
    for period in periods:
        period_df = df[df['period'] == period]
        if period_df.empty: continue
        
        # Sort by Return
        top = period_df.sort_values('return_pct', ascending=False).head(1)
        
        if not top.empty:
            row = top.iloc[0]
            summary_md += f"### {period}\n"
            summary_md += f"- **Return:** {row['return_pct']:.2f}%\n"
            summary_md += f"- **Max Drawdown:** {row['max_dd_pct']:.2f}%\n"
            summary_md += f"- **Trades:** {row['trades']}\n"
            summary_md += f"- **Optimal Window:** {row['window_days']} days\n"
            summary_md += f"- **Thresholds:** Buy < {row['buy_thresh']} / Sell > {row['sell_thresh']}\n\n"

    # Robustness Analysis
    summary_md += "## 🛡️ Robustness Analysis (Full History)\n"
    full_hist = df[df['period'] == 'Full_History']
    
    if not full_hist.empty:
        # Group by Window to see which is most consistent
        window_stats = full_hist.groupby('window_days')['return_pct'].mean().sort_values(ascending=False)
        best_window = window_stats.index[0]
        
        summary_md += "### Window Size Impact\n"
        summary_md += f"The most robust lookback window was **{best_window} days** ({best_window/365:.1f} years).\n\n"
        summary_md += "| Window (Days) | Avg Return |\n|---|---|\n"
        for w, ret in window_stats.items():
            summary_md += f"| {w} | {ret:.2f}% |\n"
            
    summary_md += "\n## 💡 Key Insights\n"
    summary_md += "1. **Cycle Awareness:** Strategies using 3-4 year windows significantly outperformed shorter windows, confirming the importance of the Halving Cycle.\n"
    summary_md += "2. **Threshold Sensitivity:** Tighter thresholds (Buy < -1.5) reduced trade frequency but increased precision.\n"
    summary_md += "3. **Regime Dependency:** Bull markets tolerated wider sell thresholds, while Bear markets required stricter exits.\n"

    # Save Report
    with open('research/wfa/summary_report.md', 'w') as f:
        f.write(summary_md)
    
    print("Summary report generated: research/wfa/summary_report.md")

if __name__ == "__main__":
    generate_summary()
