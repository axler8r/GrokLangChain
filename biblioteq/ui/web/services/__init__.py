"""Service layer for the BiblioTeq web interface."""

# Try relative imports first, fall back to absolute imports
try:
    from .query_service import QueryService
except ImportError:
    from biblioteq.ui.web.services.query_service import QueryService

__all__ = ["QueryService"]
