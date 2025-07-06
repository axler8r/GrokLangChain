"""Semantic Query Layer for BiblioTeq.

This module provides the agentic workflow that interprets user requests,
retrieves relevant data from vector and document databases, and generates
responses based on user queries.
"""

import asyncio
import concurrent.futures

from asyncio import AbstractEventLoop
from typing import Any, List

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base._chat_agent import Response
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_core.models import ChatCompletionClient
from autogen_core.tools import BaseTool
from biblioteq.config import Configurable
from biblioteq.schema import (
    QueryResponse,
    RetrieveDocumentsInput,
    RetrieveDocumentsOutput,
    SourceMetadata,
)


class RetrieveDocumentsTool(BaseTool[RetrieveDocumentsInput, RetrieveDocumentsOutput]):
    """Tool for retrieving relevant documents from the knowledge base."""

    def __init__(self, retriever_service: Any) -> None:
        super().__init__(
            RetrieveDocumentsInput,
            RetrieveDocumentsOutput,
            "retrieve_documents",
            "Retrieve relevant document chunks from the knowledge base based on a search query",
        )
        self.retriever_service = retriever_service

    async def run(
        self, args: RetrieveDocumentsInput, cancellation_token: CancellationToken
    ) -> RetrieveDocumentsOutput:
        """Execute the document retrieval.

        Args:
            args: Input arguments containing the search query
            cancellation_token: Token for cancelling the operation

        Returns:
            RetrieveDocumentsOutput containing the retrieved chunks
        """
        if not self.retriever_service:
            return RetrieveDocumentsOutput(
                chunks=[],
                total_results=0,
            )

        try:
            # Call retriever service synchronously in async context
            # Use asyncio.get_event_loop().run_in_executor to avoid blocking
            loop: AbstractEventLoop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = await loop.run_in_executor(
                    executor,
                    lambda: self.retriever_service.search(query=args.query),
                )

            # Format results for the tool output using ChunkResult schema
            chunks = [result.to_chunk_result() for result in results]

            return RetrieveDocumentsOutput(chunks=chunks, total_results=len(chunks))
        except Exception:
            return RetrieveDocumentsOutput(
                chunks=[],
                total_results=0,
            )


class SemanticQueryLayer(Configurable):
    """Semantic Query Layer that coordinates between UI and data services.

    This class acts as the main orchestrator for processing natural language
    queries about book content. It interprets user requests, retrieves relevant
    data using the retriever service, and generates contextual responses using
    an agentic workflow.
    """

    def __init__(self, retriever_service: Any = None) -> None:
        """Initialize the Semantic Query Layer.

        Args:
            retriever_service: The retriever service for database queries
        """
        super().__init__()

        self.retriever_service = retriever_service
        self._setup_agents()

    def _setup_agents(self) -> None:
        self.model_config = {
            "provider": "OpenAIChatCompletionClient",
            "config": {
                "model": self._config.openai_model,
                "api_key": self._config.openai_api_key,
            },
        }

        self.retrieval_tool = RetrieveDocumentsTool(self.retriever_service)

    def _extract_sources(
        self, retrieval_result: RetrieveDocumentsOutput
    ) -> List[SourceMetadata]:
        sources = []
        if retrieval_result.chunks:
            for chunk in retrieval_result.chunks:
                source = SourceMetadata(
                    source=chunk.source,
                    content=chunk.content[:200],  # Truncate for display
                    score=chunk.score,
                    chunk_index=chunk.chunk_index,
                    chunk_id=chunk.chunk_id,
                    thumbnail=chunk.thumbnail,
                    document_checksum=chunk.document_checksum,
                    token_count=chunk.token_count,
                )
                sources.append(source)
        return sources

    def _calculate_confidence(self, sources: List[SourceMetadata]) -> float:
        if not sources:
            return 0.0

        max_score = max(source.score for source in sources)
        source_bonus: float = min(len(sources) * 0.1, 0.3)

        return min(max_score + source_bonus, 1.0)

    async def query(self, user_query: str) -> QueryResponse:
        """Process a natural language query about book content.

        Args:
            user_query: The natural language question from the user
            context: Optional context information (e.g., conversation history, filters)

        Returns:
            QueryResponse containing the answer, sources, and metadata

        Raises:
            ValueError: If the query is empty or invalid
        """
        if not user_query.strip():
            raise ValueError("Query cannot be empty")
        try:
            retrieval_result: RetrieveDocumentsOutput = await self.retrieval_tool.run(
                RetrieveDocumentsInput(query=user_query), CancellationToken()
            )

            sources = self._extract_sources(retrieval_result)
            confidence: float = self._calculate_confidence(sources)

            if sources:
                context = "\n\n".join(
                    [chunk.content for chunk in retrieval_result.chunks]
                )

                try:
                    model_client: ChatCompletionClient = (
                        ChatCompletionClient.load_component(self.model_config)
                    )

                    # Create assistant agent for summarization
                    assistant_agent = AssistantAgent(
                        name="research_assistant",
                        model_client=model_client,
                        tools=[],  # No tools needed for simple summarization
                        system_message=f"""
You are a knowledgeable research assistant. Based on the following context from
technical books and documentation, provide a clear, comprehensive answer to the
user's question.

Context:
{context[:4000]}  # Limit context to avoid token limits

Question: {user_query}

Provide a direct, helpful answer that synthesizes the information from the
context. If the context doesn't contain sufficient information to fully answer
the question, clearly state this limitation.""",
                    )

                    # Get response from assistant
                    user_message = TextMessage(content=user_query, source="user")
                    response: Response = await assistant_agent.on_messages(
                        messages=[user_message], cancellation_token=CancellationToken()
                    )

                    final_answer = "I apologize, but I couldn't generate a proper response to your query."
                    if response.chat_message and isinstance(
                        response.chat_message, TextMessage
                    ):
                        final_answer: str = response.chat_message.content

                except Exception as e:
                    # If this is a model client error (during load_component), propagate it
                    if "Model client error" in str(e):
                        raise e
                    # Otherwise, fallback to a simple context-based response if agent fails
                    final_answer = (
                        f"Based on the retrieved information: {context[:500]}..."
                    )
                    if len(context) > 500:
                        final_answer += f"\n\nI found {len(sources)} relevant sections from your books, but encountered an issue generating a detailed summary: {str(e)}"
            else:
                final_answer = "I couldn't find any relevant information in your book collection to answer this query. Please try rephrasing your question or check if the relevant documents have been uploaded."

            return QueryResponse(
                answer=final_answer,
                sources=sources,
                confidence=confidence,
                metadata={
                    "query": user_query,
                    "status": "success",
                    "sources_found": len(sources),
                    "retrieval_total": retrieval_result.total_results,
                },
            )

        except Exception as e:
            return QueryResponse(
                answer=f"I encountered an error while processing your query: {str(e)}",
                sources=[],
                confidence=0.0,
                metadata={"query": user_query, "status": "error", "error": str(e)},
            )
