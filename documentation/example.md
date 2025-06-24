## Example `Dockerfile`
```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    <PACKAGE_NAMES_GO_HERE> \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --requirement requirements.txt
RUN rm requirements.txt

COPY .emv .
COPY *.py .

CMD ["python", "main.py"]
```

## Example `Makefile`
```Makefile
# variables --------------------------------------------------------->8---------
APPLICATION_HOME := application
COMPONENTS = component1 component2 component3
<OTHER_VARIABLES_GO_HERE> = <VALUES_GO_HERE>


# phony ------------------------------------------------------------->8---------
.PHONY: <TARGET_NAMES_GO_HERE>


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

applicaiton.build: ## Build the application
    @echo "Building application..."
    for component in $(COMPONENTS); do \
        uv export --group $$component --output $$APPLICATION_HOME/$$component/requirements.txt
    done
    docker compose build

application.status: ## Check the status of the application
    @echo "Checking application status..."
    docker compose ps

application.logs: ## Fetch application logs
    @echo "Fetching application logs..."
    docker compose logs --follow

# <COMPONENT_NAME> targets ------------------------------------------>8---------
<COMPONENT_NAME>.build: ## Build <COMPONENT_NAME>
    @echo "Building <COMPONENT_NAME> service..."
    uv export --group <COMPONENT_NAME> --output <COMPONENT_ROOT_DIR>/requirements.txt
    docker compose build <COMPONENT_NAME>

<COMPOENT_NAME>.up: ## Start <COMPONENT_NAME>
    @echo "Starting <COMPONENT_NAME> service..."
    docker compose up -d <COMPONENT_NAME>

<COMPONENT_NAME>.down: ## Stop <COMPONENT_NAME>
    @echo "Stopping <COMPONENT_NAME> service..."
    docker compose down <COMPONENT_NAME>

<COMPOENT_NAME>.status: ## Check the status of <COMPONENT_NAME>
    @echo "Checking <COMPONENT_NAME> service status..."
    docker compose ps <COMPONENT_NAME>

<COMPONENT_NAME>.logs: ## Fetch <COMPONENT_NAME> logs
    @echo "Fetching <COMPONENT_NAME> service logs..."
    docker compose logs -f <COMPONENT_NAME>

<COMPONENT_NAME>.test: ## Run tests for <COMPONENT_NAME>
    @echo "Running tests for <COMPONENT_NAME> service..."
    pytest <COMPONENT_ROOT_DIR>/test

<OTHER_TARGETS_GO_HERE>


# housekeeping targets ---------------------------------------------->8---------
clean: ## Clean up application
    @echo "Cleaning up application..."
    docker compose down --volumes --remove-orphans
    find . -name '*.pyc' -delete
    find . -name '__pycache__' -delete
    find . -name '.pytest_cache' -delete
    find . -name '.ruff_cache' -delete
    find . -name 'requirements.txt' -delete

<OTHER_TARGETS_GO_HERE>


# code formatting and linting targets ------------------------------->8---------
code.lint: ## Lint code
    @echo "Running ruff..."
    <COMMAND_TO_RUN_RUFF_TO_CHECK_CODE>

code.format: ## Format code
    @echo "Running ruff for code formatting..."
    <COMMAND_TO_RUN_RUFF_TO_FORMAT_CODE>

code.pytest: ## Test code
    @echo "Running pytest..."
    <COMMAND_TO_RUN_PYTEST>

<OTHER_TARGETS_GO_HERE>
```


## Example Project Directory Structure
```plaintext
project-root/
  |- application
  |    |- <service_name>/
  |    └- <other_service_name>/
  ├─ share/                     # Shared code
  ├─ data/
  ├─ test/
  |    |- <service_name>/
  |    └- <other_service_name>/
  ├─ docker-compose.yml
  └- Makefile
```


## Example Serive Deirectory Structure
```plaintext
<service_name>/
  |- .env                       # Environment variables for the service
  |- .env.example
  |- __init__.py                # Neccessarry?
  |- <service_name>.py          # Functionality of the service
  |- <other_service_files>
  |- main.py                    # Entry point for the service
  |- Dockerfile                 # Dockerfile for the service
  └- README.md                  # Documentation for the service
```


## Example `REAME.md`
```markdown
# <service_name>
This is the documentation for the `<service_name>` service.
It is part of the larger project described in `documentation/architecture.md`.


## Overview
This service is responsible for `<brief_description_of_service_functionality>`.


## Directory Structure
~~~plaintext
<directory_structure>
~~~


## Usage
To run this service, use the following command:
~~~bash
<command_to_run_service>
~~~


## Environment Variables
The service uses the following environment variables:
- `ENV_VAR_1`: Description of ENV_VAR_1
- `ENV_VAR_2`: Description of ENV_VAR_2


## Dependencies
This service depends on the following packages:
- `package1`: Description of package1
- `package2`: Description of package2


## Deployment
To deploy this service, use the following command:
~~~bash
<command_to_deploy_service>
~~~
```
