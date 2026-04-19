## Data Flow

`Download -> Process -> Score -> Allocation -> Execution -> Accounting -> Reporting`

### 1. Download

- Module: `src/data/download.py`
- Pulls all configured sources and stores daily raw snapshot in `data/raw/`.
- Persists source failures in metadata for auditability.

### 2. Processing

- Module: `src/strategy/process_data.py`
- Converts raw payload into normalized metrics and boolean regime flags.
- Writes canonical processed snapshot in `data/processed/`.

### 3. Scoring

- Module: `src/strategy/score.py`
- Production mode uses backtest-approved legacy scorer.
- Research modes (advanced/blend) remain available behind explicit mode selection.

### 4. Allocation

- Module: `src/execution/portfolio_manager.py`
- Converts long/medium-term scores to target BTC allocation.
- Applies trade threshold + cooldown to reduce churn.

### 5. Execution + Accounting

- Modules: `src/main_paper_trading.py`, `src/execution/accounting.py`
- Executes simulated orders and updates cash/BTC/debt/equity.
- Maintains one canonical daily portfolio snapshot (date-level de-duplication).

### 6. Reporting

- Daily markdown report in `reports/daily/`.
- Latest report mirrored to `latest_report.md`.
- README live block updated automatically.

### 7. Research Gate

- Module: `tests/backtest/compare_models.py`
- Runs baseline vs candidate models with costs and debt carry.
- Writes comparison CSV + markdown summary under `docs/backtesting-reports/`.
- Only gate-approved candidates are promoted to production defaults.
