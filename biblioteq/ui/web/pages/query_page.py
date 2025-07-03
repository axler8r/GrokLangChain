"""Document query page implementation."""

import streamlit as st

from biblioteq.ui.web.services.query_service import QueryService


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
                _process_query(query)

        _display_query_results()
        st.markdown("</div>", unsafe_allow_html=True)


def _process_query(query: str) -> None:
    """Process the user's query."""
    with st.spinner("Searching your library..."):
        query_service = QueryService()
        result, error = query_service.process_query(query)

        if error:
            st.session_state.query_error = error
            st.session_state.query_result = None
        else:
            st.session_state.last_query = query
            st.session_state.query_result = result
            st.session_state.query_error = None


def _display_query_results() -> None:
    """Display query results from session state."""
    if hasattr(st.session_state, "query_error") and st.session_state.query_error:
        st.error(f"Query failed: {st.session_state.query_error}")

    if hasattr(st.session_state, "query_result") and st.session_state.query_result:
        result = st.session_state.query_result

        st.markdown("### Response")
        st.write(result.answer)

        _display_query_metadata(result)
        _display_query_sources(result)


def _display_query_metadata(result) -> None:
    """Display query result metadata."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Confidence", f"{result.confidence:.1%}")
    with col2:
        st.metric("Status", result.metadata.get("status", "unknown").title())
    with col3:
        st.metric("Sources", len(result.sources))


def _display_query_sources(result) -> None:
    """Display query result sources."""
    if result.sources:
        with st.expander("View Sources"):
            for i, source in enumerate(result.sources, 1):
                st.markdown(f"**Source {i}:** {source.get('source', 'Unknown')}")
                st.text(source.get("content", "No content")[:200] + "...")
                st.markdown("---")
