PYTHON ?= python3

BACKEND_DIR := backend
BACKEND_VENV := $(BACKEND_DIR)/.venv
BACKEND_PYTHON := $(abspath $(BACKEND_VENV)/bin/python)
FRONTEND_DIR := frontend

.PHONY: backend-install backend-migrate backend-seed backend-run backend-test check-backend-python frontend-install frontend-run frontend-build

check-backend-python:
	@$(PYTHON) -c 'import sys; version = sys.version_info[:2]; assert (3, 10) <= version < (3, 14), f"Python 3.10-3.13 is required; found {sys.version.split()[0]}"'

backend-install: check-backend-python
	$(PYTHON) -m venv $(BACKEND_VENV)
	$(BACKEND_PYTHON) -m pip install --upgrade pip
	$(BACKEND_PYTHON) -m pip install -r $(BACKEND_DIR)/requirements.txt
	@test -f $(BACKEND_DIR)/.env || cp $(BACKEND_DIR)/.env.example $(BACKEND_DIR)/.env

backend-migrate:
	@test -x $(BACKEND_PYTHON) || (echo "Run 'make backend-install' first." && exit 1)
	cd $(BACKEND_DIR) && $(BACKEND_PYTHON) -m alembic upgrade head

backend-seed:
	@test -x $(BACKEND_PYTHON) || (echo "Run 'make backend-install' first." && exit 1)
	cd $(BACKEND_DIR) && $(BACKEND_PYTHON) -m scripts.seed

backend-run:
	@test -x $(BACKEND_PYTHON) || (echo "Run 'make backend-install' first." && exit 1)
	cd $(BACKEND_DIR) && $(BACKEND_PYTHON) -m uvicorn app.main:app --reload --port 8000

backend-test:
	@test -x $(BACKEND_PYTHON) || (echo "Run 'make backend-install' first." && exit 1)
	cd $(BACKEND_DIR) && $(BACKEND_PYTHON) -m pytest tests -q

frontend-install:
	cd $(FRONTEND_DIR) && npm ci

frontend-run:
	@test -d $(FRONTEND_DIR)/node_modules || (echo "Run 'make frontend-install' first." && exit 1)
	cd $(FRONTEND_DIR) && npm run dev

frontend-build:
	@test -d $(FRONTEND_DIR)/node_modules || (echo "Run 'make frontend-install' first." && exit 1)
	cd $(FRONTEND_DIR) && npm run build
