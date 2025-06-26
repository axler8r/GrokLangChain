"""Semantic Query Layer for BiblioTeq.

This module provides the agentic workflow that interprets user requests,
retrieves relevant data from vector and document databases, and generates
responses based on user queries.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base._chat_agent import Response
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_core.models import ChatCompletionClient
from autogen_core.tools import BaseTool
from pydantic import BaseModel, Field


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
        """Execute the document retrieval."""
        if not self.retriever_service:
            return RetrieveDocumentsOutput(
                chunks=[
                    {"content": "No retriever service available", "source": "system", "score": 0.0}
                ],
                total_results=0,
            )

        try:
            # TODO: Call actual retriever service
            # For now, return placeholder data
            chunks = [
                {
                    "content": f"Sample content from your eBooks that matches the query: {args.query}",
                    "source": "sample_book.pdf",
                    "page": 42,
                    "score": 0.85,
                }
            ]
            return RetrieveDocumentsOutput(chunks=chunks, total_results=len(chunks))
        except Exception as e:
            return RetrieveDocumentsOutput(
                chunks=[
                    {"content": f"Retrieval failed: {str(e)}", "source": "system", "score": 0.0}
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

    def __init__(
        self, retriever_service: Any = None, config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize the Semantic Query Layer.

        Args:
            retriever_service: The retriever service for database queries
            config: Configuration dictionary for the query layer
        """
        self.retriever_service = retriever_service
        self.config: Dict[str, Any] = config or {}
        self._setup_agents()

    def _setup_agents(self) -> None:
        """Set up the autogen agents for the workflow."""
        # Get model client configuration
        model_config = self.config.get(
            "model_config",
            {
                "model": "gpt-4",
                "api_key": "your-api-key",  # This should come from environment or config
            },
        )

        # Create model client - this will need proper configuration
        # For now, we'll store the config to create the client when needed
        self.model_config = model_config

        # Create the retrieval tool
        self.retrieval_tool = RetrieveDocumentsTool(self.retriever_service)

    async def query(
        self, user_query: str, context: Optional[Dict[str, Any]] = None
    ) -> QueryResponse:
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
            # Create model client (this would typically be done once and reused)
            model_client = ChatCompletionClient.load_component(self.model_config)

            # Create assistant agent with retrieval tool
            assistant_agent = AssistantAgent(
                name="assistant",
                model_client=model_client,
                tools=[self.retrieval_tool],
                system_message=
                """
You are a helpful assistant that answers questions about technical books and documentation.

Use the retrieve_documents tool to find relevant information from the user's
eBook collection.  Provide comprehensive answers based on the retrieved context.
Be precise and cite specific information when possible.  If the context doesn't
contain enough information to answer the question, say so clearly.
                """.strip(),
            )

            # Create the user message
            user_message = TextMessage(content=user_query, source="user")

            # Get response from assistant
            response: Response = await assistant_agent.on_messages(
                messages=[user_message], cancellation_token=CancellationToken()
            )

            # Extract the final response
            final_response = "No response generated"
            if response.chat_message:
                if isinstance(response.chat_message, TextMessage):
                    final_response = response.chat_message.content
                else:
                    # Handle other message types safely
                    final_response = str(response.chat_message)

            return QueryResponse(
                answer=final_response,
                sources=[],  # TODO: Extract from retrieval results
                confidence=0.8,  # TODO: Calculate based on retrieval scores
                metadata={"query": user_query, "status": "success"},
            )

        except Exception as e:
            return QueryResponse(
                answer=f"Sorry, I encountered an error processing your query: {str(e)}",
                sources=[],
                confidence=0.0,
                metadata={"query": user_query, "status": "error", "error": str(e)},
            )
