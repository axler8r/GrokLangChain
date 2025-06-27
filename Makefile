# variables --------------------------------------------------------->8---------
PYTHON ?= python3


# phony ------------------------------------------------------------->8---------
.PHONY: help up down build status logs lint format test test-coverage


# default target ---------------------------------------------------->8---------
help: ## Show this help message
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_.-]+:.*?## / {printf "  %-25s %s\n", $$1, $$2}' $(MAKEFILE_LIST)


# lifecycle targets ------------------------------------------------->8---------
dev: ## Run the web app locally for development
	@echo "Starting web app in development mode..."
	PYTHONPATH=$(PWD) uv run streamlit run biblioteq/ui/web/app.py

up: ## Start the application
	@echo "Starting application..."
	docker compose up --detach
	@echo ""
	@echo "✓ BiblioTeq is starting up!"
	@echo "📚 Web frontend will be available at: http://localhost:8501"
	@echo ""
	@echo "Use 'make logs' to view application logs"
	@echo "Use 'make status' to check service status"

down: ## Stop the application
	@echo "Stopping application..."
	docker compose down

check-req: ## Create a requirements.txt file from the current environment
	@echo "Exporting requirements from uv..."
	uv export --format requirements-txt --output-file requirements.txt

build: check-req ## Build all application components
	@echo "Building Docker images..."
	docker compose build
	@echo "Cleaning up requirements.txt..."
	rm -f requirements.txt
	@echo "Application build complete..."


status: ## Show the status of the application
	@echo "Checking application status..."
	docker compose ps

logs: ## Show logs of the application
	@echo "Showing application logs..."
	docker compose logs --tail=100 --follow


# code formatting and linting targets ------------------------------->8---------
lint: ## Lint code
	ruff check --fix --exit-zero --line-length 100 .

format: ## Format code
	ruff format --line-length 100 .

# test
test: ## Run unit tests (fast, no external dependencies)
	@echo "Running unit tests..."
	OPENAI_API_KEY=test-key uv run python -m pytest test/loader/ test/retriever/test_retriever_unit.py -v

test-integration: ## Run integration tests with real databases and API
	@echo "Running integration tests..."
	@echo "⚠️  Make sure Docker containers are running: make up"
	@if [ -z "$$OPENAI_API_KEY" ]; then \
		echo "⚠️  Loading OPENAI_API_KEY from .env file..."; \
		export $$(grep OPENAI_API_KEY biblioteq/.env 2>/dev/null | xargs); \
	fi && \
	uv run python -m pytest test/integration/ -v -s

test-all: ## Run all tests (unit + integration)
	@echo "Running all tests..."
	@$(MAKE) test
	@$(MAKE) test-integration

test-coverage: ## Run tests with coverage
	@echo "Running tests with coverage..."
	OPENAI_API_KEY=test-key python -m pytest --cov=biblioteq --cov-report=html --cov-report=term-missing test
