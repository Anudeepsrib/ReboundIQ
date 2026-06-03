.PHONY: help dev backend frontend test lint migrate seed eval down clean docker-build

help:
	@echo "ReboundIQ Makefile"
	@echo "  make dev          - Start full local stack (docker compose up --build)"
	@echo "  make backend      - Run API locally (uvicorn, requires services)"
	@echo "  make frontend     - Run Next dev (npm run dev)"
	@echo "  make test         - Backend pytest + frontend checks"
	@echo "  make lint         - Ruff + mypy + eslint + prettier"
	@echo "  make migrate      - Alembic upgrade head"
	@echo "  make seed         - Load realistic synthetic demo data (no PII)"
	@echo "  make eval         - Run AI eval suite (golden + safety + groundedness)"
	@echo "  make down         - docker compose down -v"
	@echo "  make clean        - Remove caches, .next, __pycache__ etc"

dev:
	docker compose up --build

backend:
	cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd apps/web && npm run dev

test:
	cd apps/api && python -m pytest -q --tb=short
	cd apps/web && npm test -- --watchAll=false || true

lint:
	cd apps/api && ruff check . && mypy app --ignore-missing-imports || true
	cd apps/web && npx eslint . --ext .ts,.tsx && npx prettier --check . || true

migrate:
	cd apps/api && alembic upgrade head

seed:
	cd apps/api && python -m scripts.seed_demo

eval:
	cd apps/api && python -m app.evals.runner --suite all

down:
	docker compose down -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf apps/api/.pytest_cache apps/web/.next 2>/dev/null || true
