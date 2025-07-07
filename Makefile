# variables --------------------------------------------------------->8---------
PYTHON ?= python3
PROJECT_NAME := BiblioTeq
DOCKER_COMPOSE := docker compose
WEB_PORT := 8501
MONGO_PORT := 27017
QDRANT_PORT := 6333


# phony ------------------------------------------------------------->8---------
.PHONY: help up down build status logs check format test test-coverage test-integration test-all clean install dev restart health


# default target ---------------------------------------------------->8---------
help: ## Show this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_.-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Quick Start:"
	@echo "  make install    # Install dependencies"
	@echo "  make up         # Start application"
	@echo "  make test       # Run tests"


# setup targets ----------------------------------------------------->8---------
install: ## Install dependencies using uv
	@echo "Installing dependencies..."
	uv sync

install-dev: ## Install development dependencies
	@echo "Installing development dependencies..."
	uv sync --group dev


# lifecycle targets ------------------------------------------------->8---------
dev: ## Run the web app locally for development
	@echo "Starting web app in development mode..."
	@echo "  will be available at: http://localhost:$(WEB_PORT)"
	PYTHONPATH=$(PWD) uv run streamlit run biblioteq/ui/web/app.py --server.port $(WEB_PORT)

up: ## Start the application with Docker Compose
	@echo "$(PROJECT_NAME) application..."
	$(DOCKER_COMPOSE) up --detach
	@echo ""
	@echo "$(PROJECT_NAME) is starting up!"
	@echo "frontend: http://localhost:$(WEB_PORT)"
	@echo "MongoDB: localhost:$(MONGO_PORT)"
	@echo "Qdrant: http://localhost:$(QDRANT_PORT)"
	@echo ""
	@echo "Useful commands:"
	@echo "  make logs     # View application logs"
	@echo "  make status   # Check service status"
	@echo "  make down     # Stop services"

start: up ## Start the application (alias for up)

down: ## Stop the application
	@echo "Stopping $(PROJECT_NAME) application..."
	$(DOCKER_COMPOSE) down

stop: down ## Stop the application (alias for down)

restart: up ## Restart the application (alias for up)

check-req: ## Create a requirements.txt file from the current environment
	@echo "Exporting requirements from uv..."
	uv export --format requirements-txt --output-file requirements.txt

build: check-req ## Build all application components
	@echo "Building Docker images..."
	$(DOCKER_COMPOSE) build
	@echo "Cleaning up requirements.txt..."
	rm --force requirements.txt

rebuild: clean-docker build ## Clean and rebuild everything
	@echo "Full rebuild completed"

status: ## Show the status of all services
	@echo "📊 Checking $(PROJECT_NAME) service status..."
	$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "Port status:"
	@echo "  Web ($(WEB_PORT)): $$(curl --silent --output /dev/null --write-out "%{http_code}" http://localhost:$(WEB_PORT) 2>/dev/null || echo " Not responding")"
	@echo "  MongoDB ($(MONGO_PORT)): $$(nc --zero localhost $(MONGO_PORT) 2>/dev/null && echo " Open" || echo " Closed")"
	@echo "  Qdrant ($(QDRANT_PORT)): $$(curl --silent --output /dev/null --write-out "%{http_code}" http://localhost:$(QDRANT_PORT)/dashboard 2>/dev/null || echo " Not responding")"

logs: ## Show logs of all services
	@echo "Showing $(PROJECT_NAME) application logs..."
	$(DOCKER_COMPOSE) logs --tail=100 --follow

logs-web: ## Show only web service logs
	@echo "Showing web service logs..."
	$(DOCKER_COMPOSE) logs --tail=100 --follow web

logs-mongo: ## Show only MongoDB logs
	@echo "Showing MongoDB logs..."
	$(DOCKER_COMPOSE) logs --tail=100 --follow mongo

logs-qdrant: ## Show only Qdrant logs
	@echo "Showing Qdrant logs..."
	$(DOCKER_COMPOSE) logs --tail=100 --follow qdrant

health: ## Check health of all services
	@echo "Health check for $(PROJECT_NAME)..."
	@echo "Web service: $$(curl --silent --output /dev/null --write-out "%{http_code}" http://localhost:$(WEB_PORT) 2>/dev/null && echo " Healthy" || echo " Unhealthy")"
	@echo "MongoDB: $$(nc --zero localhost $(MONGO_PORT) 2>/dev/null && echo " Healthy" || echo " Unhealthy")"
	@echo "Qdrant: $$(curl --silent --output /dev/null --write-out "%{http_code}" http://localhost:$(QDRANT_PORT)/health 2>/dev/null && echo " Healthy" || echo " Unhealthy")"


# utility targets --------------------------------------------------->8---------
check: ## Check and fix code style issues
	@echo "Checking code style and fixing issues..."
	uv run ruff check --fix --exit-zero .
	uv run vulture biblioteq/ --min-confidence 70 --ignore-names __init__ --sort-by-size

