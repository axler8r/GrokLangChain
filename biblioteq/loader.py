"""Loader module for BiblioQuiz application.

This module provides functionality to process PDF files by chunking them into
manageable pieces, storing the chunks in MongoDB, encoding them with OpenAI
embeddings, and storing the vector embeddings in Qdrant.
"""

import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import openai
import pypdf
import tiktoken
from dotenv import load_dotenv
from openai.types.create_embedding_response import CreateEmbeddingResponse
from pymongo import MongoClient
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


class Loader:
    """Processes PDF files for the BiblioQuiz application.

    This class handles the complete pipeline of PDF processing:
    1. Reading PDF files from a directory
    2. Extracting text and chunking into 512 tokens with 64 token overlap
    3. Storing chunks in MongoDB
    4. Encoding chunks with OpenAI Ada 002 embeddings
    5. Storing vector embeddings in Qdrant
    """

    def __init__(
        self,
        env_file: Optional[str] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> None:
        """Initialize the Loader with database connections from .env file.

        Args:
            env_file: Path to .env file (default: None, uses default .env)
            chunk_size: Size of text chunks in tokens (default: 512)
            chunk_overlap: Overlap between chunks in tokens (default: 64)
        """
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        # Get configuration from environment variables
        mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        mongo_db: str = os.getenv("MONGO_DB", "biblioquiz")
        mongo_collection: str = os.getenv("MONGO_COLLECTION", "chunks")
        qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "embeddings")
        openai_api_key: str | None = os.getenv("OPENAI_API_KEY")

        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.chunk_size: int = chunk_size
        self.chunk_overlap: int = chunk_overlap

        # Initialize MongoDB connection
        self.mongo_client = MongoClient(mongo_uri)
        self.mongo_db = self.mongo_client[mongo_db]
        self.mongo_collection = self.mongo_db[mongo_collection]

        # Initialize Qdrant connection
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.qdrant_collection: str = qdrant_collection

        # Initialize OpenAI client
        openai.api_key = openai_api_key

        # Initialize tokenizer for Ada 002
        self.tokenizer: tiktoken.Encoding = tiktoken.encoding_for_model("text-embedding-ada-002")

        # Ensure Qdrant collection exists
        self._ensure_qdrant_collection()

    def _ensure_qdrant_collection(self) -> None:
        """Ensure the Qdrant collection exists with proper configuration."""
        try:
            self.qdrant_client.get_collection(self.qdrant_collection)
        except Exception:
            # Collection doesn't exist, create it
            self.qdrant_client.create_collection(
                collection_name=self.qdrant_collection,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text content from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text content as a string

        Raises:
            Exception: If PDF reading fails
        """
        text: str = ""
        with open(pdf_path, "rb") as file:
            pdf_reader = pypdf.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text

    def _chunk_text(self, text: str) -> List[str]:
        """Chunk text into overlapping segments based on token count.

        Args:
            text: Input text to be chunked

        Returns:
            List of text chunks with specified token size and overlap
        """
        tokens: List[int] = self.tokenizer.encode(text)
        chunks = []

        start = 0
        while start < len(tokens):
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens: List[int] = tokens[start:end]
            chunk_text: str = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)

            if end == len(tokens):
                break

            start = end - self.chunk_overlap

        return chunks

    def _generate_chunk_id(self, file_path: str, chunk_index: int) -> str:
        """Generate a unique ID for a chunk.

        Args:
            file_path: Path of the source file
            chunk_index: Index of the chunk within the file

        Returns:
            Unique chunk identifier
        """
        content: str = f"{file_path}:{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()

    def _store_chunk_in_mongo(self, chunk_data: Dict[str, Any]) -> None:
        """Store a text chunk in MongoDB.

        Args:
            chunk_data: Dictionary containing chunk information
        """
        self.mongo_collection.insert_one(chunk_data)

    def _get_embedding(self, text: str) -> List[float]:
        """Get OpenAI Ada 002 embedding for text.

        Args:
            text: Text to encode

        Returns:
            Embedding vector as list of floats
        """
        response: CreateEmbeddingResponse = openai.embeddings.create(
            input=text, model="text-embedding-ada-002"
        )
        return response.data[0].embedding

    def _store_vector_in_qdrant(
        self, chunk_id: str, vector: List[float], metadata: Dict[str, Any]
    ) -> None:
        """Store vector embedding in Qdrant.

        Args:
            chunk_id: Unique identifier for the chunk
            vector: Embedding vector
            metadata: Additional metadata for the vector
        """
        point = PointStruct(id=chunk_id, vector=vector, payload=metadata)
        self.qdrant_client.upsert(collection_name=self.qdrant_collection, points=[point])

    def process_pdf_file(self, pdf_path: Path) -> int:
        """Process a single PDF file through the complete pipeline.

        Args:
            pdf_path: Path to the PDF file to process

        Returns:
            Number of chunks processed

        Raises:
            Exception: If processing fails at any stage
        """
        # Extract text from PDF
        text: str = self._extract_text_from_pdf(pdf_path)

        # Chunk the text
        chunks: List[str] = self._chunk_text(text)

        processed_count = 0
        for i, chunk in enumerate(chunks):
            # Generate unique ID for chunk
            chunk_id: str = self._generate_chunk_id(str(pdf_path), i)

            # Prepare chunk data for MongoDB
            chunk_data = {
                "_id": chunk_id,
                "source_file": str(pdf_path),
                "chunk_index": i,
                "text": chunk,
                "token_count": len(self.tokenizer.encode(chunk)),
            }

            # Store chunk in MongoDB
            self._store_chunk_in_mongo(chunk_data)

            # Generate embedding
            embedding: List[float] = self._get_embedding(chunk)

            # Prepare metadata for Qdrant
            metadata = {
                "source_file": str(pdf_path),
                "chunk_index": i,
                "token_count": chunk_data["token_count"],
            }

            # Store vector in Qdrant
            self._store_vector_in_qdrant(chunk_id, embedding, metadata)

            processed_count += 1

        return processed_count

    def process_directory(self, directory_path: Path) -> Dict[str, int]:
        """Process all PDF files in a directory.

        Args:
            directory_path: Path to directory containing PDF files

        Returns:
            Dictionary mapping file paths to number of chunks processed

        Raises:
            Exception: If directory access fails or processing errors occur
        """
        if not directory_path.exists() or not directory_path.is_dir():
            raise ValueError(f"Directory {directory_path} does not exist or is not a directory")

        results = {}
        pdf_files: List[Path] = list(directory_path.glob("*.pdf"))

        for pdf_file in pdf_files:
            try:
                chunk_count = self.process_pdf_file(pdf_file)
                results[str(pdf_file)] = chunk_count
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")
                results[str(pdf_file)] = 0

        return results

    def close_connections(self) -> None:
        """Close database connections."""
        self.mongo_client.close()
