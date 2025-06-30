"""Semantic Query Layer for BiblioTeq.

This module provides the agentic workflow that interprets user requests,
retrieves relevant data from vector and document databases, and generates
responses based on user queries.
"""

import asyncio
import concurrent.futures

from asyncio import AbstractEventLoop
from dataclasses import dataclass
from typing import Any, Dict, List

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base._chat_agent import Response
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_core.models import ChatCompletionClient
from autogen_core.tools import BaseTool
from biblioteq.config import Configuration
from pydantic import BaseModel, Field

configuration: Configuration = Configuration.get_instance()


@dataclass
class QueryResponse:
    """Response from a semantic query.

    Attributes:
        answer: The generated response to the user's query
        sources: List of source documents/chunks used to generate the answer
        confidence: Confidence score of the response (0.0 to 1.0)
        metadata: Additional metadata about the query processing
    """

    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    metadata: Dict[str, Any]


class RetrieveDocumentsInput(BaseModel):
    """Input schema for document retrieval."""

    query: str = Field(description="The search query to find relevant document chunks")


class RetrieveDocumentsOutput(BaseModel):
    """Output schema for document retrieval."""

    chunks: List[Dict[str, Any]] = Field(description="List of relevant document chunks")
    total_results: int = Field(description="Total number of results found")


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
                chunks=[
                    {
                        "content": "No retriever service available",
                        "source": "system",
                        "score": 0.0,
                    }
                ],
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

            # Format results for the tool output
            chunks = []
            for result in results:
                chunk = {
                    "content": result.text,
                    "source": result.source_file,
                    "chunk_index": result.chunk_index,
                    "score": result.similarity_score,
                    "chunk_id": result.chunk_id,
                }
                chunks.append(chunk)

            return RetrieveDocumentsOutput(chunks=chunks, total_results=len(chunks))
        except Exception as e:
            return RetrieveDocumentsOutput(
                chunks=[
                    {
                        "content": f"Retrieval failed: {str(e)}",
                        "source": "system",
                        "score": 0.0,
                    }
                ],
                total_results=0,
            )


class SemanticQueryLayer:
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
        self.retriever_service = retriever_service
        self._setup_agents()

    def _setup_agents(self) -> None:
        self.model_config = {
            "provider": "OpenAIChatCompletionClient",
            "config": {
                "model": configuration.openai_model,
                "api_key": configuration.openai_api_key,
            },
        }

        self.retrieval_tool = RetrieveDocumentsTool(self.retriever_service)

    def _extract_sources(self, retrieval_result):
        sources = []
        if retrieval_result.chunks:
            for chunk in retrieval_result.chunks:
                source: Dict[str, Any] = {
                    "source": chunk.get("source", "Unknown"),
                    "content": chunk.get("content", "")[:200],  # Truncate for display
                    "score": chunk.get("score", 0.0),
                    "chunk_index": chunk.get("chunk_index", 0),
                }
                sources.append(source)
        return sources

    def _calculate_confidence(self, sources: List[Dict[str, Any]]) -> float:
        if not sources:
            return 0.0

        max_score = max(source.get("score", 0.0) for source in sources)
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
                    [chunk.get("content", "") for chunk in retrieval_result.chunks]
                )

                # Create model client for generating summary
                if "provider" in self.model_config:
                    model_config = self.model_config
                else:
                    model_config = {
                        "provider": "openai",
                        "config": {
                            "model": self.model_config.get("model", "gpt-4"),
                            "api_key": self.model_config.get("api_key"),
                        },
                    }

                try:
                    model_client: ChatCompletionClient = (
                        ChatCompletionClient.load_component(model_config)
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
                    # Fallback to a simple context-based response if agent fails
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
