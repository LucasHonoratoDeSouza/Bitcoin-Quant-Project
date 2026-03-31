from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import json
import re
from pathlib import Path

from src.utils.project_paths import ACCOUNTING_DIR, PROCESSED_DATA_DIR, REPORTS_DIR, SIGNALS_DIR

app = Flask(__name__, static_folder='static')
CORS(app)

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Paper trading start date
PAPER_TRADING_START = "2025-11-23"

def parse_daily_reports():
    """Parse all daily reports to build historical data"""
    reports = []
    
    for report_file in sorted(REPORTS_DIR.glob('report_*.md')):
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract date from filename
            date_match = re.search(r'report_(\d{4}-\d{2}-\d{2})\.md', report_file.name)
            if not date_match:
                continue
            date = date_match.group(1)
            
            # Extract metrics using regex
            equity_match = re.search(r'\*\*Total Equity\*\*.*?\$([0-9,]+\.\d{2})', content)
            roi_match = re.search(r'\*\*ROI \(Total\)\*\*.*?([+-]?\d+\.\d{2})%', content)
            alpha_match = re.search(r'\*\*Alpha.*?\*\*.*?([+-]?\d+\.\d{2})%', content)
            cash_match = re.search(r'💵 \*\*Cash\*\*.*?\$([0-9,]+\.\d{2})', content)
            btc_value_match = re.search(r'🟠 \*\*Bitcoin\*\*.*?\$([0-9,]+\.\d{2})', content)
            btc_amount_match = re.search(r'`([0-9.]+) BTC`', content)
            debt_match = re.search(r'🔴 \*\*Debt\*\*.*?\$([0-9,]+\.\d{2})', content)
            
            report = {
                'date': date,
                'equity': float(equity_match.group(1).replace(',', '')) if equity_match else 0,
                'roi': float(roi_match.group(1)) if roi_match else 0,
                'alpha': float(alpha_match.group(1)) if alpha_match else 0,
                'cash': float(cash_match.group(1).replace(',', '')) if cash_match else 0,
                'btc_value': float(btc_value_match.group(1).replace(',', '')) if btc_value_match else 0,
                'btc_amount': float(btc_amount_match.group(1)) if btc_amount_match else 0,
                'debt': float(debt_match.group(1).replace(',', '')) if debt_match else 0
            }
            
            reports.append(report)
        except Exception as e:
            print(f"Error parsing {report_file}: {e}")
            continue
    
    return reports


def enrich_reports(reports):
    scores_path = SIGNALS_DIR / 'score_history.csv'

    if scores_path.exists():
        scores_df = pd.read_csv(scores_path).dropna()
        if not scores_df.empty:
            scores_df['Date'] = pd.to_datetime(scores_df['Date']).dt.strftime('%Y-%m-%d')
            scores_df = scores_df.drop_duplicates(subset=['Date'], keep='last')
            score_lookup = scores_df.set_index('Date').to_dict('index')
        else:
            score_lookup = {}
    else:
        score_lookup = {}

    for report in reports:
        score_row = score_lookup.get(report['date'], {})
        report['lt_score'] = float(score_row.get('Long_Term_Score', 0))
        report['mt_score'] = float(score_row.get('Medium_Term_Score', 0))
        report['btc_price'] = (
            report['btc_value'] / report['btc_amount']
            if report['btc_amount'] > 0
            else 0
        )

    return reports


def load_trade_history():
    order_book_path = ACCOUNTING_DIR / 'order_book.csv'
    if not order_book_path.exists():
        return []

    df = pd.read_csv(order_book_path).dropna(how='all')
    return df.to_dict('records')

@app.route('/')
def index():
    """Serve the main dashboard page"""
    return send_from_directory('static', 'index.html')

