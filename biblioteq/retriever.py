"""Retriever module for BiblioTeq application.

This module provides functionality to search for relevant text chunks using
vector similarity search in Qdrant and retrieve associated metadata from MongoDB.
"""

from typing import List

import openai
import tiktoken
from biblioteq.config import Configuration
from openai.types.create_embedding_response import CreateEmbeddingResponse
from pymongo import MongoClient
from qdrant_client import QdrantClient
from qdrant_client.models import ScoredPoint

configuration: Configuration = Configuration.get_instance()


class RetrievalResult:
    """Container for a single retrieval result with metadata."""

    def __init__(
        self,
        chunk_id: str,
        text: str,
        source_file: str,
        chunk_index: int,
        similarity_score: float,
        token_count: int,
    ) -> None:
        """Initialize a retrieval result.

        Args:
            chunk_id: Unique identifier for the chunk
            text: The actual text content of the chunk
            source_file: Path to the source PDF file
            chunk_index: Index of the chunk within the source file
            similarity_score: Cosine similarity score (0-1, higher is more similar)
            token_count: Number of tokens in the chunk
        """
        self.chunk_id: str = chunk_id
        self.text: str = text
        self.source_file: str = source_file
        self.chunk_index: int = chunk_index
        self.similarity_score: float = similarity_score
        self.token_count: int = token_count


class Retriever:
    """Retrieves relevant text chunks based on natural language queries.

    This class handles the complete pipeline of query processing:
    1. Encoding user queries with OpenAI Ada 002 embeddings
    2. Performing vector similarity search in Qdrant
    3. Retrieving associated text chunks and metadata from MongoDB
    4. Returning ranked results with configurable filtering
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

        self.max_results: int = max_results
        self.min_similarity_threshold: float = min_similarity_threshold

        self.mongo_client = MongoClient(configuration.mongo_uri)
        self.mongo_db = self.mongo_client[configuration.mongo_db]
        self.mongo_collection = self.mongo_db[configuration.mongo_collection]

        self.qdrant_client = QdrantClient(
            host=configuration.qdrant_host, port=configuration.qdrant_port
        )
        self.qdrant_collection: str = configuration.qdrant_collection

        openai.api_key = configuration.openai_api_key

        self.tokenizer: tiktoken.Encoding = tiktoken.encoding_for_model(
            "text-embedding-ada-002"
        )

    def _get_query_embedding(self, query: str) -> List[float]:
        """Get OpenAI Ada 002 embedding for the query.

        Args:
            query: Natural language query to encode

        Returns:
            Embedding vector as list of floats
        """
        response: CreateEmbeddingResponse = openai.embeddings.create(
            input=query, model="text-embedding-ada-002"
        )
        return response.data[0].embedding

    def search(
        self,
        query: str,
    ) -> List[RetrievalResult]:
        """Search for relevant chunks based on a natural language query.

        Args:
            query: Natural language query

        Returns:
            List of RetrievalResult objects sorted by similarity score (highest first)

        Raises:
            Exception: If search fails at any stage
        """

        # Get embedding for the query
        try:
            query_vector: List[float] = self._get_query_embedding(query)
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []

        # Perform vector search in Qdrant
        try:
            # Don't apply score_threshold at Qdrant level to see raw scores
            search_results: List[ScoredPoint] = self.qdrant_client.query_points(
                collection_name=self.qdrant_collection,
                query=query_vector,
                limit=self.max_results,
            ).points

        except Exception as e:
            print(f"Error in Qdrant search: {e}")
            return []

        # Retrieve full chunk data from MongoDB
        results = []
        for scored_point in search_results:
            chunk_id = scored_point.id
            similarity_score: float = scored_point.score

            # Apply threshold filtering here instead of at Qdrant level
            if similarity_score < self.min_similarity_threshold:
                continue

            # Fix: Qdrant formats MD5 hashes as UUIDs with hyphens, but MongoDB stores them without hyphens
            # Convert Qdrant UUID format back to MD5 hash format for MongoDB lookup
            if (
                isinstance(chunk_id, str)
                and len(chunk_id) == 36
                and chunk_id.count("-") == 4
            ):
                mongo_chunk_id: str = chunk_id.replace("-", "")
            else:
                mongo_chunk_id: str = str(chunk_id)

            # Get chunk data from MongoDB
            chunk_doc = self.mongo_collection.find_one({"_id": mongo_chunk_id})
            if chunk_doc:
                result = RetrievalResult(
                    chunk_id=mongo_chunk_id,  # Use the MongoDB format for consistency
                    text=chunk_doc["text"],
                    source_file=chunk_doc["source_file"],
                    chunk_index=chunk_doc["chunk_index"],
                    similarity_score=similarity_score,
                    token_count=chunk_doc["token_count"],
                )
                results.append(result)

        return results

    def close_connections(self) -> None:
        """Close database connections."""
        self.mongo_client.close()
