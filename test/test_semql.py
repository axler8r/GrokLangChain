"""Unit tests for SemanticQueryLayer.

This module tests the SemanticQueryLayer's ability to retrieve data from
vector and chunk stores and format responses using the GNU Parallel manual data.
"""

import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymongo import MongoClient
from qdrant_client import QdrantClient

from biblioteq.retriever import Retriever
from biblioteq.semql import SemanticQueryLayer, QueryResponse


class TestSemanticQueryLayer:
    """Unit tests for SemanticQueryLayer functionality."""

    @pytest.fixture(scope="class")
    def test_env_file(self):
        """Use the existing .env file for testing."""
        env_file_path = Path(__file__).parent.parent.parent / "biblioteq" / ".env"

        if not env_file_path.exists():
            pytest.skip("biblioteq/.env file not found")

        # Check if OpenAI API key is available
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if not openai_key:
            # Try to read from .env file
            try:
                with open(env_file_path, "r") as f:
                    for line in f:
                        if line.startswith("OPENAI_API_KEY="):
                            openai_key = line.split("=", 1)[1].strip()
                            break
                if not openai_key:
                    pytest.skip("OPENAI_API_KEY not found in .env file")
            except Exception:
                pytest.skip("Could not read .env file")

        return str(env_file_path)

    @pytest.fixture(scope="class")
    def retriever(self, test_env_file: str) -> Retriever:
        """Create a Retriever instance for testing with localhost connections."""
        # Create a retriever with overridden connection settings for external testing
        retriever = Retriever(
            env_file=test_env_file, max_results=5, min_similarity_threshold=0.1
        )

        # Override the connection settings to use localhost instead of Docker hostnames
        retriever.qdrant_client = QdrantClient(host="localhost", port=6333)
        retriever.mongo_client = MongoClient("mongodb://localhost:27017")
        retriever.mongo_collection = retriever.mongo_client["bibioteq"]["chunks"]

        return retriever

    @pytest.fixture(scope="class", autouse=True)
    def ensure_test_data_exists(self, test_env_file: str):
        """Ensure production databases have data."""
        # Check if production databases have data
        mongo_client = MongoClient("mongodb://localhost:27017")
        db = mongo_client["bibioteq"]  # Note: using production DB name from .env
        collection = db["chunks"]

        chunk_count = collection.count_documents({})
        if chunk_count == 0:
            pytest.skip(
                "No data found in production MongoDB. Start Docker Compose and load data first."
            )

        qdrant_client = QdrantClient(host="localhost", port=6333)
        try:
            collection_info = qdrant_client.get_collection("embeddings")
            if collection_info.points_count == 0:
                pytest.skip(
                    "No vector data found in production Qdrant. Start Docker Compose and load data first."
                )
        except Exception:
            pytest.skip(
                "Qdrant collection not found. Start Docker Compose and load data first."
            )

        mongo_client.close()
        print(
            f"Production data available: {chunk_count} chunks, {collection_info.points_count} vectors"
        )

    @pytest.fixture
    def semql_with_real_retriever(self, retriever: Retriever) -> SemanticQueryLayer:
        """Create SemanticQueryLayer with real retriever service."""
        config = {
            "model_config": {
                "model": "gpt-4",
                "api_key": os.getenv("OPENAI_API_KEY", ""),
            }
        }
        return SemanticQueryLayer(retriever_service=retriever, config=config)

    @pytest.fixture
    def semql_with_mock_retriever(self) -> SemanticQueryLayer:
        """Create SemanticQueryLayer with mock retriever service."""
        mock_retriever = MagicMock()
        mock_retriever.search.return_value = [
            MagicMock(
                text="GNU parallel is a shell tool for executing jobs in parallel using one or more computers.",
                source_file="gnu-parallel-manual.pdf",
                chunk_index=1,
                similarity_score=0.95,
                chunk_id="test-chunk-1",
            ),
            MagicMock(
                text="The parallel command can read from multiple input sources and distribute work across available processors.",
                source_file="gnu-parallel-manual.pdf",
                chunk_index=2,
                similarity_score=0.87,
                chunk_id="test-chunk-2",
            ),
        ]

        config = {
            "model_config": {
                "model": "gpt-4",
                "api_key": "mock-api-key",
            }
        }
        return SemanticQueryLayer(retriever_service=mock_retriever, config=config)

    def test_semql_initialization(self, semql_with_real_retriever: SemanticQueryLayer):
        """Test that SemanticQueryLayer initializes correctly."""
        assert semql_with_real_retriever.retriever_service is not None
        assert semql_with_real_retriever.config is not None
        assert semql_with_real_retriever.model_config is not None
        assert semql_with_real_retriever.retrieval_tool is not None

        # Check tool is configured correctly
        tool = semql_with_real_retriever.retrieval_tool
        assert tool.name == "retrieve_documents"
        assert "knowledge base" in tool.description.lower()

    def test_retrieve_documents_tool_with_real_data(
        self, semql_with_real_retriever: SemanticQueryLayer
    ):
        """Test RetrieveDocumentsTool with real retriever service."""
        tool = semql_with_real_retriever.retrieval_tool

        async def run_test():
            from biblioteq.semql import RetrieveDocumentsInput
            from autogen_core import CancellationToken

            # Test with GNU Parallel related query
            input_data = RetrieveDocumentsInput(query="parallel shell commands")
            result = await tool.run(input_data, CancellationToken())

            assert isinstance(result.chunks, list)
            assert result.total_results >= 0

            if result.total_results > 0:
                # Check structure of returned chunks
                chunk = result.chunks[0]
                assert "content" in chunk
                assert "source" in chunk or "source_file" in chunk
                assert "score" in chunk or "similarity_score" in chunk

                # Should contain relevant content about GNU Parallel
                content = chunk["content"].lower()
                assert any(
                    term in content for term in ["parallel", "gnu", "shell", "command"]
                )

                print(
                    f"Retrieved {result.total_results} chunks for 'parallel shell commands'"
                )
                print(f"Sample content: {chunk['content'][:100]}...")

            return result

        result = asyncio.run(run_test())
        assert result is not None

    def test_retrieve_documents_tool_with_mock_data(
        self, semql_with_mock_retriever: SemanticQueryLayer
    ):
        """Test RetrieveDocumentsTool with mock retriever service."""
        tool = semql_with_mock_retriever.retrieval_tool

        async def run_test():
            from biblioteq.semql import RetrieveDocumentsInput
            from autogen_core import CancellationToken

            input_data = RetrieveDocumentsInput(query="GNU parallel")
            result = await tool.run(input_data, CancellationToken())

            assert isinstance(result.chunks, list)
            assert result.total_results == 2
            assert len(result.chunks) == 2

            # Check mock data structure
            chunk = result.chunks[0]
            assert "content" in chunk
            assert "GNU parallel" in chunk["content"]
            assert chunk["source"] == "gnu-parallel-manual.pdf"

            return result

        result = asyncio.run(run_test())
        assert result is not None

    def test_retrieve_documents_tool_no_retriever(self):
        """Test RetrieveDocumentsTool behavior with no retriever service."""
        semql = SemanticQueryLayer(retriever_service=None, config={})
        tool = semql.retrieval_tool

        async def run_test():
            from biblioteq.semql import RetrieveDocumentsInput
            from autogen_core import CancellationToken

            input_data = RetrieveDocumentsInput(query="test query")
            result = await tool.run(input_data, CancellationToken())

            assert isinstance(result.chunks, list)
            assert result.total_results == 0
            assert len(result.chunks) == 1
            assert "No retriever service available" in result.chunks[0]["content"]

            return result

        result = asyncio.run(run_test())
        assert result is not None

    def test_query_input_validation(
        self, semql_with_mock_retriever: SemanticQueryLayer
    ):
        """Test query input validation."""

        async def run_test():
            # Test empty query
            with pytest.raises(ValueError, match="Query cannot be empty"):
                await semql_with_mock_retriever.query("")

            # Test whitespace-only query
            with pytest.raises(ValueError, match="Query cannot be empty"):
                await semql_with_mock_retriever.query("   ")

            # Test valid query (should not raise)
            try:
                await semql_with_mock_retriever.query("valid query")
            except ValueError:
                pytest.fail("Valid query should not raise ValueError")
            except Exception:
                # Other exceptions are expected due to mock setup
                pass

        asyncio.run(run_test())

    @patch("biblioteq.semql.ChatCompletionClient")
    @patch("biblioteq.semql.AssistantAgent")
    def test_query_response_structure(
        self,
        mock_agent_class,
        mock_client_class,
        semql_with_mock_retriever: SemanticQueryLayer,
    ):
        """Test that query method returns properly structured QueryResponse."""
        # Mock the model client
        mock_client = AsyncMock()
        mock_client_class.load_component.return_value = mock_client

        # Mock the assistant agent
        mock_agent = AsyncMock()
        mock_response = AsyncMock()
        mock_response.chat_message = MagicMock()
        mock_response.chat_message.content = "GNU parallel is a powerful tool for executing jobs in parallel. Based on the retrieved documents, it can process shell commands across multiple processors and handle various input sources efficiently."

        mock_agent.on_messages.return_value = mock_response
        mock_agent_class.return_value = mock_agent

        async def run_test():
            result = await semql_with_mock_retriever.query("What is GNU parallel?")

            # Check QueryResponse structure
            assert isinstance(result, QueryResponse)
            assert isinstance(result.answer, str)
            assert isinstance(result.sources, list)
            assert isinstance(result.confidence, float)
            assert isinstance(result.metadata, dict)

            # Check content
            assert len(result.answer) > 0
            assert "GNU parallel" in result.answer
            assert result.confidence > 0
            assert result.metadata["status"] == "success"
            assert result.metadata["query"] == "What is GNU parallel?"

            return result

        result = asyncio.run(run_test())
        assert result is not None

    @patch("biblioteq.semql.ChatCompletionClient")
    def test_query_error_handling(
        self, mock_client_class, semql_with_mock_retriever: SemanticQueryLayer
    ):
        """Test query error handling when model client fails."""
        # Mock client to raise exception
        mock_client_class.load_component.side_effect = Exception("Model client error")

        async def run_test():
            result = await semql_with_mock_retriever.query("test query")

            # Should return error response, not raise exception
            assert isinstance(result, QueryResponse)
            assert result.confidence == 0.0
            assert result.metadata["status"] == "error"
            assert "error" in result.metadata
            assert "Model client error" in result.answer

            return result

        result = asyncio.run(run_test())
        assert result is not None

    def test_retriever_service_integration(self, retriever: Retriever):
        """Test that retriever service returns expected data structure."""
        # Test direct retriever functionality
        results = retriever.search("GNU parallel")

        assert isinstance(results, list)
        assert len(results) >= 0

        if len(results) > 0:
            result = results[0]

            # Check that result has expected attributes
            assert hasattr(result, "text")
            assert hasattr(result, "source_file")
            assert hasattr(result, "similarity_score")
            assert hasattr(result, "chunk_id")

            # Check data types
            assert isinstance(result.text, str)
            assert isinstance(result.source_file, str)
            assert isinstance(result.similarity_score, float)

            # Check content makes sense
            assert len(result.text) > 0
            assert result.source_file.endswith(".pdf")
            assert 0.0 <= result.similarity_score <= 1.0

            print(f"Direct retriever test: {len(results)} results")
            print(
                f"Top result: {result.text[:50]}... (score: {result.similarity_score:.3f})"
            )

    def test_retrieval_tool_data_formatting(
        self, semql_with_real_retriever: SemanticQueryLayer
    ):
        """Test that RetrieveDocumentsTool properly formats data from retriever."""
        tool = semql_with_real_retriever.retrieval_tool

        async def run_test():
            from biblioteq.semql import RetrieveDocumentsInput
            from autogen_core import CancellationToken

            input_data = RetrieveDocumentsInput(query="parallel jobs")
            result = await tool.run(input_data, CancellationToken())

            if result.total_results > 0:
                chunk = result.chunks[0]

                # Check required fields are present and formatted correctly
                assert "content" in chunk
                assert isinstance(chunk["content"], str)
                assert len(chunk["content"]) > 0

                # Source information
                source_key = "source" if "source" in chunk else "source_file"
                assert source_key in chunk
                assert chunk[source_key].endswith(".pdf")

                # Score information
                score_key = "score" if "score" in chunk else "similarity_score"
                assert score_key in chunk
                assert isinstance(chunk[score_key], float)
                assert 0.0 <= chunk[score_key] <= 1.0

                print(
                    f"Data formatting test passed: {result.total_results} chunks formatted correctly"
                )

            return result

        result = asyncio.run(run_test())
        assert result is not None

    def test_multiple_queries_different_topics(
        self, semql_with_real_retriever: SemanticQueryLayer
    ):
        """Test retrieval tool with multiple different queries."""
        tool = semql_with_real_retriever.retrieval_tool

        test_queries = [
            "parallel processing",
            "shell commands",
            "GNU software",
            "job execution",
            "input sources",
        ]

        async def run_test():
            from biblioteq.semql import RetrieveDocumentsInput
            from autogen_core import CancellationToken

            results = {}

            for query in test_queries:
                input_data = RetrieveDocumentsInput(query=query)
                result = await tool.run(input_data, CancellationToken())
                results[query] = result

                # Basic validation
                assert isinstance(result.chunks, list)
                assert isinstance(result.total_results, int)
                assert result.total_results >= 0

                if result.total_results > 0:
                    # Basic validation that we got results
                    print(f"Query '{query}': {result.total_results} results")

            return results

        results = asyncio.run(run_test())
        assert len(results) == len(test_queries)

    def teardown_method(self):
        """Clean up after each test method."""
        # Close any open connections
        pass
