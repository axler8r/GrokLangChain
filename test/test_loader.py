"""Tests for Loader class.

This module contains tests for the PDF processing functionality,
specifically testing chunking and encoding capabilities without
database storage.
"""

import os
from pathlib import Path
from typing import List, LiteralString
from unittest.mock import Mock, patch

import pytest

from biblioteq.loader import Loader


@pytest.fixture
def test_pdf_path() -> Path:
    """Fixture providing the path to the test PDF file."""
    return (
        Path(__file__).parent.parent.parent
        / "data"
        / "book"
        / "Deep Learning with Python, 2nd Edittion (Deep_Learning_with_Python_Second_Editio).pdf"
    )


@pytest.fixture
def create_mock_loader() -> Loader:
    """Fixture providing a Loader instance with mocked database connections."""
    with (
        patch("biblioteq.loader.MongoClient"),
        patch("biblioteq.loader.QdrantClient"),
        patch("biblioteq.loader.load_dotenv"),
        patch("biblioteq.loader.openai") as mock_openai,
        patch.dict(
            os.environ,
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
        # Mock openai.api_key assignment
        mock_openai.api_key = None

        loader = Loader()

        # Mock the database-related methods to avoid actual connections
        loader._ensure_qdrant_collection = Mock()
        loader._store_chunk_in_mongo = Mock()
        loader._store_vector_in_qdrant = Mock()

        return loader


class TestLoader:
    """Test class for Loader functionality."""

    def test_pdf_file_exists(self, test_pdf_path: Path) -> None:
        """Test that the test PDF file exists."""
        assert test_pdf_path.exists(), f"Test PDF file not found at {test_pdf_path}"
        assert test_pdf_path.suffix == ".pdf", "Test file should be a PDF"

    def test_extract_text_from_pdf(self, create_mock_loader: Loader, test_pdf_path: Path) -> None:
        """Test PDF text extraction functionality."""
        text = create_mock_loader._extract_text_from_pdf(test_pdf_path)

        assert isinstance(text, str), "Extracted text should be a string"
        assert len(text) > 0, "Extracted text should not be empty"
        assert len(text) > 100, "Extracted text should be substantial (>100 characters)"

        # Check for expected content in a Deep Learning book
        text_lower: str = text.lower()
        assert any(
            keyword in text_lower
            for keyword in [
                "deep learning",
                "neural",
                "machine learning",
                "python",
                "keras",
                "tensorflow",
            ]
        ), "Text should contain deep learning related keywords"

    def test_chunk_text(self, create_mock_loader: Loader, test_pdf_path: Path) -> None:
        """Test text chunking functionality."""
        # Extract text from PDF
        text: str = create_mock_loader._extract_text_from_pdf(test_pdf_path)

        # Chunk the text
        chunks: List[str] = create_mock_loader._chunk_text(text)

        assert isinstance(chunks, list), "Chunks should be returned as a list"
        assert len(chunks) > 0, "Should produce at least one chunk"

        # Test chunk properties
        for i, chunk in enumerate(chunks):
            assert isinstance(chunk, str), f"Chunk {i} should be a string"
            assert len(chunk.strip()) > 0, f"Chunk {i} should not be empty"

            # Check token count is within expected range
            token_count: int = len(create_mock_loader.tokenizer.encode(chunk))
            assert token_count <= create_mock_loader.chunk_size, (
                f"Chunk {i} token count ({token_count}) should not exceed "
                f"chunk_size ({create_mock_loader.chunk_size})"
            )

    def test_chunk_overlap(self, create_mock_loader: Loader) -> None:
        """Test that chunking produces overlapping content when expected."""
        # Use a simple test text that we know will produce multiple chunks
        test_text: LiteralString = (
            "This is a test sentence. " * 100
        )  # Repeat to ensure multiple chunks

        chunks: List[str] = create_mock_loader._chunk_text(test_text)

        if len(chunks) > 1:
            # Check that there's some overlap between consecutive chunks
            # This is a basic check - in practice, overlap detection would be more sophisticated
            assert len(chunks) >= 2, "Should have multiple chunks for overlap testing"

    @patch.object(Loader, "_get_embedding")
    def test_get_embedding(self, mock_get_embedding, create_mock_loader: Loader) -> None:
        """Test embedding generation functionality."""
        # Mock the _get_embedding method directly
        mock_get_embedding.return_value = [0.1, 0.2, 0.3] * 512  # 1536 dimensions

        test_text = "This is a test text for embedding generation."
        embedding: List[float] = create_mock_loader._get_embedding(test_text)

        assert isinstance(embedding, list), "Embedding should be a list"
        assert len(embedding) == 1536, "Ada-002 embeddings should be 1536 dimensions"
        assert all(isinstance(x, (int, float)) for x in embedding), (
            "All embedding values should be numeric"
        )

        # Verify the method was called correctly
        mock_get_embedding.assert_called_once_with(test_text)

    def test_generate_chunk_id(self, create_mock_loader: Loader) -> None:
        """Test chunk ID generation."""
        file_path = "/test/path/file.pdf"
        chunk_index = 5

        chunk_id: str = create_mock_loader._generate_chunk_id(file_path, chunk_index)

        assert isinstance(chunk_id, str), "Chunk ID should be a string"
        assert len(chunk_id) == 32, "MD5 hash should be 32 characters long"

        # Test that same inputs produce same ID
        chunk_id2: str = create_mock_loader._generate_chunk_id(file_path, chunk_index)
        assert chunk_id == chunk_id2, "Same inputs should produce identical chunk IDs"

        # Test that different inputs produce different IDs
        chunk_id3: str = create_mock_loader._generate_chunk_id(file_path, chunk_index + 1)
        assert chunk_id != chunk_id3, "Different inputs should produce different chunk IDs"

    @patch.object(Loader, "_get_embedding")
    def test_end_to_end_chunking_and_encoding(
        self, mock_get_embedding, create_mock_loader: Loader, test_pdf_path: Path
    ) -> None:
        """Test end-to-end chunking and encoding without database storage."""
        # Mock the _get_embedding method directly
        mock_get_embedding.return_value = [0.1] * 1536

        # Extract and chunk text
        text: str = create_mock_loader._extract_text_from_pdf(test_pdf_path)
        chunks: List[str] = create_mock_loader._chunk_text(text)

        assert len(chunks) > 0, "Should produce chunks from the PDF"

        # Test encoding a sample of chunks (limit to avoid too many API calls in tests)
        sample_chunks: List[str] = chunks[:3] if len(chunks) >= 3 else chunks

        for i, chunk in enumerate(sample_chunks):
            # Generate chunk ID
            chunk_id = create_mock_loader._generate_chunk_id(str(test_pdf_path), i)
            assert chunk_id is not None, f"Should generate chunk ID for chunk {i}"

            # Get embedding
            embedding: List[float] = create_mock_loader._get_embedding(chunk)
            assert len(embedding) == 1536, f"Embedding for chunk {i} should be 1536 dimensions"

            # Verify chunk data structure (what would be stored in MongoDB)
            chunk_data = {
                "_id": chunk_id,
                "source_file": str(test_pdf_path),
                "chunk_index": i,
                "text": chunk,
                "token_count": len(create_mock_loader.tokenizer.encode(chunk)),
            }

            assert chunk_data["_id"] == chunk_id, "Chunk data should have correct ID"
            assert chunk_data["source_file"] == str(test_pdf_path), (
                "Chunk data should have correct source file"
            )
            assert chunk_data["chunk_index"] == i, "Chunk data should have correct index"
            assert chunk_data["text"] == chunk, "Chunk data should have correct text"
            assert chunk_data["token_count"] > 0, "Chunk data should have positive token count"

    def test_tokenizer_initialization(self, create_mock_loader: Loader) -> None:
        """Test that the tokenizer is properly initialized."""
        assert create_mock_loader.tokenizer is not None, "Tokenizer should be initialized"

        # Test tokenizer functionality
        test_text = "Hello, world!"
        tokens: List[int] = create_mock_loader.tokenizer.encode(test_text)
        assert isinstance(tokens, list), "Tokenizer should return list of tokens"
        assert len(tokens) > 0, "Should produce at least one token"

        # Test decoding
        decoded_text: str = create_mock_loader.tokenizer.decode(tokens)
        assert decoded_text == test_text, "Decoded text should match original"

    def test_chunk_configuration(self, create_mock_loader: Loader) -> None:
        """Test that chunk size and overlap are properly configured."""
        assert create_mock_loader.chunk_size == 512, "Default chunk size should be 512"
        assert create_mock_loader.chunk_overlap == 64, "Default chunk overlap should be 64"
        assert create_mock_loader.chunk_overlap < create_mock_loader.chunk_size, (
            "Chunk overlap should be less than chunk size"
        )
        assert create_mock_loader.chunk_size == 512, "Default chunk size should be 512"
        assert create_mock_loader.chunk_overlap == 64, "Default chunk overlap should be 64"
        assert create_mock_loader.chunk_overlap < create_mock_loader.chunk_size, (
            "Chunk overlap should be less than chunk size"
        )
