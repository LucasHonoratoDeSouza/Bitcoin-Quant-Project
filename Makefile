.PHONY: install test lint status download process paper run dashboard backtest backtest-subperiod backtest-walkforward backtest-robustness backtest-stochastic backtest-all clean

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

test:
	$(PYTHON) -m unittest discover -s tests -p 'test*.py' -v

lint:
	$(PYTHON) -m compileall src webapp main.py tests

status:
	$(PYTHON) main.py status

download:
	$(PYTHON) main.py download

process:
	$(PYTHON) main.py process

paper:
	$(PYTHON) main.py paper

run:
	$(PYTHON) main.py full

dashboard:
	$(PYTHON) main.py dashboard

backtest:
	$(PYTHON) tests/backtest/compare_models.py

backtest-subperiod:
	$(PYTHON) tests/backtest/subperiod_analysis.py

backtest-walkforward:
	$(PYTHON) tests/backtest/walkforward_analysis.py

backtest-robustness:
	$(PYTHON) tests/backtest/robustness_analysis.py

backtest-stochastic:
	$(PYTHON) tests/backtest/stochastic_calculus_validation.py

backtest-all:
	$(PYTHON) tests/backtest/compare_models.py
	$(PYTHON) tests/backtest/subperiod_analysis.py
	$(PYTHON) tests/backtest/walkforward_analysis.py
	$(PYTHON) tests/backtest/robustness_analysis.py
	$(PYTHON) tests/backtest/stochastic_calculus_validation.py

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
