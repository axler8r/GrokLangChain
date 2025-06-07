# variables
PYTHON ?= python3
PYTHON_VENV ?= .venv


# docker compose
up:
	docker compose up --build --detach

down:
	docker compose down

log:
	docker compose logs --follow --tail=100

ps:
	docker compose ps

build:
	docker compose build

# code
lint:
	ruff --fix --exit-zero --show-source --line-length 100 .

format:
	ruff format --exit-zero --line-length 100 .

# test
test:
	pytest test

test-coverage:
	pytest --cov=src --cov-report=html --cov-report=term-missing test

