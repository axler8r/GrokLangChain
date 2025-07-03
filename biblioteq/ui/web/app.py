"""
BiblioTeq Web Frontend

A Streamlit-based web interface for uploading PDF documents and querying
book content using natural language.
"""

import asyncio
import tempfile
from asyncio import Task
from pathlib import Path
from typing import Any, Dict

import streamlit as st
from pymongo import MongoClient
from qdrant_client import QdrantClient
from streamlit.delta_generator import DeltaGenerator

from biblioteq.config import Configuration
from biblioteq.loader import Loader
from biblioteq.retriever import Retriever
from biblioteq.semql import SemanticQueryLayer

configuration: Configuration = Configuration.get_instance()


def apply_material_design_styles() -> None:
    """Apply Material Design-inspired CSS styles to the Streamlit app."""
    # Load CSS from external file
    css_path: Path = Path(__file__).parent / "axler8r.css"

    with open(css_path, "r") as css_file:
        css_content: str = css_file.read()

    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def render_header() -> None:
    """Render the main application header."""
    st.markdown(
        """
    <div class="main-header">
        <h1>BiblioTeq</h1>
        <p>Document Management and Intelligent Query System</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_load_section() -> None:
    """Render the document loading interface."""
    st.markdown(
        '<h2 class="section-header">Load Documents</h2>', unsafe_allow_html=True
    )

    with st.container():
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)

        uploaded_files = st.file_uploader(
            "Select PDF files to upload",
            type=["pdf"],
            accept_multiple_files=True,
            help="Choose one or more PDF files to add to your library",
        )

        if uploaded_files:
            st.write(f"Selected {len(uploaded_files)} file(s):")
            for file in uploaded_files:
                st.write(f"• {file.name}")

            if st.button("Upload Documents", key="upload_btn"):
                try:
                    # Initialize the loader
                    loader = Loader()

                    # Process each uploaded file
                    progress_bar: DeltaGenerator = st.progress(0)
                    status_text: DeltaGenerator = st.empty()
                    results = {}

                    for i, uploaded_file in enumerate(uploaded_files):
                        status_text.text(f"Processing {uploaded_file.name}...")

                        # Save uploaded file to temporary location
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".pdf"
                        ) as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = Path(tmp_file.name)

                        try:
                            # Process the PDF file
                            chunk_count = loader.process_pdf_file(tmp_path)
                            results[uploaded_file.name] = chunk_count

                        finally:
                            # Clean up temporary file
                            tmp_path.unlink(missing_ok=True)

                        # Update progress
                        progress_bar.progress((i + 1) / len(uploaded_files))

                    # Close loader connections
                    loader.close_connections()

                    # Display results
                    status_text.text("Processing complete!")
                    st.success(
                        f"Successfully processed {len(uploaded_files)} document(s)"
                    )

                    # Show processing details
                    st.markdown("### Processing Results")
                    for filename, chunks in results.items():
                        st.write(f"• **{filename}**: {chunks} chunks created")

                except Exception as e:
                    st.error(f"Error processing documents: {str(e)}")
                    st.info("Please check your database connections and try again")

        st.markdown("</div>", unsafe_allow_html=True)


def render_query_section() -> None:
    """Render the document query interface."""
    st.markdown('<h2 class="section-header">Query Library</h2>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="query-section">', unsafe_allow_html=True)

        query = st.text_area(
            "Enter your question",
            placeholder="Ask a question about your documents...",
            height=100,
            help="Use natural language to query your document library",
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Search", key="search_btn", disabled=not query.strip()):
                with st.spinner("Searching your library..."):
                    # Process query using SemanticQueryLayer
                    result, error = process_query_sync(query)

                    if error:
                        st.session_state.query_error = error
                        st.session_state.query_result = None
                    else:
                        st.session_state.last_query = query
                        st.session_state.query_result = result
                        st.session_state.query_error = None

        # Display results
        if hasattr(st.session_state, "query_error") and st.session_state.query_error:
            st.error(f"Query failed: {st.session_state.query_error}")

        if hasattr(st.session_state, "query_result") and st.session_state.query_result:
            result = st.session_state.query_result

            st.markdown("### Response")
            st.write(result.answer)

            # Display metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Confidence", f"{result.confidence:.1%}")
            with col2:
                st.metric("Status", result.metadata.get("status", "unknown").title())
            with col3:
                st.metric("Sources", len(result.sources))

            # Display sources if available
            if result.sources:
                with st.expander("View Sources"):
                    for i, source in enumerate(result.sources, 1):
                        st.markdown(
                            f"**Source {i}:** {source.get('source', 'Unknown')}"
                        )
                        st.text(source.get("content", "No content")[:200] + "...")
                        st.markdown("---")

        st.markdown("</div>", unsafe_allow_html=True)


@st.cache_resource
def initialize_semql() -> None | SemanticQueryLayer:
    """Initialize and cache the SemanticQueryLayer instance."""
    try:
        retriever = Retriever(max_results=5, min_similarity_threshold=0.1)

        retriever.qdrant_client = QdrantClient(
            host=configuration.qdrant_host, port=configuration.qdrant_port
        )
        retriever.mongo_client = MongoClient(configuration.mongo_uri)
        retriever.mongo_collection = retriever.mongo_client[configuration.mongo_db][
            configuration.mongo_collection
        ]

        # Create and return SemanticQueryLayer
        return SemanticQueryLayer(retriever_service=retriever)

    except Exception as e:
        st.error(f"Failed to initialize query system: {str(e)}")
        return None


async def process_query_async(semql, query: str):  # -> Any:
    """Process a query asynchronously using the SemanticQueryLayer."""
    try:
        result = await semql.query(query)
        return result
    except Exception as e:
        raise e


def process_query_sync(query: str):
    """Synchronous wrapper for query processing."""
    semql: None | SemanticQueryLayer = initialize_semql()
    if semql is None:
        return None, "Failed to initialize query system"

    try:
        # Check if there's already an event loop running (Streamlit context)
        try:
            loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
            # If there's already a loop, we need to run in a separate thread
            import threading

            result_container: Dict[str, Any] = {"result": None, "error": None}

            def run_async() -> None:
                try:
                    new_loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        result = new_loop.run_until_complete(
                            process_query_async(semql, query)
                        )
                        result_container["result"] = result
                    finally:
                        # Clean up pending tasks before closing loop
                        pending: set[Task[Any]] = asyncio.all_tasks(new_loop)
                        for task in pending:
                            task.cancel()

                        # Wait for cancelled tasks to finish
                        if pending:
                            new_loop.run_until_complete(
                                asyncio.gather(*pending, return_exceptions=True)
                            )

                        new_loop.close()
                except Exception as e:
                    result_container["error"] = str(e)

            thread = threading.Thread(target=run_async)
            thread.start()
            thread.join()

            if result_container["error"]:
                return None, result_container["error"]
            return result_container["result"], None

        except RuntimeError:
            # No event loop running, we can create our own
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(process_query_async(semql, query))
                return result, None
            finally:
                # Clean up pending tasks before closing loop
                pending: set[Task[Any]] = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()

                # Wait for cancelled tasks to finish
                if pending:
                    loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )

                loop.close()

    except Exception as e:
        return None, str(e)


def main() -> None:
    """Main application entry point."""
    st.set_page_config(
        page_title="BiblioTeq",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    apply_material_design_styles()
    render_header()

    # Initialize session state for navigation
    if "selected_action" not in st.session_state:
        st.session_state.selected_action = "Load"

    # Sidebar navigation
    with st.sidebar:
        st.markdown("## Navigation")

        # Query button
        if st.button(
            "Query Library",
            key="query_btn",
            help="Search and query your document library",
            use_container_width=True,
        ):
            st.session_state.selected_action = "Query"

        # Load button
        if st.button(
            "Load Documents",
            key="load_btn",
            help="Load new documents into your library",
            use_container_width=True,
        ):
            st.session_state.selected_action = "Load"

        # Show current selection
        st.markdown(f"**Current:** {st.session_state.selected_action}")

    # Main content area
    if st.session_state.selected_action == "Load":
        render_load_section()
    elif st.session_state.selected_action == "Query":
        render_query_section()


if __name__ == "__main__":
    main()
