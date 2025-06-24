# variables --------------------------------------------------------->8---------
PYTHON ?= python3


# phony ------------------------------------------------------------->8---------
.PHONY = help up down build status logs lint format test test-coverage


# default target ---------------------------------------------------->8---------
help: ## Show this help message
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_.-]+:.*?## / {printf "  %-25s %s\n", $$1, $$2}' $(MAKEFILE_LIST)


# lifecycle targets ------------------------------------------------->8---------
up: ## Start the application
	@echo "Starting application..."
	docker compose up --detach

down: ## Stop the application
	@echo "Stopping application..."
	docker compose down

check-req: ## Create a requirements.txt file from the current environment
	@echo "Checking requirements..."
	@if [ -f requirements.txt ]; then \
		echo "Removing existing requirements.txt..."; \
		rm requirements.txt; \
	fi
	@echo "Creating new requirements.txt..."
	uv --export requirements.txt --output-file requirements.txt

build: check-req ## Build all application components
	@echo "Application build complete...
	docker compose build


status: ## Show the status of the application
	@echo "Checking application status..."
	docker compose ps

logs: ## Show logs of the application
	@echo "Showing application logs..."
	docker compose logs --tail=100 --follow


# code formatting and linting targets ------------------------------->8---------
lint: ## Lint code
	ruff --fix --exit-zero --show-source --line-length 100 .

format: ## Format code
	ruff format --exit-zero --line-length 100 .

# test
test: ## Run tests
	@echo "Running tests..."
	OPENAI_API_KEY=test-key pytest test

test-coverage: ## Run tests with coverage
	@echo "Running tests with coverage..."
	OPENAI_API_KEY=test-key pytest --cov=application --cov-report=html --cov-report=term-missing application
