"""Query processing service with async/sync coordination."""

import asyncio
import threading
from typing import Any, Dict, Tuple, Optional
from asyncio import Task

import streamlit as st
from pymongo import MongoClient
from qdrant_client import QdrantClient

from biblioteq.config import Configuration
from biblioteq.retriever import Retriever
from biblioteq.schema import QueryResponse
from biblioteq.semql import SemanticQueryLayer


class QueryService:
    """Service for handling document queries with async/sync coordination."""

    def __init__(self) -> None:
        """Initialize the query service."""
        self.configuration = Configuration.get_instance()

    @st.cache_resource
    def _initialize_semql(_self) -> Optional[SemanticQueryLayer]:
        try:
            retriever = Retriever(max_results=5, min_similarity_threshold=0.1)

            retriever.qdrant_client = QdrantClient(
                host=_self.configuration.qdrant_host,
                port=_self.configuration.qdrant_port,
            )
            retriever.mongo_client = MongoClient(_self.configuration.mongo_uri)
            retriever.mongo_collection = retriever.mongo_client[
                _self.configuration.mongo_db
            ][_self.configuration.mongo_collection]

            return SemanticQueryLayer(retriever_service=retriever)
        except Exception as e:
            st.error(f"Failed to initialize query system: {str(e)}")
            return None

    async def _process_query_async(
        self, semql: SemanticQueryLayer, query: str
    ) -> QueryResponse:
        try:
            return await semql.query(query)
        except Exception as e:
            raise e

    def process_query(
        self, query: str
    ) -> Tuple[Optional[QueryResponse], Optional[str]]:
        """Process a query synchronously with proper async/sync coordination.

        Args:
            query: The user's natural language query

        Returns:
            Tuple of (QueryResponse or None, error message or None)
        """
        semql = self._initialize_semql()
        if semql is None:
            return None, "Failed to initialize query system"

        try:
            # Check if there's already an event loop running
            try:
                asyncio.get_running_loop()
                return self._run_in_thread(semql, query)
            except RuntimeError:
                return self._run_in_new_loop(semql, query)
        except Exception as e:
            return None, str(e)

    def _run_in_thread(
        self, semql: SemanticQueryLayer, query: str
    ) -> Tuple[Optional[QueryResponse], Optional[str]]:
        result_container: Dict[str, Any] = {"result": None, "error": None}

        def run_async() -> None:
            try:
                new_loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    result: QueryResponse = new_loop.run_until_complete(
                        self._process_query_async(semql, query)
                    )
                    result_container["result"] = result
                finally:
                    self._cleanup_event_loop(new_loop)
            except Exception as e:
                result_container["error"] = str(e)

        thread = threading.Thread(target=run_async)
        thread.start()
        thread.join()

        if result_container["error"]:
            return None, result_container["error"]

        return result_container["result"], None

    def _run_in_new_loop(
        self, semql: SemanticQueryLayer, query: str
    ) -> Tuple[Optional[QueryResponse], Optional[str]]:
        loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result: QueryResponse = loop.run_until_complete(
                self._process_query_async(semql, query)
            )
            return result, None
        finally:
            self._cleanup_event_loop(loop)

    def _cleanup_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        pending: set[Task[Any]] = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()

        # Wait for cancelled tasks to finish
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

        loop.close()
