# Project Overview
The project is called **BiblioTeq**.

The application will be deployed as a **Docker Compose** application.


## Functionality
The application will allow users to:
- Upload pdf files of books.
- The upload can be done through a web interface or a command line interface.
- Query the content of the books using natural language from a web interface.
- The application will use an agentic service to interpret user requests, pull
  data from a vector database, and generate responses based on user queries.


## Modules
- `ui`: The frontent.
  - `web`: A web application built with Streamlit.
  - `cli`: A command line interface for interacting with the application.
- `agent`: An agentic service that interprets user requests, pulls data
    from a vector database and generates responses based on user queries.
- `loader`: Chunks and encodes data from pdf files (my books) and stores
    it in a vector database and document database.
- `inspector`: A database inspection service for browsing and analyzing stored
    documents, chunks, and embeddings in MongoDB and Qdrant. *(To be implemented)*


## Libraries
These are the _proposed_ libraries to be used in the project:
- `streamlit`: For the user interface.
- `autogen`: For the agentic workflow that integrates the front end and data
    storage services.
- `loguru`: For logging.
- `python-dotenv`: To manage environment variables.
- `qdrant-client`: Used for interacting with the Qdrant vector database.
- `pymongo`: Used for interacting with MongoDB document database.
- `tiktoken`: Used for embedding and chunking data from pdf files.
- `pypdf`: Used for reading pdf files.
- `tiktoken`: For embedding and chunking data from pdf files.


## Tools
- `make` for build automation and task management.
- `pytest`: For testing.
- `ruff` for linting and code formatting.
- `uv` for dependency management and virtual environments.


## Project Structure
Here is a _proposed_ layout of project's structure:
``` plaintext
project-root/
  ├─ biblioteq/
  |    |- ui/
  |    |    |- web/
  |    |    |    └- app.py
  |    |    └- cli/
  |    |         └- app.py
  |    |- .env
  |    |- .env.example
  |    |- agent.py
  |    |- <other_files>
  |    |- loader.py
  |    └- main.py
  |- data/
  ├─ test/
  |    |- test_historian.py
  |    |- <other_test_files>>
  |    └- test_loader.py
  |- Dockerfile
  |- docker-compose.yml
  |- README.md
  └- Makefile
```
