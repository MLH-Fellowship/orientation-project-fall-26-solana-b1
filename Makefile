PYTHON ?= python3

BACKEND_DIR := backend
BACKEND_VENV := $(BACKEND_DIR)/.venv
BACKEND_PYTHON := $(BACKEND_VENV)/bin/python

.PHONY: backend-install backend-run backend-test check-backend-python

check-backend-python:
	@$(PYTHON) -c 'import sys; version = sys.version_info[:2]; assert (3, 10) <= version < (3, 14), f"Python 3.10-3.13 is required; found {sys.version.split()[0]}"'

backend-install: check-backend-python
	$(PYTHON) -m venv $(BACKEND_VENV)
	$(BACKEND_PYTHON) -m pip install -r $(BACKEND_DIR)/requirements.txt
	@test -f $(BACKEND_DIR)/.env || cp $(BACKEND_DIR)/.env.example $(BACKEND_DIR)/.env

backend-run:
	@test -x $(BACKEND_PYTHON) || (echo "Run 'make backend-install' first." && exit 1)
	cd $(BACKEND_DIR) && .venv/bin/python -m uvicorn app.main:app --reload --port 8000

backend-test:
	@test -x $(BACKEND_PYTHON) || (echo "Run 'make backend-install' first." && exit 1)
	cd $(BACKEND_DIR) && .venv/bin/python -m pytest tests -q

