"""
BiblioTeq Web Frontend

A Streamlit-based web interface for uploading PDF documents and querying 
book content using natural language.
"""

import streamlit as st
import tempfile
from pathlib import Path

# Import the loader module
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from biblioteq.loader import Loader


def apply_material_design_styles() -> None:
    """Apply Material Design-inspired CSS styles to the Streamlit app."""
    # Load CSS from external file
    css_path = Path(__file__).parent / "styles.css"
    
    with open(css_path, "r") as css_file:
        css_content = css_file.read()
    
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def render_header() -> None:
    """Render the main application header."""
    st.markdown("""
    <div class="main-header">
        <h1>BiblioTeq</h1>
        <p>Document Management and Intelligent Query System</p>
    </div>
    """, unsafe_allow_html=True)


def render_load_section() -> None:
    """Render the document loading interface."""
    st.markdown('<h2 class="section-header">Load Documents</h2>', 
                unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Select PDF files to upload",
            type=['pdf'],
            accept_multiple_files=True,
            help="Choose one or more PDF files to add to your library"
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
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    results = {}
                    
                    for i, uploaded_file in enumerate(uploaded_files):
                        status_text.text(f"Processing {uploaded_file.name}...")
                        
                        # Save uploaded file to temporary location
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
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
                    st.success(f"Successfully processed {len(uploaded_files)} document(s)")
                    
                    # Show processing details
                    st.markdown("### Processing Results")
                    for filename, chunks in results.items():
                        st.write(f"• **{filename}**: {chunks} chunks created")
                        
                except Exception as e:
                    st.error(f"Error processing documents: {str(e)}")
                    st.info("Please check your database connections and try again")
        
        st.markdown('</div>', unsafe_allow_html=True)


def render_query_section() -> None:
    """Render the document query interface."""
    st.markdown('<h2 class="section-header">Query Library</h2>', 
                unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="query-section">', unsafe_allow_html=True)
        
        query = st.text_area(
            "Enter your question",
            placeholder="Ask a question about your documents...",
            height=100,
            help="Use natural language to query your document library"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Search", key="search_btn", disabled=not query.strip()):
                # TODO: Implement agent query functionality
                with st.spinner("Searching your library..."):
                    st.session_state.last_query = query
                    st.session_state.query_result = "Query functionality will be integrated with the agent module"
        
        if hasattr(st.session_state, 'query_result'):
            st.markdown("### Response")
            st.write(st.session_state.query_result)
        
        st.markdown('</div>', unsafe_allow_html=True)


def main() -> None:
    """Main application entry point."""
    st.set_page_config(
        page_title="BiblioTeq",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    apply_material_design_styles()
    render_header()
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## Navigation")
        
        action = st.radio(
            "Select Action",
            ["Load", "Query"],
            index=0,
            help="Choose whether to load new documents or query existing ones"
        )
    
    # Main content area
    if action == "Load":
        render_load_section()
    elif action == "Query":
        render_query_section()


if __name__ == "__main__":
    main()
