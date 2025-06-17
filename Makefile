# variables
PYTHON ?= python3
PYTHON_VENV ?= .venv

PHONY = help up down log ps build lint format test test-coverage

.PHONY: $(PHONY)

# Default target
help: ## Show this help message
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# docker compose
up: ## Start docker compose services
	@echo "Starting Docker Compose services..."
	docker compose up --build --detach

down: ## Stop docker compose services
	@echo "Stopping Docker Compose services..."
	docker compose down

log: ## Show the logs of docker compose services
	@echo "Showing logs of Docker Compose services..."
	docker compose logs --follow --tail=100

ps: ## Show the status of the docker compose services
	@echo "Showing status of Docker Compose services..."
	docker compose ps

build: ## Build docker compose services
	@echo "Building Docker Compose services..."
	docker compose build

# code
lint: ## Lint code
	ruff --fix --exit-zero --show-source --line-length 100 .

format: ## Format code
	ruff format --exit-zero --line-length 100 .

# test
test: ## Run tests
	@echo "Running tests..."
	OPENAI_API_KEY=test-key pytest application

test-coverage: ## Run tests with coverage
	@echo "Running tests with coverage..."
	OPENAI_API_KEY=test-key pytest --cov=application --cov-report=html --cov-report=term-missing application
