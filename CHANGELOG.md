# CHANGELOG

## v0.1.0
**2025-06-29**

### Breaking Changes

- **Project Architecture**: Migrated from monorepo to monolith structure
  - Removed archivist component and enabled direct Qdrant access
  - Eliminated intermediary layer, allowing components to interact directly with vector database
  - Updated service dependencies and connection patterns

- **Dependency Management**: Switched from Poetry to `uv` package management
  - Removed Poetry-managed `pyproject.toml` and `poetry.lock` files
  - Removed `requirements.txt` files
  - Initialized new `uv` managed virtual environment
  - Updated Docker builds to use `uv` for faster dependency management

- **Module Restructuring**: Reorganized directory layout and module structure
  - Moved tests from `application/*/test/` to top-level `test/*/` directory
  - Restructured loader module with source/test separation
  - Updated import paths and package structure throughout codebase

### Added

- **Web Frontend**: Streamlit-based web interface (`app.py`)
  - Material Design-inspired CSS styling
  - Document upload interface with progress tracking
  - Natural language query interface with source attribution
  - Async query processing with proper error handling

- **Core Components**: Complete PDF processing and retrieval system
  - `Loader` class for PDF processing, chunking, and embedding generation
  - `Retriever` class for semantic search and document retrieval
  - `SemanticQueryLayer` for natural language query processing
  - `Configuration` management system

- **PDF Processing Pipeline**: Comprehensive document processing capabilities
  - Smart text chunking (512 tokens with 64-token overlap using tiktoken)
  - OpenAI embeddings integration with Ada-002 model
  - Dual storage: MongoDB for text chunks, Qdrant for vector embeddings
  - Batch processing capability for multiple PDF files

- **Testing Infrastructure**: Comprehensive test suite
  - pytest-based testing framework
  - Mock implementations for external dependencies
  - End-to-end workflow validation
  - Coverage reporting and analysis

- **Documentation**: Complete project documentation
  - Architecture documentation with mermaid diagrams
  - API documentation and usage examples
  - Development setup and configuration guides
  - Performance and scalability considerations

- **Development Tools**: Enhanced development workflow
  - VS Code workspace configuration and settings
  - GitHub Copilot integration and instructions
  - Makefile-driven command interface
  - Docker containerization with docker-compose setup

### Changed

- **Class Naming**: Renamed `PDFProcessor` to `Loader` for consistency
  - Updated file paths: `pdf_processor.py` → `loader.py`
  - Updated test files: `test_pdf_processor.py` → `test_loader.py`
  - Applied project naming conventions throughout codebase

- **Dependency Updates**: Migrated from deprecated libraries
  - Replaced PyPDF2 with pypdf for PDF processing
  - Updated API usage and import statements
  - Maintained backward compatibility while resolving deprecation warnings

- **Project Structure**: Reorganized directory layout
  - Centralized test organization under top-level `test/` directory
  - Updated VS Code settings for new directory structure
  - Improved Python path setup and module importing

- **Configuration Management**: Enhanced environment setup
  - Added `.env.example` files for configuration templates
  - Updated Docker configuration and environment variables
  - Improved database connection management

### Fixed

- **Build Configuration**: Resolved Docker and build issues
  - Fixed Dockerfile path references from `source/main.py` to `main.py`
  - Updated pip install command from `--requirements` to `--requirement`
  - Corrected run_loader.sh script paths

- **Test Configuration**: Resolved testing and dependency issues
  - Added `.PHONY` declaration to Makefile to prevent 'up to date' errors
  - Fixed test target to run pytest on correct directories
  - Added OPENAI_API_KEY environment variable for test execution
  - Updated coverage settings and dependency installation

- **Import Issues**: Corrected module imports and paths
  - Fixed import paths in test files for new directory structure
  - Added proper Python path setup for importing application modules
  - Corrected test PDF file paths and relative imports

- **Code Quality**: Improved formatting and type safety
  - Added type hints throughout codebase
  - Fixed code formatting and import organization
  - Enhanced error handling and exception management

### Infrastructure

- **Docker Services**: Complete containerization setup
  - MongoDB service configuration
  - Qdrant vector database integration
  - Automated weekly PDF processing service with cron scheduling
  - Multi-stage Docker builds with Python 3.12 slim base

- **Database Integration**: Dual storage architecture
  - MongoDB for document chunks and metadata
  - Qdrant for vector embeddings and similarity search
  - Connection pooling and resource management

- **Automated Processing**: Scheduled document processing
  - Weekly automated PDF processing (Sundays at 2 AM)
  - Configurable PDF path processing with environment variables
  - Comprehensive logging and monitoring capabilities
