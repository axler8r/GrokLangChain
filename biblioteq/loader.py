"""Loader module for BiblioQuiz application.

This module provides functionality to process PDF files by chunking them into
manageable pieces, storing the chunks in MongoDB, encoding them with OpenAI
embeddings, and storing the vector embeddings in Qdrant.
"""

import hashlib
from pathlib import Path
from typing import Any, Dict, List

import openai
import pypdf
import tiktoken
from openai.types.create_embedding_response import CreateEmbeddingResponse
from pymongo import MongoClient
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from biblioteq.config import Configuration

configuration: Configuration = Configuration.get_instance()


class Loader:
    """Index PDF files.

    This class handles the complete pipeline of PDF processing:
    1. Reading PDF files from a directory
    2. Extracting text and chunking into 512 tokens with 64 token overlap
    3. Storing chunks in MongoDB
    4. Encoding chunks with OpenAI Ada 002 embeddings
    5. Storing vector embeddings in Qdrant
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ) -> None:
        """Initialize the Loader with database connections.

        Args:
            chunk_size: Size of text chunks in tokens (default: 512)
            chunk_overlap: Overlap between chunks in tokens (default: 64)
        """

        self.chunk_size: int = chunk_size
        self.chunk_overlap: int = chunk_overlap

        self.mongo_client = MongoClient(configuration.mongo_uri)
        self.mongo_db = self.mongo_client[configuration.mongo_db]
        self.mongo_collection = self.mongo_db[configuration.mongo_collection]

        self.qdrant_client = QdrantClient(
            host=configuration.qdrant_host, port=configuration.qdrant_port
        )
        self.qdrant_collection: str = configuration.qdrant_collection

        openai.api_key = configuration.openai_api_key

        self.tokenizer: tiktoken.Encoding = tiktoken.encoding_for_model(
            configuration.openai_encoding_model
        )

        self._ensure_qdrant_collection()

    def _ensure_qdrant_collection(self) -> None:
        try:
            self.qdrant_client.get_collection(self.qdrant_collection)
        except Exception:
            # Collection doesn't exist, create it
            self.qdrant_client.create_collection(
                collection_name=self.qdrant_collection,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        text: str = ""
        with open(pdf_path, "rb") as file:
            pdf_reader = pypdf.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text

    def _chunk_text(self, text: str) -> List[str]:
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

            start: int = end - self.chunk_overlap

        return chunks

    def _generate_chunk_id(self, file_path: str, chunk_index: int) -> str:
        content: str = f"{file_path}:{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()

    def _store_chunk_in_mongo(self, chunk_data: Dict[str, Any]) -> None:
        self.mongo_collection.insert_one(chunk_data)

    def _get_embedding(self, text: str) -> List[float]:
        response: CreateEmbeddingResponse = openai.embeddings.create(
            input=text, model=configuration.openai_encoding_model
        )
        return response.data[0].embedding

    def _store_vector_in_qdrant(
        self, chunk_id: str, vector: List[float], metadata: Dict[str, Any]
    ) -> None:
        point = PointStruct(id=chunk_id, vector=vector, payload=metadata)
        self.qdrant_client.upsert(
            collection_name=self.qdrant_collection, points=[point]
        )

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
            raise ValueError(
                f"Directory {directory_path} does not exist or is not a directory"
            )

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
