"""Retriever module for BiblioTeq application.

This module provides functionality to search for relevant text chunks using
vector similarity search in Qdrant and retrieve associated metadata from MongoDB.
"""

from typing import List

import openai
import tiktoken
from biblioteq.config import Configurable
from biblioteq.schema import ChunkRecord, RetrievalResult
from openai.types.create_embedding_response import CreateEmbeddingResponse
from pymongo import MongoClient
from qdrant_client import QdrantClient
from qdrant_client.models import ScoredPoint


class Retriever(Configurable):
    """Retrieves relevant text chunks based on natural language queries.

    This class handles the complete pipeline of query processing:
    1. Encoding user queries with OpenAI Ada 002 embeddings
    2. Performing vector similarity search in Qdrant
    3. Retrieving associated text chunks and metadata from MongoDB
    4. Returning ranked results with configurable filtering

    Works with content-based checksum indexing where chunk IDs are generated
    from document checksums, ensuring consistent identification regardless
    of file location or name changes.
    """

    def __init__(
        self,
        max_results: int = 10,
        min_similarity_threshold: float = 0.6,
    ) -> None:
        """Initialize the Retriever with database connections.

        Args:
            max_results: Maximum number of results to return (default: 10)
            min_similarity_threshold: Minimum similarity score threshold (default: 0.6)
        """

        super().__init__()

        self.max_results: int = max_results
        self.min_similarity_threshold: float = min_similarity_threshold

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

    def _get_query_embedding(self, query: str) -> List[float]:
        response: CreateEmbeddingResponse = openai.embeddings.create(
            input=query, model=self._config.openai_encoding_model
        )
        return response.data[0].embedding

    def _convert_uuid_to_md5(self, chunk_id: str) -> str:
        """Convert UUID format to MD5 format by removing hyphens.
        
        This handles potential legacy data where Qdrant might return UUIDs
        with hyphens but MongoDB stores them without hyphens.
        
        Args:
            chunk_id: Chunk ID potentially in UUID format with hyphens
            
        Returns:
            Chunk ID with hyphens removed
        """
        return chunk_id.replace("-", "")

    def search(
        self,
        query: str,
        max_results: int | None = None,
        min_similarity_threshold: float | None = None,
    ) -> List[RetrievalResult]:
        """Search for relevant text chunks using vector similarity.

        Args:
            query: Natural language query string
            max_results: Maximum number of results to return (uses instance default if None)
            min_similarity_threshold: Minimum similarity score threshold (uses instance default if None)

        Returns:
            List of RetrievalResult objects sorted by similarity score (highest first)
        """
        # Use instance defaults if parameters not provided
        max_results = max_results or self.max_results
        min_similarity_threshold = min_similarity_threshold or self.min_similarity_threshold

        # Generate embedding for the query
        query_vector = self._get_query_embedding(query)
        if not query_vector:
            return []

        # Handle empty query
        if not query.strip():
            return []

        # Perform vector search in Qdrant
        try:
            # Don't apply score_threshold at Qdrant level to see raw scores
            search_results: List[ScoredPoint] = self.qdrant_client.query_points(
                collection_name=self.qdrant_collection,
                query=query_vector,
                limit=max_results,
            ).points

        except Exception as e:
            print(f"Error in Qdrant search: {e}")
            return []

        # Retrieve full chunk data from MongoDB
        results = []
        for scored_point in search_results:
            chunk_id = str(scored_point.id)
            similarity_score: float = scored_point.score

            # Apply threshold filtering here instead of at Qdrant level
            if similarity_score < min_similarity_threshold:
                continue

            # Convert UUID format to MD5 format if needed (remove hyphens)
            mongo_chunk_id = self._convert_uuid_to_md5(chunk_id)

            # Get chunk data from MongoDB using the converted chunk ID
            chunk_doc = self.mongo_collection.find_one({"_id": mongo_chunk_id})
            if chunk_doc:
                # Convert MongoDB document to ChunkRecord
                chunk_record = ChunkRecord.from_mongo_dict(chunk_doc)
                
                # Create RetrievalResult with similarity score
                result = RetrievalResult.from_chunk_record(chunk_record, similarity_score)
                results.append(result)

        return results

    def close_connections(self) -> None:
        """Close database connections."""
        self.mongo_client.close()
