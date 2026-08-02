PYTHON ?= python3
VENV := .venv
BIN := $(VENV)/bin

.PHONY: help setup install run test check smoke docker-up docker-down clean

help:
	@echo "Targets:"
	@echo "  setup       — создать venv и установить зависимости"
	@echo "  install     — переустановить зависимости"
	@echo "  run         — запустить Telegram-бота"
	@echo "  test        — запустить smoke-тест"
	@echo "  check       — проверить синтаксис всех .py"
	@echo "  docker-up   — собрать и запустить bot + mini-app в Docker"
	@echo "  docker-down — остановить Docker-сервисы"
	@echo "  clean       — удалить venv и __pycache__"

setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	@grep -v '^google-cloud-aiplatform' requirements.txt > /tmp/apas-req.txt && \
		$(BIN)/pip install -r /tmp/apas-req.txt && rm /tmp/apas-req.txt

install:
	@grep -v '^google-cloud-aiplatform' requirements.txt > /tmp/apas-req.txt && \
		$(BIN)/pip install -r /tmp/apas-req.txt && rm /tmp/apas-req.txt

run:
	$(BIN)/python main.py

test: smoke

smoke:
	$(BIN)/python tests/smoke_test.py

check:
	$(PYTHON) -m compileall -q .

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

clean:
	rm -rf $(VENV)
	find . -name __pycache__ -type d -not -path './.git/*' -exec rm -rf {} +
