# variables --------------------------------------------------------->8---------
APPLICATION_HOME := application
COMPONENTS = historian librarian loader orchestrator

PYTHON ?= python3
PYTHON_VENV ?= .venv

# phony ------------------------------------------------------------->8---------
.PHONY = help lint format test test-coverage loader.up loader.down loader.build loader.status loader.logs

# default target ---------------------------------------------------->8---------
help: ## Show this help message
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# application targets ----------------------------------------------->8---------
application.up: ## Start the application
	@echo "Starting application..."
	docker compose up --detach

application.down: ## Stop the application
	@echo "Stopping application..."
	docker compose down

application.build: ## Build the application
	@echo "Building application..."
	for component in $(COMPONENTS); do \
		uv export --group $$component --output $$APPLICATION_HOME/$$component/requirements.txt; \
	done
	docker compose build
	@echo "Removing requirements.txt files after build..."
	for component in $(COMPONENTS); do \
		rm -f $(APPLICATION_HOME)/$$component/requirements.txt; \
	done

application.status: ## Check the status of the application
	@echo "Checking application status..."
	docker compose ps

application.logs: ## Fetch application logs
	@echo "Fetching application logs..."

# loader targets ---------------------------------------------------->8---------
loader.up: ## Start the loader service
	@echo "Starting loader service..."
	docker compose up -d loader

loader.down: ## Stop the loader service
	@echo "Stopping loader service..."
	docker compose stop loader

loader.build: ## Build the loader service
	@echo "Generating requirements.txt for loader..."
	uv export --group loader --output $(APPLICATION_HOME)/loader/requirements.txt
	@echo "Building loader service..."
	docker compose build loader
	@echo "Removing requirements.txt after build..."
	rm -f $(APPLICATION_HOME)/loader/requirements.txt

loader.status: ## Check the status of the loader service
	@echo "Checking loader service status..."
	docker compose ps loader

loader.logs: ## Fetch loader service logs
	@echo "Fetching loader service logs..."
	docker compose logs -f loader

# code
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
