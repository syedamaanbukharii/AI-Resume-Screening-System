.PHONY: install dev migrate revision test lint format up down build docs

install:
	pip install -r backend/requirements.txt

dev:
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

migrate:
	cd backend && alembic upgrade head

revision:
	cd backend && alembic revision --autogenerate -m "$(m)"

test:
	cd backend && pytest -q

lint:
	cd backend && ruff check . && black --check .

format:
	cd backend && black . && ruff check --fix .

# --- Docker ---
up:
	docker compose -f docker/docker-compose.yml up --build

down:
	docker compose -f docker/docker-compose.yml down

build:
	docker build -f docker/Dockerfile.backend -t rs-backend .
	docker build -f docker/Dockerfile.frontend -t rs-frontend .

# Fully-offline stack (Gemma + nomic via Ollama)
up-offline:
	docker compose -f docker/docker-compose.yml --profile offline up --build
