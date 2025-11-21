quant-bitcoin-bot/
│
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt           # dependências
├── pyproject.toml / setup.py # se quiser transformar em pacote
│
├── docs/
│   ├── architecture/          # diagramas, fluxos do sistema, UML
│   ├── methodology/           # explicações sobre modelos, indicadores, features
│   ├── trading-rules/         # regras formais de compra/venda/alavancagem
│   ├── backtesting-reports/   # relatórios de testes históricos
│   ├── risk-management/       # documentos de gestão de risco e alavancagem
│   ├── glossary.md            # dicionário de termos
│   └── roadmap.md             # planejamento e milestones
│
├── data/
│   ├── raw/                   # dados crus da exchange (OHLC, funding, OI)
│   ├── interim/               # dados tratados parcialmente
│   ├── processed/             # dados completos e limpos para modelagem
│   ├── external/              # dados externos (sentimento, google trends, etc)
│   └── features/              # features já geradas e salvas (npz, parquet, csv)
│
├── notebooks/                 # Jupyter notebooks
│   ├── exploratory/           # EDA, estatísticas, análise de mercado
│   ├── feature-engineering/
│   ├── model-development/
│   ├── backtesting/
│   └── experiments/           # testes diversos
│
├── src/
│   ├── data/
│   │   ├── download.py        # download de OHLCV, funding, open interest etc
│   │   ├── loaders.py         # funções padronizadas de carregamento
│   │   └── preprocessing.py   # limpeza, normalização, merges
│   │
│   ├── features/
│   │   ├── technical.py       # indicadores técnicos (RSI, MACD, volatilidade, ciclo)
│   │   ├── sentiment.py       # sentimento on-chain / redes sociais
│   │   ├── derivatives.py     # funding, open interest, basis, risco
│   │   └── build_features.py  # pipeline de geração de features
│   │
│   ├── models/
│   │   ├── model_base.py      # classe base para modelos ML
│   │   ├── regression/        # modelos de previsão de preço/retorno
│   │   ├── classification/    # modelos de bull/bear, rali, tops/corretivas
│   │   ├── time_series/       # LSTM, transformers, seq2seq, prophet etc
│   │   └── train.py           # treinamento principal
│   │
│   ├── strategy/
│   │   ├── allocation.py      # lógica de divisão entre caixa/bitcoin/dívida
│   │   ├── position_sizing.py # sizing das posições
│   │   ├── risk.py            # alavancagem, drawdown, stop, exposição máxima
│   │   ├── signals.py         # geração dos sinais a partir dos modelos/features
│   │   └── execution.py       # camada de execução (simulada ou real)
│   │
│   ├── backtesting/
│   │   ├── engine.py          # mecanismo de backtesting
│   │   ├── metrics.py         # métricas: sharpe, sortino, maxDD, calmar
│   │   ├── walk_forward.py    # walk-forward analysis
│   │   └── plots.py           # gráficos do backtest
│   │
│   ├── live/
│   │   ├── exchange_api.py    # integração com exchange (Binance, Bybit etc)
│   │   ├── live_trading.py    # loop de trading em produção
│   │   ├── portfolio.py       # estado atual de caixa, btc, dívida
│   │   ├── risk_monitor.py    # controle em tempo real de risco/exposição
│   │   └── logging/           # logs de produção
│   │
│   └── utils/
│       ├── config.py
│       ├── logger.py
│       ├── math_tools.py
│       └── helpers.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── regression/
│   └── test_data/
│
├── scripts/
│   ├── run_backtest.py
│   ├── train_model.py
│   ├── update_data.py
│   └── generate_features.py
│