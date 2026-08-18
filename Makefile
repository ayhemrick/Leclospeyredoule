# Convenience targets. Everything here also works as a plain command; see the
# README if you would rather not use make.
.DEFAULT_GOAL := help
.PHONY: help up down logs seed test lint format e2e migrate revision

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

up: ## Start the whole stack with hot reload
	docker compose up --build

down: ## Stop the stack and drop the volumes
	docker compose down -v

logs: ## Follow the API logs
	docker compose logs -f api

migrate: ## Apply database migrations
	cd backend && uv run alembic upgrade head

revision: ## Autogenerate a migration: make revision m="what changed"
	cd backend && uv run alembic revision --autogenerate -m "$(m)"

test: ## Run both test suites
	cd backend && uv run pytest
	cd frontend && npm run test

e2e: ## Run the end-to-end suite (needs the stack running)
	cd frontend && npm run e2e

lint: ## Lint and type-check everything
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app
	cd frontend && npm run lint -- --max-warnings 0 && npm run typecheck

format: ## Format everything
	cd backend && uv run ruff format . && uv run ruff check . --fix
	cd frontend && npm run format
