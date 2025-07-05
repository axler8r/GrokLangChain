"""Schema definitions for BiblioTeq application.

This module contains all data structure definitions used across the application,
ensuring consistency between components and providing a single source of truth
for data schemas.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ChunkRecord:
    """MongoDB document schema for text chunks.

    This represents the complete document stored in MongoDB for each text chunk,
    including all metadata needed for retrieval and display.
    """

    chunk_id: str  # Used as MongoDB _id field
    document_title: str
    document_checksum: str
    thumbnail: str  # Base64-encoded thumbnail
    chunk_index: int
    text: str
    token_count: int

    def to_mongo_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for MongoDB storage.

        Returns:
            Dictionary with _id field mapped from chunk_id
        """
        return {
            "_id": self.chunk_id,
            "document_title": self.document_title,
            "document_checksum": self.document_checksum,
            "thumbnail": self.thumbnail,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "token_count": self.token_count,
        }

    @classmethod
    def from_mongo_dict(cls, mongo_doc: Dict[str, Any]) -> "ChunkRecord":
        """Create ChunkRecord from MongoDB document.

        Args:
            mongo_doc: Dictionary from MongoDB with _id field

        Returns:
            ChunkRecord instance
        """
        return cls(
            chunk_id=mongo_doc["_id"],
            document_title=mongo_doc["document_title"],
            document_checksum=mongo_doc["document_checksum"],
            thumbnail=mongo_doc["thumbnail"],
            chunk_index=mongo_doc["chunk_index"],
            text=mongo_doc["text"],
            token_count=mongo_doc["token_count"],
        )


@dataclass
class RetrievalResult:
    """Result returned by retriever with similarity scoring.

    Extends ChunkRecord with similarity scoring information from vector search.
    """

    chunk_id: str
    text: str
    document_title: str
    document_checksum: str
    thumbnail: str
    chunk_index: int
    similarity_score: float
    token_count: int

    @classmethod
    def from_chunk_record(
        cls, chunk_record: ChunkRecord, similarity_score: float
    ) -> "RetrievalResult":
        """Create RetrievalResult from ChunkRecord and similarity score.

        Args:
            chunk_record: The chunk data from MongoDB
            similarity_score: Cosine similarity score from vector search

        Returns:
            RetrievalResult instance
        """
        return cls(
            chunk_id=chunk_record.chunk_id,
            text=chunk_record.text,
            document_title=chunk_record.document_title,
            document_checksum=chunk_record.document_checksum,
            thumbnail=chunk_record.thumbnail,
            chunk_index=chunk_record.chunk_index,
            similarity_score=similarity_score,
            token_count=chunk_record.token_count,
        )


@dataclass
class EmbeddingMetadata:
    """Qdrant payload schema for vector storage.

    Contains metadata stored alongside vectors in Qdrant for filtering
    and enriching search results.
    """

    document_title: str
    document_checksum: str
    chunk_index: int
    token_count: int

    def to_qdrant_payload(self) -> Dict[str, Any]:
        """Convert to dictionary format for Qdrant payload.

        Returns:
            Dictionary suitable for Qdrant point payload
        """
        return {
            "document_title": self.document_title,
            "document_checksum": self.document_checksum,
            "chunk_index": self.chunk_index,
            "token_count": self.token_count,
        }
