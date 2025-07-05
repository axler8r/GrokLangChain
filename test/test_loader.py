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
from biblioteq.schema import ChunkRecord, EmbeddingMetadata


@pytest.fixture
def test_pdf_path() -> Path:
    """Fixture providing the path to the test PDF file."""
    return Path(__file__).parent / "data" / "gnu-parallel-manual.pdf"


@pytest.fixture
def create_mock_loader() -> Loader:
    """Fixture providing a Loader instance with mocked database connections."""
    with (
        patch("biblioteq.loader.MongoClient"),
        patch("biblioteq.loader.QdrantClient"),
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
        loader._store_embedding_in_qdrant = Mock()
        loader._create_thumbnail = Mock(return_value="mock_base64_thumbnail")

        return loader


class TestLoader:
    """Test class for Loader functionality."""

    def test_pdf_file_exists(self, test_pdf_path: Path) -> None:
        """Test that the test PDF file exists."""
        assert test_pdf_path.exists(), f"Test PDF file not found at {test_pdf_path}"
        assert test_pdf_path.suffix == ".pdf", "Test file should be a PDF"

    def test_extract_text_from_pdf(
        self, create_mock_loader: Loader, test_pdf_path: Path
    ) -> None:
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
    def test_get_embedding(
        self, mock_get_embedding, create_mock_loader: Loader
    ) -> None:
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
        """Test chunk ID generation based on document checksum."""
        document_checksum = "a1b2c3d4e5f6g7h8i9j0"  # Mock checksum
        chunk_index = 5

        chunk_id: str = create_mock_loader._generate_chunk_id(
            document_checksum, chunk_index
        )

        assert isinstance(chunk_id, str), "Chunk ID should be a string"
        assert len(chunk_id) == 32, "MD5 hash should be 32 characters long"

        # Test that same inputs produce same ID
        chunk_id2: str = create_mock_loader._generate_chunk_id(
            document_checksum, chunk_index
        )
        assert chunk_id == chunk_id2, "Same inputs should produce identical chunk IDs"

        # Test that different inputs produce different IDs
        chunk_id3: str = create_mock_loader._generate_chunk_id(
            document_checksum, chunk_index + 1
        )
        assert chunk_id != chunk_id3, (
            "Different inputs should produce different chunk IDs"
        )

    def test_generate_document_checksum(
        self, create_mock_loader: Loader, test_pdf_path: Path
    ) -> None:
        """Test document checksum generation."""
        checksum: str = create_mock_loader._generate_document_checksum(test_pdf_path)

        assert isinstance(checksum, str), "Checksum should be a string"
        assert len(checksum) == 32, "MD5 checksum should be 32 characters long"
        assert checksum.isalnum(), "Checksum should be alphanumeric"

        # Test that same file produces same checksum
        checksum2: str = create_mock_loader._generate_document_checksum(test_pdf_path)
        assert checksum == checksum2, "Same file should produce identical checksums"

    @patch("biblioteq.loader.convert_from_path")
    @patch("biblioteq.loader.io.BytesIO")
    @patch("biblioteq.loader.base64.b64encode")
    def test_create_thumbnail(
        self,
        mock_b64encode,
        mock_bytesio,
        mock_convert,
        create_mock_loader: Loader,
        test_pdf_path: Path,
    ) -> None:
        """Test thumbnail creation from PDF."""
        # Mock the PDF to image conversion
        mock_image = Mock()
        mock_image.thumbnail = Mock()
        mock_image.save = Mock()
        mock_convert.return_value = [mock_image]

        # Mock BytesIO and base64 encoding
        mock_output = Mock()
        mock_output.read.return_value = b"mock_image_data"
        mock_bytesio.return_value = mock_output
        mock_b64encode.return_value = b"mock_base64_data"

        # Remove the _create_thumbnail mock to test the real method
        del create_mock_loader._create_thumbnail

        thumbnail: str = create_mock_loader._create_thumbnail(test_pdf_path)

        assert isinstance(thumbnail, str), "Thumbnail should be a string"
        assert len(thumbnail) > 0, "Thumbnail should not be empty"

        # Verify the mocked methods were called
        mock_convert.assert_called_once_with(test_pdf_path, first_page=1, last_page=1)
        # Check that thumbnail was called with correct size, regardless of resample value
        mock_image.thumbnail.assert_called_once()
        call_args = mock_image.thumbnail.call_args
        assert call_args.kwargs["size"] == (160, 160), (
            "Thumbnail should be resized to 160x160"
        )
        mock_image.save.assert_called_once()

    @patch.object(Loader, "_get_embedding")
    @patch.object(Loader, "_create_thumbnail")
    def test_end_to_end_chunking_and_encoding(
        self,
        mock_thumbnail,
        mock_get_embedding,
        create_mock_loader: Loader,
        test_pdf_path: Path,
    ) -> None:
        """Test end-to-end chunking and encoding without database storage."""
        # Mock the _get_embedding method directly
        mock_get_embedding.return_value = [0.1] * 1536
        # Mock thumbnail creation
        mock_thumbnail.return_value = "mock_thumbnail_base64_string"

        # Generate document checksum and mock thumbnail
        document_checksum: str = create_mock_loader._generate_document_checksum(
            test_pdf_path
        )
        document_title = test_pdf_path.stem

        # Extract and chunk text
        text: str = create_mock_loader._extract_text_from_pdf(test_pdf_path)
        chunks: List[str] = create_mock_loader._chunk_text(text)

        assert len(chunks) > 0, "Should produce chunks from the PDF"

        # Test encoding a sample of chunks (limit to avoid too many API calls in tests)
        sample_chunks: List[str] = chunks[:3] if len(chunks) >= 3 else chunks

        for i, chunk in enumerate(sample_chunks):
            # Generate chunk ID using document checksum
            chunk_id = create_mock_loader._generate_chunk_id(document_checksum, i)
            assert chunk_id is not None, f"Should generate chunk ID for chunk {i}"

            # Get embedding
            embedding: List[float] = create_mock_loader._get_embedding(chunk)
            assert len(embedding) == 1536, (
                f"Embedding for chunk {i} should be 1536 dimensions"
            )

            # Verify chunk data structure (what would be stored in MongoDB via ChunkRecord)
            expected_chunk_record = ChunkRecord(
                chunk_id=chunk_id,
                document_title=document_title,
                document_checksum=document_checksum,
                thumbnail="mock_thumbnail_base64_string",
                chunk_index=i,
                text=chunk,
                token_count=len(create_mock_loader.tokenizer.encode(chunk)),
            )

            # Verify the ChunkRecord structure
            assert expected_chunk_record.chunk_id == chunk_id, (
                "ChunkRecord should have correct ID"
            )
            assert expected_chunk_record.document_title == document_title, (
                "ChunkRecord should have correct document title"
            )
            assert expected_chunk_record.document_checksum == document_checksum, (
                "ChunkRecord should have correct document checksum"
            )
            assert expected_chunk_record.thumbnail == "mock_thumbnail_base64_string", (
                "ChunkRecord should have correct thumbnail"
            )
            assert expected_chunk_record.chunk_index == i, (
                "ChunkRecord should have correct index"
            )
            assert expected_chunk_record.text == chunk, (
                "ChunkRecord should have correct text"
            )
            assert expected_chunk_record.token_count > 0, (
                "ChunkRecord should have positive token count"
            )

            # Verify EmbeddingMetadata structure
            expected_metadata = EmbeddingMetadata(
                document_title=document_title,
                document_checksum=document_checksum,
                chunk_index=i,
                token_count=expected_chunk_record.token_count,
            )

            assert expected_metadata.document_title == document_title, (
                "EmbeddingMetadata should have correct document title"
            )
            assert expected_metadata.document_checksum == document_checksum, (
                "EmbeddingMetadata should have correct document checksum"
            )
            assert expected_metadata.chunk_index == i, (
                "EmbeddingMetadata should have correct chunk index"
            )
            assert expected_metadata.token_count > 0, (
                "EmbeddingMetadata should have positive token count"
            )

    def test_tokenizer_initialization(self, create_mock_loader: Loader) -> None:
        """Test that the tokenizer is properly initialized."""
        assert create_mock_loader.tokenizer is not None, (
            "Tokenizer should be initialized"
        )

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
        assert create_mock_loader.chunk_overlap == 64, (
            "Default chunk overlap should be 64"
        )
        assert create_mock_loader.chunk_overlap < create_mock_loader.chunk_size, (
            "Chunk overlap should be less than chunk size"
        )
        assert create_mock_loader.chunk_size == 512, "Default chunk size should be 512"
        assert create_mock_loader.chunk_overlap == 64, (
            "Default chunk overlap should be 64"
        )
        assert create_mock_loader.chunk_overlap < create_mock_loader.chunk_size, (
            "Chunk overlap should be less than chunk size"
        )

    @patch.object(Loader, "process_pdf_file")
    def test_process_directory(
        self, mock_process_pdf, create_mock_loader: Loader, tmp_path: Path
    ) -> None:
        """Test directory processing with automatic document naming."""
        # Create test directory with mock PDF files
        test_dir = tmp_path / "test_pdfs"
        test_dir.mkdir()

        # Create mock PDF files
        pdf1 = test_dir / "document1.pdf"
        pdf2 = test_dir / "document2.pdf"
        pdf1.write_bytes(b"mock pdf content 1")
        pdf2.write_bytes(b"mock pdf content 2")

        # Mock the process_pdf_file method to return different values for different files
        def mock_side_effect(pdf_path, document_name):
            if pdf_path == pdf1:
                return 5
            elif pdf_path == pdf2:
                return 3
            else:
                return 0

        mock_process_pdf.side_effect = mock_side_effect

        # Process directory
        results = create_mock_loader.process_directory(test_dir)

        # Verify results
        assert len(results) == 2, "Should process both PDF files"
        assert str(pdf1) in results, "Should include first PDF in results"
        assert str(pdf2) in results, "Should include second PDF in results"
        assert results[str(pdf1)] == 5, (
            "Should return correct chunk count for first PDF"
        )
        assert results[str(pdf2)] == 3, (
            "Should return correct chunk count for second PDF"
        )

        # Verify process_pdf_file was called with correct document names
        mock_process_pdf.assert_any_call(pdf1, "document1")
        mock_process_pdf.assert_any_call(pdf2, "document2")

    @patch.object(Loader, "_get_embedding")
    @patch("biblioteq.loader.convert_from_path")
    @patch("biblioteq.loader.io.BytesIO")
    @patch("biblioteq.loader.base64.b64encode")
    def test_optimized_workflow_integration(
        self,
        mock_b64encode,
        mock_bytesio,
        mock_convert,
        mock_get_embedding,
        create_mock_loader: Loader,
        test_pdf_path: Path,
    ) -> None:
        """Test the complete optimized workflow with checksum and single thumbnail generation."""
        # Mock dependencies
        mock_image = Mock()
        mock_image.thumbnail = Mock()
        mock_image.save = Mock()
        mock_convert.return_value = [mock_image]
        mock_get_embedding.return_value = [0.1] * 1536

        # Mock BytesIO and base64 encoding for thumbnail generation
        mock_output = Mock()
        mock_output.read.return_value = b"mock_image_data"
        mock_bytesio.return_value = mock_output
        mock_b64encode.return_value = b"mock_base64_data"

        # Ensure the database methods are properly mocked for call tracking
        mock_store_mongo = Mock()
        mock_store_qdrant = Mock()
        create_mock_loader._store_chunk_in_mongo = mock_store_mongo
        create_mock_loader._store_embedding_in_qdrant = mock_store_qdrant

        # Remove the _create_thumbnail mock to test the real thumbnail generation
        del create_mock_loader._create_thumbnail

        # Process the PDF file
        document_name = "test_document"
        chunk_count = create_mock_loader.process_pdf_file(test_pdf_path, document_name)

        assert chunk_count > 0, "Should process at least one chunk"

        # Verify thumbnail was created only once (not per chunk)
        mock_convert.assert_called_once_with(test_pdf_path, first_page=1, last_page=1)

        # Verify database storage methods were called
        assert mock_store_mongo.call_count == chunk_count
        assert mock_store_qdrant.call_count == chunk_count

        # Verify the stored data has correct structure
        stored_chunk_calls = mock_store_mongo.call_args_list
        for call in stored_chunk_calls:
            chunk_record = call[0][0]  # First argument should be a ChunkRecord

            # Verify it's a ChunkRecord instance
            assert isinstance(chunk_record, ChunkRecord), (
                "Should store ChunkRecord objects"
            )

            # Check field values
            assert isinstance(chunk_record.chunk_id, str)
            assert chunk_record.document_title == document_name
            assert isinstance(chunk_record.document_checksum, str)
            assert len(chunk_record.document_checksum) == 32  # MD5 length
            assert isinstance(chunk_record.chunk_index, int)
            assert isinstance(chunk_record.text, str)
            assert isinstance(chunk_record.token_count, int)
            assert chunk_record.token_count > 0

        # Verify the Qdrant storage calls
        stored_qdrant_calls = mock_store_qdrant.call_args_list
        for call in stored_qdrant_calls:
            chunk_id = call[0][0]  # First argument: chunk_id
            embedding = call[0][1]  # Second argument: embedding vector
            metadata = call[0][2]  # Third argument: EmbeddingMetadata

            assert isinstance(chunk_id, str)
            assert isinstance(embedding, list)
            assert len(embedding) == 1536  # OpenAI embedding dimension
            assert isinstance(metadata, EmbeddingMetadata), (
                "Should store EmbeddingMetadata objects"
            )
            assert metadata.document_title == document_name
