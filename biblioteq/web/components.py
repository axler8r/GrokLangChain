"""Reusable UI components for the BiblioTeq web interface."""

from pathlib import Path
import streamlit as st


def apply_stylesheet() -> None:
    """Apply Material Design-inspired CSS styles to the Streamlit app."""
    css_path: Path = Path(__file__).parent / "static/axler8r.css"

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
