SOURCES = app tests

.DEFAULT_GOAL := help
py = poetry run

DOCKER_COMPOSE_FILE = contrib/docker-compose.yml
DOCKER_COMPOSE_PROJECT_NAME = bts


help: ## Display this help screen
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

install: ## Install project dependencies
	poetry install --no-interaction --no-ansi
.PHONY: install

format: ## Format the source code
	$(py) ruff check --config pyproject.toml --fix $(SOURCES) alembic
	$(py) ruff format --config pyproject.toml $(SOURCES) alembic
.PHONY: format

lint: ## Lint the source code
	poetry check
	$(py) ruff check --config pyproject.toml  $(SOURCES)
	$(py) mypy $(SOURCES)
	$(py) bandit -r app
.PHONY: lint

test: ## Run tests
	$(py) pytest
.PHONY: test

coverage: ## Run unit tests and check coverage
	$(py) coverage run -m pytest --cov=app tests -n0
	$(py) coverage report  --precision=2 -m --fail-under=80
.PHONY: coverage


compose-up: ## Run the development server with docker-compose
	COMPOSE_PROJECT_NAME=${DOCKER_COMPOSE_PROJECT_NAME} docker-compose -f ${DOCKER_COMPOSE_FILE} up --build --remove-orphans -d
.PHONY: compose-up

compose-down: ## Stop the development server with docker-compose
	COMPOSE_PROJECT_NAME=${DOCKER_COMPOSE_PROJECT_NAME} docker-compose -f ${DOCKER_COMPOSE_FILE} down --remove-orphans -t 0 -v
.PHONY: compose-down

migrate:  ## Run the alembic migrations
	$(py) alembic upgrade head
.PHONY: migrate

run-web: ## Run the web server
	$(py) gunicorn -w 1 -k uvicorn.workers.UvicornWorker app.asgi:fastapi_app --bind 0.0.0.0:8000 --timeout 300 --log-level debug --reload
.PHONY: run-web

run-workers: ## Run misc tasks workers
	$(py) python -m app.cmd run-workers
.PHONY: run-workers


jwt: ## Generate a JWT token
	$(py) python scripts/get_jwt.py
.PHONY: jwt