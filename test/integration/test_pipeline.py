"""Integration tests for BiblioTeq loader and retriever pipeline.

This module tests the complete pipeline using a known test document (GNU Parallel manual)
to ensure the loader can process PDFs and the retriever can find relevant content.
"""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from pymongo import MongoClient
from qdrant_client import QdrantClient

from biblioteq.loader import Loader
from biblioteq.retriever import Retriever, RetrievalResult


class TestLoaderRetrieverIntegration:
    """Integration tests for the complete BiblioTeq pipeline."""

    @pytest.fixture(scope="class")
    def test_pdf_path(self) -> Path:
        """Path to the test PDF file.

        Returns:
            Path to the GNU Parallel manual PDF for testing
        """
        return Path(__file__).parent.parent / "data" / "gnu-parallel-manual.pdf"

    @pytest.fixture(scope="class")
    def test_env_file(self) -> Generator[str, None, None]:
        """Create a temporary .env file for testing with test database names.

        Yields:
            Path to temporary .env file with test configuration
        """
        # Get the real OpenAI API key from environment
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if not openai_key:
            pytest.skip("OPENAI_API_KEY environment variable is required for integration tests")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(f"""# Test MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB=biblioteq_test
MONGO_COLLECTION=chunks_test

# Test Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=embeddings_test

# OpenAI Configuration (use real key for integration tests)
OPENAI_API_KEY={openai_key}
""")

        yield f.name

        # Cleanup
        os.unlink(f.name)

    @pytest.fixture(scope="class")
    def loader(self, test_env_file: str) -> Loader:
        """Create a Loader instance for testing.

        Args:
            test_env_file: Path to test environment file

        Returns:
            Configured Loader instance
        """
        return Loader(env_file=test_env_file)

    @pytest.fixture(scope="class")
    def retriever(self, test_env_file: str) -> Retriever:
        """Create a Retriever instance for testing.

        Args:
            test_env_file: Path to test environment file

        Returns:
            Configured Retriever instance
        """
        return Retriever(env_file=test_env_file, max_results=10, min_similarity_threshold=0.1)

    @pytest.fixture(scope="class", autouse=True)
    def setup_and_cleanup_databases(self, test_env_file: str):
        """Setup and cleanup test databases before and after test class.

        Args:
            test_env_file: Path to test environment file
        """
        # Setup: Clean test databases before tests
        mongo_client = MongoClient("mongodb://localhost:27017")
        qdrant_client = QdrantClient(host="localhost", port=6333)

        # Drop test collections if they exist
        mongo_client.drop_database("biblioteq_test")
        try:
            qdrant_client.delete_collection("embeddings_test")
        except Exception:
            pass  # Collection might not exist

        yield

        # Cleanup: Clean test databases after tests
        mongo_client.drop_database("biblioteq_test")
        try:
            qdrant_client.delete_collection("embeddings_test")
        except Exception:
            pass

        mongo_client.close()

    def test_pdf_file_exists(self, test_pdf_path: Path) -> None:
        """Test that the test PDF file exists and is readable."""
        assert test_pdf_path.exists(), f"Test PDF not found at {test_pdf_path}"
        assert test_pdf_path.is_file(), f"Test PDF path is not a file: {test_pdf_path}"
        assert test_pdf_path.stat().st_size > 0, "Test PDF file is empty"

    def test_loader_can_process_pdf(self, loader: Loader, test_pdf_path: Path) -> None:
        """Test that the loader can successfully process the test PDF."""
        chunk_count = loader.process_pdf_file(test_pdf_path)

        assert chunk_count > 0, "Loader should have created at least one chunk"
        assert chunk_count > 10, "GNU Parallel manual should create many chunks"

        print(f"Loader processed {chunk_count} chunks from GNU Parallel manual")

    def test_loader_stores_data_in_mongodb(self, loader: Loader) -> None:
        """Test that the loader stored chunk data in MongoDB."""
        collection = loader.mongo_collection

        # Check that documents were inserted
        total_docs = collection.count_documents({})
        assert total_docs > 0, "No documents found in MongoDB"

        # Check structure of a sample document
        sample_doc = collection.find_one()
        assert sample_doc is not None
        assert "_id" in sample_doc
        assert "source_file" in sample_doc
        assert "chunk_index" in sample_doc
        assert "text" in sample_doc
        assert "token_count" in sample_doc

        # Verify it contains our test file
        assert str(sample_doc["source_file"]).endswith("gnu-parallel-manual.pdf")

        print(f"MongoDB contains {total_docs} chunks")

    def test_loader_stores_vectors_in_qdrant(self, loader: Loader) -> None:
        """Test that the loader stored vector embeddings in Qdrant."""
        collection_info = loader.qdrant_client.get_collection(loader.qdrant_collection)

        assert collection_info.points_count > 0, "No vectors found in Qdrant"  # type: ignore

        # Test that we can retrieve a point with vectors
        points = loader.qdrant_client.scroll(
            collection_name=loader.qdrant_collection,
            limit=1,
            with_vectors=True,  # Include vector data
        )[0]

        assert len(points) > 0, "Could not retrieve any points from Qdrant"

        # Check point structure
        point = points[0]
        assert point.id is not None
        assert point.vector is not None, f"Point vector is None: {point}"
        assert len(point.vector) == 1536, "Expected Ada-002 embedding dimension"
        assert point.payload is not None
        assert "source_file" in point.payload

        print(f"Qdrant contains {collection_info.points_count} vectors")
        print(f"Sample vector dimension: {len(point.vector)}")

    def test_retriever_can_search_gnu_parallel_content(self, retriever: Retriever) -> None:
        """Test that the retriever can find GNU Parallel specific content."""
        # Debug: Check if retriever is using the correct collection
        print(f"Retriever collection: {retriever.qdrant_collection}")

        # Debug: Check collection info
        try:
            collection_info = retriever.qdrant_client.get_collection(retriever.qdrant_collection)
            print(f"Collection points count: {collection_info.points_count}")
        except Exception as e:
            print(f"Error getting collection info: {e}")

        # Test search for core GNU Parallel concepts
        query = "parallel processing shell commands"
        print(f"Searching for: '{query}'")

        # Try with very low threshold first
        results = retriever.search(query, min_similarity_threshold=0.0, max_results=10)
        print(f"Results with threshold 0.0: {len(results)}")

        if len(results) == 0:
            # Try an even simpler search
            simple_results = retriever.search("GNU", min_similarity_threshold=0.0, max_results=5)
            print(f"Simple 'GNU' search results: {len(simple_results)}")

            if len(simple_results) == 0:
                # Debug: List available collections
                collections = retriever.qdrant_client.get_collections()
                print(f"Available Qdrant collections: {[c.name for c in collections.collections]}")

        assert len(results) > 0, "Should find results for parallel processing"

        # Check result structure
        result = results[0]
        assert isinstance(result, RetrievalResult)
        assert isinstance(result.text, str)
        assert len(result.text) > 0
        assert isinstance(result.similarity_score, float)
        assert 0.0 <= result.similarity_score <= 1.0
        assert result.source_file.endswith("gnu-parallel-manual.pdf")

        print(f"Found {len(results)} results for 'parallel processing shell commands'")
        print(f"Top result similarity: {result.similarity_score:.3f}")

    def test_retriever_search_for_specific_commands(self, retriever: Retriever) -> None:
        """Test searches for specific GNU Parallel commands and concepts."""
        test_queries = [
            "parallel command line",
            "job slots",
            "input sources",
            "GNU parallel",
            "shell script",
        ]

        for query in test_queries:
            results = retriever.search(query, max_results=5)
            assert isinstance(results, list), f"Results should be a list for query: {query}"

            if len(results) > 0:
                # Verify results are ordered by similarity
                for i in range(len(results) - 1):
                    assert results[i].similarity_score >= results[i + 1].similarity_score, (
                        "Results should be ordered by similarity score"
                    )

                # Check that results contain the query terms (case insensitive)
                found_relevant = any(
                    any(term.lower() in result.text.lower() for term in query.split())
                    for result in results[:3]  # Check top 3 results
                )

                print(
                    f"Query '{query}': {len(results)} results, "
                    f"top score: {results[0].similarity_score:.3f}, "
                    f"relevant: {found_relevant}"
                )

    def test_retriever_similarity_threshold_filtering(self, retriever: Retriever) -> None:
        """Test that similarity threshold filtering works correctly."""
        query = "parallel"

        # Search with low threshold
        results_low = retriever.search(query, min_similarity_threshold=0.1)

        # Search with high threshold
        results_high = retriever.search(query, min_similarity_threshold=0.7)

        # High threshold should return fewer or equal results
        assert len(results_high) <= len(results_low), "Higher threshold should return fewer results"

        # All high threshold results should have high similarity
        for result in results_high:
            assert result.similarity_score >= 0.7, (
                f"Result similarity {result.similarity_score} below threshold 0.7"
            )

        print(f"Low threshold (0.1): {len(results_low)} results")
        print(f"High threshold (0.7): {len(results_high)} results")

    def test_retriever_max_results_limiting(self, retriever: Retriever) -> None:
        """Test that max_results parameter limits the number of results."""
        query = "GNU"

        # Search with different limits
        results_small = retriever.search(query, max_results=3)
        results_large = retriever.search(query, max_results=10)

        assert len(results_small) <= 3, "Should respect max_results=3"
        assert len(results_large) <= 10, "Should respect max_results=10"

        if len(results_large) >= 3:
            # If we have enough results, small should be exactly 3
            assert len(results_small) == 3, "Should return exactly 3 results when available"

            # First 3 results should be the same (highest similarity)
            for i in range(3):
                assert results_small[i].chunk_id == results_large[i].chunk_id, (
                    "Top results should be the same regardless of limit"
                )

    def test_retriever_empty_and_invalid_queries(self, retriever: Retriever) -> None:
        """Test retriever behavior with edge case queries."""
        # Empty query
        empty_results = retriever.search("")
        assert isinstance(empty_results, list), "Should return list for empty query"

        # Very unlikely to match query
        unlikely_results = retriever.search(
            "quantum mechanics biochemistry astrophysics", min_similarity_threshold=0.8
        )
        assert isinstance(unlikely_results, list), "Should return list for unlikely query"
        # May be empty or have very low similarity results

        print(f"Empty query results: {len(empty_results)}")
        print(f"Unlikely query results: {len(unlikely_results)}")

    def test_end_to_end_pipeline_integrity(
        self, loader: Loader, retriever: Retriever, test_pdf_path: Path
    ) -> None:
        """Test the complete end-to-end pipeline integrity."""
        # Get the total number of chunks created by loader
        mongo_count = loader.mongo_collection.count_documents({})
        qdrant_info = loader.qdrant_client.get_collection(loader.qdrant_collection)
        qdrant_count = qdrant_info.points_count

        # MongoDB and Qdrant should have the same number of items
        assert mongo_count == qdrant_count, (
            f"Mismatch: MongoDB has {mongo_count} chunks, Qdrant has {qdrant_count} vectors"
        )

        # Verify we can retrieve content that should definitely exist
        results = retriever.search("GNU", max_results=5)
        assert len(results) > 0, "Should find results for 'GNU' in GNU Parallel manual"

        # Verify the retrieved chunks can be found in MongoDB
        for result in results:
            mongo_doc = loader.mongo_collection.find_one({"_id": result.chunk_id})
            assert mongo_doc is not None, f"Chunk {result.chunk_id} not found in MongoDB"
            assert mongo_doc["text"] == result.text, "Text mismatch between retriever and MongoDB"
            assert mongo_doc["source_file"] == result.source_file, "Source file mismatch"
            assert mongo_doc["chunk_index"] == result.chunk_index, "Chunk index mismatch"

        print("✅ End-to-end pipeline integrity verified:")
        print(f"   - {mongo_count} chunks in MongoDB")
        print(f"   - {qdrant_count} vectors in Qdrant")
        print(f"   - Retrieved {len(results)} results successfully")
        print("   - All data consistency checks passed")

    def test_cleanup_connections(self, loader: Loader, retriever: Retriever) -> None:
        """Test that connections can be properly closed."""
        # This should not raise exceptions
        loader.close_connections()
        retriever.close_connections()
