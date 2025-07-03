"""Document loading page implementation."""

import tempfile
from pathlib import Path
from typing import Dict

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from biblioteq.loader import Loader


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
                _process_uploaded_files(uploaded_files)

        st.markdown("</div>", unsafe_allow_html=True)


def _process_uploaded_files(uploaded_files) -> None:
    """Process the uploaded PDF files."""
    try:
        loader = Loader()
        progress_bar: DeltaGenerator = st.progress(0)
        status_text: DeltaGenerator = st.empty()
        results: Dict[str, int] = {}

        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = Path(tmp_file.name)

            try:
                chunk_count = loader.process_pdf_file(tmp_path)
                results[uploaded_file.name] = chunk_count
            finally:
                tmp_path.unlink(missing_ok=True)

            progress_bar.progress((i + 1) / len(uploaded_files))

        loader.close_connections()
        _display_processing_results(uploaded_files, results, status_text)

    except Exception as e:
        st.error(f"Error processing documents: {str(e)}")
        st.info("Please check your database connections and try again")


def _display_processing_results(
    uploaded_files, results: Dict[str, int], status_text: DeltaGenerator
) -> None:
    """Display the results of document processing."""
    status_text.text("Processing complete!")
    st.success(f"Successfully processed {len(uploaded_files)} document(s)")

    st.markdown("### Processing Results")
    for filename, chunks in results.items():
        st.write(f"• **{filename}**: {chunks} chunks created")
