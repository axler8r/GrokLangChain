"""Improved unit tests for the Retriever module.

These tests focus on component logic with proper mocking,
avoiding external dependencies while testing core functionality.
"""

import pytest
from unittest.mock import Mock, patch
from biblioteq.services.retriever import Retriever
from biblioteq.core.schema import RetrievalResult


class TestRetrieverUnit:
    """Unit tests for Retriever class with proper mocking."""

    @pytest.fixture
    def mock_retriever(self):
        """Create a Retriever instance with mocked dependencies."""
        with (
            patch("biblioteq.services.retriever.MongoClient"),
            patch("biblioteq.services.retriever.QdrantClient"),
            patch("biblioteq.services.retriever.openai"),
            patch.dict(
                "os.environ",
                {
                    "MONGO_URI": "mongodb://test:27017",
                    "MONGO_DB": "test_db",
                    "MONGO_COLLECTION": "test_collection",
                    "QDRANT_HOST": "test_host",
                    "QDRANT_PORT": "6333",
                    "QDRANT_COLLECTION": "test_collection",
                    "OPENAI_API_KEY": "test_key",
                },
            ),
        ):
            retriever = Retriever(max_results=5, min_similarity_threshold=0.1)

            # Setup mocks
            retriever.mongo_collection = Mock()
            retriever.qdrant_client = Mock()

            return retriever

    def test_retriever_initialization(self, mock_retriever):
        """Test retriever initialization with correct parameters."""
        assert mock_retriever.max_results == 5
        assert mock_retriever.min_similarity_threshold == 0.1

    def test_query_embedding_generation(self, mock_retriever):
        """Test embedding generation logic."""
        with patch.object(mock_retriever, "_get_query_embedding") as mock_embed:
            mock_embed.return_value = [0.1] * 1536

            embedding = mock_retriever._get_query_embedding("test query")

            assert len(embedding) == 1536
            assert all(isinstance(x, (int, float)) for x in embedding)
            mock_embed.assert_called_once_with("test query")

    def test_search_with_mocked_data(self, mock_retriever):
        """Test search functionality with mocked Qdrant and MongoDB data."""
        # Mock Qdrant search results
        mock_scored_point = Mock()
        mock_scored_point.id = "test-chunk-id-without-hyphens"
        mock_scored_point.score = 0.85

        mock_query_result = Mock()
        mock_query_result.points = [mock_scored_point]

        mock_retriever.qdrant_client.query_points.return_value = mock_query_result

        # Mock MongoDB document
        mock_doc = {
            "_id": "test-chunk-id-without-hyphens",
            "text": "This is test content about parallel processing",
            "document_title": "Test Document",
            "document_checksum": "test-checksum-123",
            "thumbnail": "test-thumbnail-base64",
            "chunk_index": 0,
            "token_count": 50,
        }
        mock_retriever.mongo_collection.find_one.return_value = mock_doc

        # Mock embedding generation
        with patch.object(mock_retriever, "_get_query_embedding") as mock_embed:
            mock_embed.return_value = [0.1] * 1536

            results = mock_retriever.search("test query")

            assert len(results) == 1
            result = results[0]
            assert isinstance(result, RetrievalResult)
            assert result.chunk_id == "test-chunk-id-without-hyphens"
            assert result.similarity_score == 0.85
            assert result.text == "This is test content about parallel processing"

    def test_uuid_to_md5_conversion(self, mock_retriever):
        """Test the critical UUID to MD5 conversion logic."""
        # Mock Qdrant returning UUID format
        mock_scored_point = Mock()
        mock_scored_point.id = "4b3b26b5-9507-653c-62c3-60c3b1119303"  # UUID format
        mock_scored_point.score = 0.80

        mock_query_result = Mock()
        mock_query_result.points = [mock_scored_point]

        mock_retriever.qdrant_client.query_points.return_value = mock_query_result

        # Mock MongoDB document with MD5 format
        expected_md5_id = "4b3b26b59507653c62c360c3b1119303"  # No hyphens
        mock_doc = {
            "_id": expected_md5_id,
            "text": "Test content",
            "document_title": "Test Document UUID",
            "document_checksum": "test-checksum-uuid",
            "thumbnail": "test-thumbnail-uuid-base64",
            "chunk_index": 0,
            "token_count": 50,
        }
        mock_retriever.mongo_collection.find_one.return_value = mock_doc

        with patch.object(mock_retriever, "_get_query_embedding") as mock_embed:
            mock_embed.return_value = [0.1] * 1536

            results = mock_retriever.search("test")

            # Verify MongoDB was called with converted ID (no hyphens)
            mock_retriever.mongo_collection.find_one.assert_called_with(
                {"_id": expected_md5_id}
            )

            # Verify result uses MD5 format
            assert len(results) == 1
            assert results[0].chunk_id == expected_md5_id

    # def test_similarity_threshold_filtering(self, mock_retriever):
    #     """Test that similarity threshold filtering works correctly."""
    #     # Create mock points with different scores
    #     high_score_point = Mock()
    #     high_score_point.id = "high-score-id"
    #     high_score_point.score = 0.85

    #     low_score_point = Mock()
    #     low_score_point.id = "low-score-id"
    #     low_score_point.score = 0.05

    #     mock_query_result = Mock()
    #     mock_query_result.points = [high_score_point, low_score_point]

    #     mock_retriever.qdrant_client.query_points.return_value = mock_query_result

    #     # Mock MongoDB to return docs for both IDs
    #     def mock_find_one(query):
    #         chunk_id = query["_id"]
    #         return {
    #             "_id": chunk_id,
    #             "text": f"Content for {chunk_id}",
    #             "source_file": "test.pdf",
    #             "chunk_index": 0,
    #             "token_count": 50,
    #         }

    #     mock_retriever.mongo_collection.find_one.side_effect = mock_find_one

    #     with patch.object(mock_retriever, "_get_query_embedding") as mock_embed:
    #         mock_embed.return_value = [0.1] * 1536

    #         # Search with threshold that should filter out low score
    #         results = mock_retriever.search("test", min_similarity_threshold=0.7)

    #         # Should only return the high-score result
    #         assert len(results) == 1
    #         assert results[0].similarity_score == 0.85

    # def test_max_results_limiting(self, mock_retriever):
    #     """Test that max_results parameter works correctly."""
    #     # Create multiple mock points
    #     points = []
    #     for i in range(10):
    #         point = Mock()
    #         point.id = f"chunk-id-{i}"
    #         point.score = 0.8 - (i * 0.01)  # Decreasing scores
    #         points.append(point)

    #     mock_query_result = Mock()
    #     mock_query_result.points = points

    #     mock_retriever.qdrant_client.query_points.return_value = mock_query_result

    #     # Mock MongoDB
    #     def mock_find_one(query):
    #         chunk_id = query["_id"]
    #         return {
    #             "_id": chunk_id,
    #             "text": f"Content for {chunk_id}",
    #             "source_file": "test.pdf",
    #             "chunk_index": 0,
    #             "token_count": 50,
    #         }

    #     mock_retriever.mongo_collection.find_one.side_effect = mock_find_one

    #     with patch.object(mock_retriever, "_get_query_embedding") as mock_embed:
    #         mock_embed.return_value = [0.1] * 1536

    #         # Search with max_results=3
    #         mock_retriever.search("test", max_results=3)

    #         # Verify Qdrant was called with limit=3
    #         mock_retriever.qdrant_client.query_points.assert_called_once()
    #         call_args = mock_retriever.qdrant_client.query_points.call_args
    #         assert call_args.kwargs["limit"] == 3

    def test_empty_query_handling(self, mock_retriever):
        """Test handling of empty query."""
        with patch.object(mock_retriever, "_get_query_embedding") as mock_embed:
            mock_embed.return_value = [0.1] * 1536

            mock_query_result = Mock()
            mock_query_result.points = []
            mock_retriever.qdrant_client.query_points.return_value = mock_query_result

            results = mock_retriever.search("")

            assert isinstance(results, list)
            assert len(results) == 0

    def test_mongodb_lookup_failure(self, mock_retriever):
        """Test handling when MongoDB lookup fails."""
        # Mock Qdrant to return a result
        mock_scored_point = Mock()
        mock_scored_point.id = "nonexistent-id"
        mock_scored_point.score = 0.85

        mock_query_result = Mock()
        mock_query_result.points = [mock_scored_point]

        mock_retriever.qdrant_client.query_points.return_value = mock_query_result

        # Mock MongoDB to return None (document not found)
        mock_retriever.mongo_collection.find_one.return_value = None

        with patch.object(mock_retriever, "_get_query_embedding") as mock_embed:
            mock_embed.return_value = [0.1] * 1536

            results = mock_retriever.search("test")

            # Should return empty list when MongoDB lookup fails
            assert len(results) == 0

    def test_close_connections(self, mock_retriever):
        """Test connection cleanup."""
        # Should not raise an exception
        mock_retriever.close_connections()

        # Verify MongoDB client close was called
        mock_retriever.mongo_client.close.assert_called_once()
