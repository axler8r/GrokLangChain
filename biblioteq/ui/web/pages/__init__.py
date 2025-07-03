"""Page components for the BiblioTeq web interface."""

# Try relative imports first, fall back to absolute imports
try:
    from .load_page import render_load_section
    from .query_page import render_query_section
except ImportError:
    from biblioteq.ui.web.pages.load_page import render_load_section
    from biblioteq.ui.web.pages.query_page import render_query_section

__all__ = ["render_load_section", "render_query_section"]
