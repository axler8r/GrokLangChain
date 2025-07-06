"""Loader module for BiblioQuiz application.

This module provides functionality to process PDF files by chunking them into
manageable pieces, storing the chunks in MongoDB, encoding them with OpenAI
embeddings, and storing the vector embeddings in Qdrant.
"""

import base64
import hashlib
import io
from pathlib import Path
from typing import Dict, List

import openai
import pypdf
import tiktoken
from PIL import Image
from openai.types.create_embedding_response import CreateEmbeddingResponse
from pdf2image import convert_from_path
from pymongo import MongoClient
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from biblioteq.config import Configurable
from biblioteq.schema import ChunkRecord, EmbeddingMetadata


class Loader(Configurable):
    """Index PDF files using content-based checksums.

    This class handles the complete pipeline of PDF processing:
    1. Reading PDF files from a directory
    2. Generating MD5 checksums for content-based deduplication
    3. Creating thumbnails from the first page of each PDF
    4. Extracting text and chunking into 512 tokens with 64 token overlap
    5. Storing chunks in MongoDB with document metadata
    6. Encoding chunks with OpenAI Ada 002 embeddings
    7. Storing vector embeddings in Qdrant with consistent IDs

    Chunk IDs are generated from document checksums, ensuring consistent
    identification regardless of file location or name changes.
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
        super().__init__()

        self.chunk_size: int = chunk_size
        self.chunk_overlap: int = chunk_overlap

        self.mongo_client = MongoClient(self._config.mongo_uri)
        self.mongo_db = self.mongo_client[self._config.mongo_db]
        self.mongo_collection = self.mongo_db[self._config.mongo_collection]

        self.qdrant_client = QdrantClient(
            host=self._config.qdrant_host, port=self._config.qdrant_port
        )
        self.qdrant_collection: str = self._config.qdrant_collection

        openai.api_key = self._config.openai_api_key

        self.tokenizer: tiktoken.Encoding = tiktoken.encoding_for_model(
            self._config.openai_encoding_model
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

    def _create_thumbnail(self, pdf_path: Path) -> str:
        pages: List[Image.Image] = convert_from_path(
            pdf_path, first_page=1, last_page=1
        )
        if pages:
            output = io.BytesIO()

            first_page: Image.Image = pages[0]
            first_page.thumbnail(size=(160, 160), resample=Image.Resampling.LANCZOS)
            first_page.save(output, "PNG")

            output.seek(0)

            return base64.b64encode(output.read()).decode("utf-8")
        else:
            raise ValueError(f"No pages found in PDF: {pdf_path}")

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

    def _generate_document_checksum(self, pdf_path: Path) -> str:
        hasher = hashlib.md5()
        with open(pdf_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _generate_chunk_id(self, document_checksum: str, chunk_index: int) -> str:
        content: str = f"{document_checksum}:{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()

    def _store_chunk_in_mongo(self, chunk_record: ChunkRecord) -> None:
        self.mongo_collection.insert_one(chunk_record.to_mongo_dict())

    def _get_embedding(self, text: str) -> List[float]:
        response: CreateEmbeddingResponse = openai.embeddings.create(
            input=text, model=self._config.openai_encoding_model
        )
        return response.data[0].embedding

    def _store_embedding_in_qdrant(
        self, chunk_id: str, vector: List[float], metadata: EmbeddingMetadata
    ) -> None:
        point = PointStruct(
            id=chunk_id, vector=vector, payload=metadata.to_qdrant_payload()
        )
        self.qdrant_client.upsert(
            collection_name=self.qdrant_collection, points=[point]
        )

    def _index_chunk(
        self,
        chunk: str,
        document_checksum: str,
        document_title: str,
        thumbnail: str,
        index: int,
    ) -> None:
        chunk_id: str = self._generate_chunk_id(document_checksum, index)
        token_count: int = len(self.tokenizer.encode(chunk))

        # Create chunk record for MongoDB
        chunk_record = ChunkRecord(
            chunk_id=chunk_id,
            document_title=document_title,
            document_checksum=document_checksum,
            thumbnail=thumbnail,
            chunk_index=index,
            text=chunk,
            token_count=token_count,
        )
        self._store_chunk_in_mongo(chunk_record)

        # Create embedding and metadata for Qdrant
        embedding: List[float] = self._get_embedding(chunk)
        embedding_metadata = EmbeddingMetadata(
            document_title=document_title,
            document_checksum=document_checksum,
            chunk_index=index,
            token_count=token_count,
        )
        self._store_embedding_in_qdrant(chunk_id, embedding, embedding_metadata)

    def process_pdf_file(self, pdf_path: Path, document_name: str) -> int:
        """Process a single PDF file through the complete pipeline.

        Args:
            pdf_path: Path to the PDF file to process
            document_name: Name of the document (used for indexing)

        Returns:
            Number of chunks processed

        Raises:
            Exception: If processing fails at any stage
        """
        document_checksum: str = self._generate_document_checksum(pdf_path)
        thumbnail: str = self._create_thumbnail(pdf_path)
        text: str = self._extract_text_from_pdf(pdf_path)
        chunks: List[str] = self._chunk_text(text)

        processed_count = 0
        for i, chunk in enumerate(chunks):
            self._index_chunk(chunk, document_checksum, document_name, thumbnail, i)
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
                document_name: str = pdf_file.stem
                chunk_count: int = self.process_pdf_file(pdf_file, document_name)
                results[str(pdf_file)] = chunk_count
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")
                results[str(pdf_file)] = 0

        return results

    def close_connections(self) -> None:
        """Close database connections."""
        self.mongo_client.close()
