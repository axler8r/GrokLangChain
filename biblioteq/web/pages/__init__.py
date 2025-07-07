"""Page components for the BiblioTeq web interface."""

from biblioteq.web.pages.load_page import render_load_section
from biblioteq.web.pages.query_page import render_query_section

__all__: list[str] = ["render_load_section", "render_query_section"]
