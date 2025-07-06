"""Configuration module for BiblioTeq."""

import os
from abc import ABC

from attr import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Configuration:
    """Configuration for database and service connections.

    Attributes:
        mongo_uri: MongoDB connection URI.
        mongo_db: MongoDB database name.
        mongo_collection: MongoDB collection name.
        qdrant_host: Qdrant service host.
        qdrant_port: Qdrant service port.
        qdrant_collection: Qdrant collection name.
        openai_api_key: OpenAI API key.
        openai_model: OpenAI model name for text generation.
        openai_encoding_model: OpenAI encoding model name.
        pdf_path: Path to PDF files.
    """

    mongo_uri: str = os.getenv("MONGO_URI", "UNDEFINED")
    mongo_db: str = os.getenv("MONGO_DB", "UNDEFINED")
    mongo_collection: str = os.getenv("MONGO_COLLECTION", "UNDEFINED")
    qdrant_host: str = os.getenv("QDRANT_HOST", "UNDEFINED")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "-1"))
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "UNDEFINED")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "UNDEFINED")
    openai_model: str = os.getenv("OPENAI_MODEL", "UNDEFINED")
    openai_encoding_model: str = os.getenv("OPENAI_ENCODING_MODEL", "UNDEFINED")
    pdf_path: str = os.getenv("PDF_PATH", "UNDEFINED")

    @classmethod
    def get_instance(cls) -> "Configuration":
        """Returns a singleton instance of Configuration."""
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance


class Configurable(ABC):
    """Abstract base class for configurable components.

    This class provides a method to get the configuration instance.
    """

    def __init__(self) -> None:
        """Initializes the Configurable instance."""
        self._config: Configuration = Configuration.get_instance()