format: ## Format code with ruff
	@echo "Formatting code..."
	uv run ruff format .

lint: check ## Alias for check (backward compatibility)

clean: ## Clean up temporary files and caches
	@echo "Cleaning up temporary files..."
	find . -type d -name "__pycache__" -exec rm --recursive --force {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm --recursive --force {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm --recursive --force {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true
	find . -name "*~" -delete 2>/dev/null || true
	rm --force requirements.txt

clean-docker: ## Clean up Docker resources
	@echo "Cleaning up Docker resources..."
	$(DOCKER_COMPOSE) down --volumes --rmi local 2>/dev/null || true
	docker system prune --force 2>/dev/null || true

clean-all: clean clean-docker ## Clean everything (files + Docker)

# test targets ------------------------------------------------------>8---------
test: ## Run unit tests (fast, no external dependencies)
	@echo "Running unit tests..."
	OPENAI_API_KEY=test-key \
	uv run python -m pytest \
		--verbose --tb=short \
		test/test_loader.py \
		test/test_retriever.py \
		test/test_semql.py

test-integration: up ## Run integration tests with real databases and API
	@echo "Running integration tests..."
	@echo "  Note: This requires OPENAI_API_KEY and running services"
	@if [ --zero "$$OPENAI_API_KEY" ]; then \
		echo "Loading OPENAI_API_KEY from .env file..."; \
		export $$(grep OPENAI_API_KEY biblioteq/.env 2>/dev/null | xargs); \
	fi && \
	uv run python -m pytest test/test_integration.py --verbose --capture=no --tb=short

test-all: ## Run all tests (unit + integration)
	@echo "Running complete test suite..."
	@$(MAKE) test
	@$(MAKE) test-integration

test-coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	OPENAI_API_KEY=test-key \
	uv run python -m pytest test/test_loader.py test/test_retriever.py \
		--cov=biblioteq --cov-report=html --cov-report=term-missing --verbose
	@echo "Coverage report generated in htmlcov/"

# test-watch: ## Run tests in watch mode (requires pytest-watch)
# 	@echo "Running tests in watch mode..."
# 	OPENAI_API_KEY=test-key \
# 	uv run ptw --runner "python -m pytest test/test_loader.py test/test_retriever.py --verbose"

# data management targets ------------------------------------------->8---------
# load-sample-data: up ## Load sample PDF data (requires running services)
# 	@echo "Loading sample data..."
# 	@if [ --zero "$$OPENAI_API_KEY" ]; then \
# 		echo "Loading OPENAI_API_KEY from .env file..."; \
# 		export $$(grep OPENAI_API_KEY biblioteq/.env 2>/dev/null | xargs); \
# 	fi && \
# 	echo "Processing PDFs from data/book/ directory..." && \
# 	PYTHONPATH=$(PWD) PDF_PATH="$(PWD)/data/book" uv run python -m biblioteq.main

# backup-data: ## Backup MongoDB and Qdrant data
# 	@echo "Creating data backup..."
# 	mkdir -p backups/$$(date +%Y%m%d_%H%M%S)
# 	$(DOCKER_COMPOSE) exec --tty mongo mongodump --archive > backups/$$(date +%Y%m%d_%H%M%S)/mongo_backup.archive

# environment targets ----------------------------------------------->8---------
env-check: ## Check environment setup
	@echo "Checking environment setup..."
	@echo "Python: $$($(PYTHON) --version 2>/dev/null || echo "Not found")"
	@echo "uv: $$(uv --version 2>/dev/null || echo "Not found")"
	@echo "Docker: $$(docker --version 2>/dev/null || echo "Not found")"
	@echo "Docker Compose: $$(docker compose version 2>/dev/null || echo "Not found")"
	@echo "OPENAI_API_KEY: $$([ -n "$$OPENAI_API_KEY" ] && echo "Set" || echo "Not set")"
	@echo ""
	@echo "Project files:"
	@echo "  pyproject.toml: $$([ -f pyproject.toml ] && echo "Present" || echo "Not present")"
	@echo "  docker-compose.yml: $$([ -f docker-compose.yml ] && echo "Present" || echo "Not present")"
	@echo "  .env: $$([ -f biblioteq/.env ] && echo "Present" || echo "Not present")"

env-setup: ## Set up development environment from scratch
	@echo "Setting up development environment..."
	@echo "Installing uv (if not present)..."
	@which uv > /dev/null || curl --location --silent --show-error --fail https://astral.sh/uv/install.sh | sh
	@echo "Installing dependencies..."
	@$(MAKE) install-dev
	@echo "Creating .env file from example (if needed)..."
	@[ -f biblioteq/.env ] || cp biblioteq/.env.example biblioteq/.env
	@echo ""
	@echo "Development environment setup completed!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit biblioteq/.env to add your OPENAI_API_KEY"
	@echo "  2. Run 'make up' to start the application"
	@echo "  3. Run 'make test' to verify everything works"
