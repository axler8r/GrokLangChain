# BiblioTeq
BiblioTeq is to investigate how to build a RAG applicaiton.

It's a PDF document indexing and search application that leverages a vector
database, an imbedding database and an OpenAI's model to provide a summary of
information stored in the databases.

It allows you to upload, index, and semantically search through your PDF library
using natural language queries.

**Key Features:**
- **PDF Processing**: Extracts and indexes content from PDF documents
- **Vector Search**: Uses Qdrant vector database for semantic similarity search
- **AI-Powered**: Integrates with an OpenAI model for intelligent query understanding
- **Web Interface**: Streamlit-based web UI for easy document management
- **Composed Application**: Docker Compose architecture with MongoDB and Qdrant backends


## Initialize
BiblioTeq uses `uv` as its Python package manager for fast and reliable
dependency management. `uv` is a modern Python package installer and resolver
written in Rust that's significantly faster than pip.

You can install `uv` using the official installer:
```zsh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Once `uv` is installed, initialize and set up the project:
```zsh
# Clone the repository (if not already done)
git clone <repository-url>
cd BiblioTeq

# Install dependencies and set up the virtual environment
uv sync
```

This will create a virtual environment and install all required dependencies as
specified in `pyproject.toml`.


## Run
BiblioTeq is built as a Docker Compose application, which orchestrates multiple
services including the web frontend, MongoDB database, and Qdrant vector
database. Docker Compose allows you to define and run multi-container
applications with a single command, making deployment and development consistent
across different environments.

To start the application:
```zsh
make up
```

This command builds the Docker images (if needed), starts all services in the
background, and makes the application available at http://localhost:8501. The
services include:
- **Web Frontend**: Streamlit application (port 8501)
- **MongoDB**: Document metadata storage (port 27017)
- **Qdrant**: Vector database for semantic search (port 6333)

The `Makefile` serves as the primary interface for all project operations. It
provides convenient targets for common tasks:
- `make up` - Start the application
- `make down` - Stop the application  
- `make dev` - Run in development mode
- `make logs` - View application logs
- `make test` - Run unit tests
- `make build` - Build Docker images

Use `make help` to see all available commands.


## Contribute
We welcome contributions to BiblioTeq! Whether you're fixing bugs, adding
features, or improving documentation, your help is appreciated. Please start by
reading the existing code and documentation to understand the project structure.
Make sure to run the test suite (`make test`) and follow the coding standards
(use `make format` and `make check` to ensure code quality). Submit pull
requests with clear descriptions of your changes and include tests for new
functionality.


## License
BiblioTeq is released under the MIT License, which allows for both personal and
commercial use with minimal restrictions. See the [LICENSE](LICENSE) file for
the complete license terms.


## Documentation
Additional project documentation can be found in the
[`documentation/`](documentation/) directory, which includes architectural
diagrams, design decisions, and learning notes from the development process. For
API documentation and code examples, refer to the docstrings in the source code
and the test files in the [`test/`](test/) directory.
