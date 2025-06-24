# variables --------------------------------------------------------->8---------
APPLICATION_HOME := application
COMPONENTS = historian librarian loader orchestrator
PYTHON ?= python3
PYTHON_VENV ?= .venv


# phony ------------------------------------------------------------->8---------
.PHONY = help lint format test test-coverage \
	loader.up loader.down loader.build loader.status loader.logs \
	application.up application.down application.build application.build-force application.status application.logs \
	build-historian build-librarian build-loader build-orchestrator \
	historian.build librarian.build orchestrator.build


# default target ---------------------------------------------------->8---------
help: ## Show this help message
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_.-]+:.*?## / {printf "  %-25s %s\n", $$1, $$2}' $(MAKEFILE_LIST)


# application targets ----------------------------------------------->8---------
application.up: ## Start the application
	@echo "Starting application..."
	docker compose up --detach

application.down: ## Stop the application
	@echo "Stopping application..."
	docker compose down

application.build: build-historian build-librarian build-loader build-orchestrator ## Build all application components
	@echo "Application build complete...
	@echo "Summary: All buildable components have been processed"

application.build-force: ## Force rebuild all components (ignore dependency groups that might fail)
	@echo "Force building all components..."
	@$(MAKE) --keep-going build-historian build-librarian build-loader build-orchestrator

# Component build targets ------------------------------------------>8---------
build-historian: ## Build historian component
	@echo "Building historian component..."
	@if uv export --group historian --output-file $(APPLICATION_HOME)/historian/requirements.txt 2>/dev/null; then \
		echo "✓ Generated requirements.txt for historian"; \
		if docker compose build historian; then \
			echo "✓ Successfully built historian"; \
		else \
			echo "✗ Failed to build historian with Docker"; \
		fi; \
		rm -f $(APPLICATION_HOME)/historian/requirements.txt; \
	else \
		echo "✗ Failed to generate requirements.txt for historian (skipping build)"; \
	fi

build-librarian: ## Build librarian component
	@echo "Building librarian component..."
	@if uv export --group librarian --output-file $(APPLICATION_HOME)/librarian/requirements.txt 2>/dev/null; then \
		echo "✓ Generated requirements.txt for librarian"; \
		if docker compose build librarian; then \
			echo "✓ Successfully built librarian"; \
		else \
			echo "✗ Failed to build librarian with Docker"; \
		fi; \
		rm -f $(APPLICATION_HOME)/librarian/requirements.txt; \
	else \
		echo "✗ Failed to generate requirements.txt for librarian (skipping build)"; \
	fi

build-loader: ## Build loader component
	@echo "Building loader component..."
	@if uv export --group loader --output-file $(APPLICATION_HOME)/loader/requirements.txt 2>/dev/null; then \
		echo "✓ Generated requirements.txt for loader"; \
		if docker compose build loader; then \
			echo "✓ Successfully built loader"; \
		else \
			echo "✗ Failed to build loader with Docker"; \
		fi; \
		rm -f $(APPLICATION_HOME)/loader/requirements.txt; \
	else \
		echo "✗ Failed to generate requirements.txt for loader (skipping build)"; \
	fi

build-orchestrator: ## Build orchestrator component
	@echo "Building orchestrator component..."
	@if uv export --group orchestrator --output-file $(APPLICATION_HOME)/orchestrator/requirements.txt 2>/dev/null; then \
		echo "✓ Generated requirements.txt for orchestrator"; \
		if docker compose build orchestrator; then \
			echo "✓ Successfully built orchestrator"; \
		else \
			echo "✗ Failed to build orchestrator with Docker"; \
		fi; \
		rm -f $(APPLICATION_HOME)/orchestrator/requirements.txt; \
	else \
		echo "✗ Failed to generate requirements.txt for orchestrator (skipping build)"; \
	fi


# loader targets ---------------------------------------------------->8---------
loader.up: ## Start the loader service
	@echo "Starting loader service..."
	docker compose up -d loader

loader.down: ## Stop the loader service
	@echo "Stopping loader service..."
	docker compose stop loader

loader.build: build-loader ## Build the loader service

loader.status: ## Check the status of the loader service
	@echo "Checking loader service status..."
	docker compose ps loader

loader.logs: ## Fetch loader service logs
	@echo "Fetching loader service logs..."
	docker compose logs -f loader


# code formatting and linting targets ------------------------------->8---------
code.lint: ## Lint code
	ruff --fix --exit-zero --show-source --line-length 100 .

code.format: ## Format code
	ruff format --exit-zero --line-length 100 .

# test
code.test: ## Run tests
	@echo "Running tests..."
	OPENAI_API_KEY=test-key pytest test

code.test-coverage: ## Run tests with coverage
	@echo "Running tests with coverage..."
	OPENAI_API_KEY=test-key pytest --cov=application --cov-report=html --cov-report=term-missing application


# Individual service build shortcuts -------------------------------->8---------
historian.build: build-historian ## Build historian service
librarian.build: build-librarian ## Build librarian service  
orchestrator.build: build-orchestrator ## Build orchestrator service
