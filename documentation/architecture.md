# Project Overview
The project is called **BiblioTeq**.

This is a monorepo containing multiple Python services.

The application will be deployed as a **Docker Compose** application.


## Services
- `librarian`: The frontent.
- `orchestrator`: An agentic service that interprets user requests, pulls data
    from a vector database and generates responses based on user queries.
- `loader`: Chunks and encodes data from pdf files (my books) and stores
    it in a vector database and document database.
- `historian`: Stores and retrieves user query history.
- `inspector`: Monitors the health and performance of the application. Optional.

## Shared Code
- `share`: Contains shared code and utilities used by other services.

## Technologies
- **Python**: The programming language used for all services.
- **Docker**: For containerizing services.
- **Docker Compose**: For orchestrating the multi-container application.
- **Streamlit**: For building the user interface.
- **AutoGen**: For building the agentic framework.
- **qdrant**: The vector database for storing and retrieving embeddings.
- **MongoDB**: For storing dockument chunks and user query history.
- **tiktoken**: For embedding and chunking data from pdf files.
- **FastAPI**: Used for exposing APIs for services.
- **Graphana**: Monitoring the health and performance of the application. Optional.
- **Prometheus**: Used for monitoring and alerting. Optional.


## Libraries
These are the _proposed_ libraries to be used in the project:
- `streamlit`: For the user interface.
- `autogen`: For the agentic workflow that integrates the front end and data
    storage services.
- `loguru`: For logging.
- `python-dotenv`: To manage environment variables.
- `fastapi`: For exposing services as APIs.
  - `pydantic`: For definitions and validations of API payloads.
- `python-dotenv`: For managing environment variables in all services.
- `qdrant-client`: Used for interacting with the Qdrant vector database.
- `pymongo`: Used for interacting with MongoDB document database.
- `tiktoken`: Used for embedding and chunking data from pdf files.
- `pypdf`: Used for reading pdf files.


## CICD Utilities
- `make` for build automation and task management.
- `pytest`: For testing all services.
- `ruff` for linting and code formatting.
- `uv` for dependency management and virtual environments.
- Github Actions for continuous integration and deployment (CICD).


## Project Structure
Here is a _proposed_ layout of project's structure:
``` plaintext
project-root/
  ├─ application/                 # Source directory
  |    |- historian               # Service directory
  |    |    |- .env               # Environment variables for the service
  |    |    |- .env.example
  |    |    |- __init__.py        # Neccessarry?
  |    |    |- historian.py       # Functionality of the service
  |    |    |- main.py            # Entry point for the service
  |    |    |- <...>              # Other service files
  |    |    |- Dockerfile         # Dockerfile for the service
  |    |    └- README.md          # Documentation for the service
  |    |- librarian/
  |    |    |- .env
  |    |    |- .env.example
  |    |    |- __init__.py
  |    |    |- librarian.py
  |    |    |- main.py
  |    |    |- Dockerfile
  |    |    └- README.md
  |    |- loader/
  |    |    |- .env
  |    |    |- .env.example
  |    |    |- __init__.py
  |    |    |- loader.py
  |    |    |- main.py
  |    |    |- Dockerfile
  |    |    └- README.md
  |    └- orchestrator/
  |         |- .env
  |         |- .env.example
  |         |- __init__.py
  |         |- orchestrator.py
  |         |- main.py
  |         |- Dockerfile
  |         └- README.md
  ├─ share/
  |- data/
  ├─ test/
  |    loader/
  |    |- __init__.py
  |    └- test_loader.py
  |- docker-compose.yml
  └- Makefile
```

# Copilot Instructions


## General Guidelines
- Use Python 3.12 or later for all services.
- Follow PEP 8 style guidelines for Python code.
- Use type hints for variables, function signatures and class definitions.
- Annotate all functions and classes with type hints.
- Write docstrings for all functions and classes, following the Google style guide.
