"""
BiblioTeq Web Frontend

Main Streamlit application entry point for the BiblioTeq document management
and intelligent query system.
"""

import sys
from pathlib import Path
import streamlit as st

# Add project root to Python path if running directly
if __name__ == "__main__":
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(project_root))
    except NameError:
        # Handle case where __file__ is not defined (e.g., exec scenarios)
        project_root = Path(".").resolve()
        sys.path.insert(0, str(project_root))

from biblioteq.ui.web.components import apply_stylesheet, render_header
from biblioteq.ui.web.pages import render_load_section, render_query_section


def main() -> None:
    """Main application entry point."""
    st.set_page_config(
        page_title="BiblioTeq",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    apply_stylesheet()
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