@app.route('/api/paper-trading-history')
def get_paper_trading_history():
    """Return complete paper trading history from daily reports"""
    try:
        reports = enrich_reports(parse_daily_reports())
        reports = [report for report in reports if report['date'] >= PAPER_TRADING_START]
        
        return jsonify({
            'success': True,
            'data': reports,
            'total_days': len(reports)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/current-scores')
def get_current_scores():
    """Return latest scores from score history"""
    try:
        scores_path = SIGNALS_DIR / 'score_history.csv'
        if not scores_path.exists():
            return jsonify({
                'success': False,
                'error': 'No score data available'
            }), 404

        df = pd.read_csv(scores_path)
        
        # Get the latest non-empty row
        df = df.dropna()
        if len(df) == 0:
            return jsonify({
                'success': False,
                'error': 'No score data available'
            }), 404
        
        latest = df.iloc[-1].to_dict()
        
        return jsonify({
            'success': True,
            'data': latest
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/portfolio')
def get_portfolio():
    """Return current portfolio status from latest report"""
    try:
        reports = enrich_reports(parse_daily_reports())
        if not reports:
            return jsonify({
                'success': False,
                'error': 'No reports found'
            }), 404
        
        latest = reports[-1]
        trades = load_trade_history()
        
        return jsonify({
            'success': True,
            'data': {
                'cash': latest['cash'],
                'btc': latest['btc_amount'],
                'btc_value': latest['btc_value'],
                'debt': latest['debt'],
                'equity': latest['equity'],
                'trades': trades,
                'total_trades': len(trades)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/price-history')
def get_price_history():
    """Return Bitcoin price history with scores from paper trading"""
    try:
        reports = enrich_reports(parse_daily_reports())
        
        price_data = [{
            'date': r['date'],
            'price': r['btc_price'],
            'lt_score': r.get('lt_score', 0),
            'mt_score': r.get('mt_score', 0)
        } for r in reports]
        
        return jsonify({
            'success': True,
            'data': price_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/performance-metrics')
def get_performance_metrics():
    """Calculate and return performance metrics from paper trading"""
    try:
        reports = parse_daily_reports()
        if not reports:
            return jsonify({
                'success': False,
                'error': 'No reports found'
            }), 404
        
        # Calculate btc_price for all reports
        for report in reports:
            if report['btc_amount'] > 0:
                report['btc_price'] = report['btc_value'] / report['btc_amount']
            else:
                report['btc_price'] = 0
        
        initial_capital = 2000.0
        latest = reports[-1]
        
        # Get initial and final prices
        initial_price = reports[0]['btc_price'] if reports[0]['btc_price'] > 0 else 86593.19
        final_price = latest['btc_price'] if latest['btc_price'] > 0 else 90617.91
        
        # Strategy returns (from equity)
        strategy_return = latest['roi']
        
        # Buy & Hold returns
        bnh_return = ((final_price - initial_price) / initial_price) * 100
        
        # Alpha
        alpha = latest['alpha']
        
        # S&P 500 Return
        sp500_return = 0.0
        try:
            import yfinance as yf
            # Fetch S&P 500 data from paper trading start
            sp500 = yf.Ticker("^GSPC")
            # Get data with some buffer before start date to ensure we get a start price
            hist = sp500.history(start=PAPER_TRADING_START)
            
            if not hist.empty:
                start_price = hist.iloc[0]['Close']
                current_price = hist.iloc[-1]['Close']
                sp500_return = ((current_price - start_price) / start_price) * 100
        except Exception as e:
            print(f"Error fetching S&P 500 data: {e}")
            sp500_return = 0.0
        
        # Max Drawdown (calculate from equity history)
        equities = [r['equity'] for r in reports]
        peak = equities[0]
        max_dd = 0
        for equity in equities:
            if equity > peak:
                peak = equity
            dd = ((equity - peak) / peak) * 100
            if dd < max_dd:
                max_dd = dd
        
        # Sharpe Ratio (simplified)
        if len(reports) > 1:
            returns = [(reports[i]['equity'] / reports[i-1]['equity'] - 1) for i in range(1, len(reports))]
            if returns and len(returns) > 0:
                mean_return = sum(returns) / len(returns)
                std_return = (sum((r - mean_return) ** 2 for r in returns) / len(returns)) ** 0.5
                sharpe_ratio = (mean_return / std_return) * (365 ** 0.5) if std_return > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        return jsonify({
            'success': True,
            'data': {
                'initial_capital': initial_capital,
                'final_value': latest['equity'],
                'strategy_return': round(strategy_return, 2),
                'bnh_return': round(bnh_return, 2),
                'sp500_return': round(sp500_return, 2),
                'alpha': round(alpha, 2),
                'max_drawdown': round(max_dd, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'total_days': len(reports)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/latest-processed-data')
def get_latest_processed_data():
    """Return latest processed market data"""
    try:
        # Find the latest processed file
        json_files = list(PROCESSED_DATA_DIR.glob('processed_data_*.json'))
        if not json_files:
            return jsonify({
                'success': False,
                'error': 'No processed data files found'
            }), 404
        
        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Bitcoin Quant Dashboard...")
    print("📊 Dashboard available at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
