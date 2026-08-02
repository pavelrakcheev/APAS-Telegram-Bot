PYTHON ?= python3
VENV := .venv
BIN := $(VENV)/bin

.PHONY: help setup install run test check lint format smoke docker-up docker-down clean test-cov pre-commit dev

help:
	@echo "Targets:"
	@echo "  setup       — создать venv и установить зависимости"
	@echo "  install     — переустановить зависимости"
	@echo "  run         — запустить Telegram-бота"
	@echo "  test        — запустить все тесты"
	@echo "  test-cov    — запустить тесты с покрытием"
	@echo "  smoke       — запустить smoke-тест"
	@echo "  lint        — проверить код (ruff)"
	@echo "  format      — форматировать код (ruff)"
	@echo "  check       — проверить синтаксис всех .py"
	@echo "  pre-commit  — запустить pre-commit на всех файлах"
	@echo "  docker-up   — собрать и запустить bot + mini-app в Docker"
	@echo "  docker-down — остановить Docker-сервисы"
	@echo "  clean       — удалить venv и __pycache__"
	@echo "  dev         — установить dev-зависимости"

setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	@grep -v '^google-cloud-aiplatform' requirements.txt > /tmp/apas-req.txt && \
		$(BIN)/pip install -r /tmp/apas-req.txt && rm /tmp/apas-req.txt

install:
	@grep -v '^google-cloud-aiplatform' requirements.txt > /tmp/apas-req.txt && \
		$(BIN)/pip install -r /tmp/apas-req.txt && rm /tmp/apas-req.txt

dev:
	$(BIN)/pip install -r requirements-dev.txt
	$(BIN)/pre-commit install

run:
	$(BIN)/python main.py

test:
	$(BIN)/pytest tests/ -v

test-cov:
	$(BIN)/pytest tests/ -v --cov=Models --cov=Commands --cov-report=html --cov-report=term-missing

smoke:
	$(BIN)/python tests/smoke_test.py

lint:
	$(BIN)/ruff check .

format:
	$(BIN)/ruff format .

check:
	$(PYTHON) -m compileall -q .

pre-commit:
	$(BIN)/pre-commit run --all-files

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

clean:
	rm -rf $(VENV) htmlcov .coverage coverage.xml
	find . -name __pycache__ -type d -not -path './.git/*' -exec rm -rf {} +
