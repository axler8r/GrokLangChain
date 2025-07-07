# CHANGELOG


## v0.7.0
**2025-07-07**

### Breaking Changes
- **Project Architecture**: Split monolithic web UI into modular architecture
  - Restructured web interface into separate components and pages
  - Separated UI logic from core application functionality
  - Updated component dependencies and interaction patterns
- **Data Schema**: Implement content-based schema with centralized data
    management and optimized processing
  - Consolidated data schemas into centralized schema module
  - Migrated from UUID-based to content-based chunk identification
  - Optimized data processing pipeline for better performance
  - Updated all components to use centralized schema definitions
- **Project Structure**: Restructure project for release
  - Reorganized BiblioTeq package layout for production deployment
  - Updated module organization and import paths
  - Prepared codebase for stable release distribution

### Added
- **Thumbnail Display**: Add thumbnail display to query sources
  - Enhanced query interface with visual document previews
  - Improved user experience with document identification
  - Integrated thumbnail generation and display capabilities
- **Content Processing**: Implement content-based checksums and optimize
    processing
  - Added content-based checksum validation for document integrity
  - Optimized processing pipeline for better performance
  - Enhanced data deduplication and validation mechanisms
- **Development Tools**: Add dead code inspection tool
  - Added tooling for identifying unused code segments
  - Enhanced code quality and maintenance capabilities
  - Improved development workflow with automated code analysis

### Changed
- **Code Organization**: Enhanced project structure and maintainability
  - Reorganized BiblioTeq package layout for better modularity
  - Consolidated data schemas into centralized schema module
  - Refactored semantic query layer to use centralized schemas
  - Updated document loader with proper dependencies and type safety
  - Updated query system with proper type safety and schema alignment
- **Documentation**: Updated project documentation and formatting
  - Updated documentation structure and content
  - Corrected copyright notices throughout codebase
  - Updated README file with current project information
  - Enhanced Makefile with improved command structure
- **Code Quality**: Improved code formatting and type safety
  - Formatted import statements throughout codebase
  - Added comprehensive type hints for better code safety
  - Updated import statements for consistency
  - Applied consistent code formatting standards
- **Testing Infrastructure**: Enhanced test coverage and integration
  - Updated test mockups for new architecture
  - Enhanced loader tests and integration test coverage
  - Updated tests to use new schema and content-based chunk IDs
  - Updated semantic query layer tests for new schema architecture
- **Build Configuration**: Updated deployment and containerization
  - Updated application path in Dockerfile for new structure
  - Enhanced Makefile with improved build targets
  - Updated location of style sheet for web interface

### Removed
- **Legacy Code**: Remove redundant and obsolete components
  - Removed redundant documentation files
  - Removed legacy UUID-to-MD5 conversion logic
  - Cleaned up obsolete code patterns and dependencies


## v0.1.0
**2025-06-29**

### Breaking Changes
- **Project Architecture**: Migrated from monorepo to monolith structure
  - Removed archivist component and enabled direct Qdrant access
  - Eliminated intermediary layer, allowing components to interact directly with
    vector database
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
