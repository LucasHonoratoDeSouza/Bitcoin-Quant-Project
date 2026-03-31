.PHONY: install test lint status download process paper run dashboard clean

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

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
