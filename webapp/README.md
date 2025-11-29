# Bitcoin Quant Dashboard

Professional web dashboard for visualizing Bitcoin quantitative trading strategy performance.

## Features

- 📊 **Interactive Charts**: Bitcoin price with score overlays, performance comparison, portfolio allocation
- 📈 **Performance Metrics**: Total return, Alpha, Sharpe ratio, Max drawdown
- 🎯 **Real-time Scores**: Long-term and medium-term market sentiment indicators
- 💼 **Portfolio Tracking**: Current holdings, cash balance, trade history
- 🎨 **Premium Design**: Dark mode with glassmorphism effects and smooth animations

## Quick Start

### 1. Install Dependencies

```bash
cd /home/lucas/Documentos/PROJETÃO
source venv/bin/activate
pip install flask flask-cors
```

### 2. Start the Server

```bash
cd webapp
python app.py
```

### 3. Open Dashboard

Navigate to http://localhost:5000 in your browser.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Main dashboard page |
| `GET /api/backtest-results` | Complete backtest data |
| `GET /api/current-scores` | Latest LT/MT scores |
| `GET /api/portfolio` | Current portfolio status |
| `GET /api/price-history` | Bitcoin price with scores |
| `GET /api/performance-metrics` | Performance metrics |
| `GET /api/latest-processed-data` | Latest market data |

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Charts**: Chart.js
- **Design**: Custom CSS with glassmorphism and animations

## Project Structure

```
webapp/
├── app.py                 # Flask API server
└── static/
    ├── index.html        # Dashboard HTML
    ├── css/
    │   └── styles.css   # Design system
    └── js/
        └── dashboard.js # Chart rendering
```

## Performance Highlights

- **Strategy Return**: +225.73%
- **Buy & Hold Return**: +195.51%
- **Alpha**: +30.22%
- **Max Drawdown**: -51.36%
- **Sharpe Ratio**: 0.68
- **Backtest Period**: 2021-2025 (1,788 days)

## License

Part of the Bitcoin Quant Project.
