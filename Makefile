.PHONY: install download process run clean

PYTHON = venv/bin/python
PIP = venv/bin/pip

install:
	$(PIP) install -r requirements.txt

download:
	$(PYTHON) src/data/download.py

process:
	$(PYTHON) src/strategy/process_data.py

run: download process
	@echo "🚀 Daily workflow completed!"

paper: download process
	$(PYTHON) src/main_paper_trading.py

clean:
	rm -rf __pycache__
	rm -rf src/__pycache__
	rm -rf src/*/__pycache__
