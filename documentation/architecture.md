# Project Overview
The project is called **BiblioQuiz**.

This is a monorepo containing multiple Python components.

The application will be deployed as a **Docker Compose** application.


## Components
- `share`: Contains shared code and utilities used by other components.
- `librarian`: The frontent.
- `orchestrator`: An agentic component that interprets user requests, pulls data
  from a vector database and generates responses based on user queries.
- `loader`: Chunks and encodes data from pdf files (my books) and stores
  it in a vector database for retrieval by the agent.
- `historian`: Stores and retrieves user query history.
- `monitor`: Monitors the health and performance of the application.


## Technologies
- **Python**: The primary programming language used for all components.
- **Docker**: For containerizing components.
- **Docker Compose**: For orchestrating the multi-container application.
- **Streamlit**: Used for building the `librarian` user interface.
- **AutoGen**: Used for building the `orchestrator` agentic framework.
- **qdrant**: The vector database for storing and retrieving embeddings directly accessed by other services.
- **MongoDB**: Used for storing user query history in the `historian` component.
- **LangChain**: For embedding and chunking data from pdf files in the `loader`.
- **FastAPI**: Used for building APIs in the `agent` component.
- **Graphana**: Used for monitoring the health and performance of the application.
- **Prometheus**: Used for monitoring and alerting in the `monitor` component.


## Libraries
- `streamlit`: Used for building the frontend user interface.
- `autogen`: Used for building the agent that interacts with the vector database.
- `loguru`: Used for logging and debugging.
- `python-dotenv`: Manage secrets and environment variables.
- `fastapi`: Used for building APIs in the `agent` component.
- `pydantic`: Used for data validation and serialization in the `agent` component.
- `python-dotenv`: Used for managing environment variables in all components.
- `tqdm`: Used for progress bars in the `loader` component.
- `qdrant-client`: Used for interacting with the Qdrant vector database directly
  component.
- `pymongo`: Used for interacting with MongoDB in the `historian` component.
- `LangChain`: Used for embedding and chunking data from pdf files in the `loader`
  component.
- `PyPDF2`: Used for reading pdf files in the `loader` component.
- `pytest`: Used for testing all components.


## Utilities
- `uv` for dependency management and virtual environments.
- `ruff` for linting and code formatting.
- `make` for build automation and task management.


## Project Structure
Here is an outline of important directories and files in the project:

``` plaintext
project-root/
  ├─ application/
  |    |- librarian/
  |    |    |- .env
  |    |    |- librarian.py
  |    |    |- main.py
  |    |    └- Dockerfile
  |    |- orchestrator/
  |    |    |- .env
  |    |    |- orchestrator.py
  |    |    |- main.py
  |    |    └- Dockerfile
  |    |- historian
  |    |    |- .env
  |    |    |- historian.py
  |    |    |- main.py
  |    |    └- Dockerfile
  |    └- loader/
  |         |- src/
  |         |    |- __init__.py
  |         |    |- main.py
  |         |    └- pdf_processor.py
  |         |- test/
  |         |    |- __init__.py
  |         |    └- test_pdf_processor.py
  |         |- .env
  |         |- Dockerfile
  |         |- README.md
  |         |- run_loader.sh
  |         └- pyproject.toml
  ├─ share/
  |- data/
  ├─ test/
  |- docker-compose.yml
  └- Makefile
```

# Copilot Instructions


## General Guidelines
- Use Python 3.12 or later for all components.
- Follow PEP 8 style guidelines for Python code.
- Use type hints for function signatures and class definitions.
- Annotate all functions and classes with type hints.
- Write docstrings for all functions and classes, following the Google style guide.
