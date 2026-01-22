"""
Chronofact.ai Configuration Module
Manages environment variables, Qdrant configuration, and API settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class QdrantConfig:
    """Qdrant client configuration."""

    def __init__(self):
        # Qdrant connection mode
        self.mode = os.getenv("QDRANT_MODE", "local").lower()  # local, docker, cloud, memory

        # Local mode settings
        self.storage_path = os.getenv("QDRANT_STORAGE_PATH", "./data/qdrant")

        # Remote mode settings
        self.host = os.getenv("QDRANT_HOST", "localhost")
        self.port = int(os.getenv("QDRANT_PORT", "6333"))
        self.url = os.getenv("QDRANT_URL")  # For cloud deployments

        # Authentication
        self.api_key = os.getenv("QDRANT_API_KEY")
        self.username = os.getenv("QDRANT_USERNAME")
        self.password = os.getenv("QDRANT_PASSWORD")

        # Connection settings
        self.timeout = int(os.getenv("QDRANT_TIMEOUT", "30"))
        self.https = os.getenv("QDRANT_HTTPS", "false").lower() == "true"
        self.grpc_port = int(os.getenv("QDRANT_GRPC_PORT", "6334"))

        # Advanced settings
        self.prefetch = int(os.getenv("QDRANT_PREFETCH", "10"))
        self.retry_on_failure = os.getenv("QDRANT_RETRY_ON_FAILURE", "true").lower() == "true"
        self.max_retries = int(os.getenv("QDRANT_MAX_RETRIES", "3"))


class GoogleAIConfig:
    """Google AI API configuration for BAML."""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY", "")


class EmbeddingConfig:
    """Sentence transformer embedding configuration."""
    
    def __init__(self):
        self.model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.device = os.getenv("EMBEDDING_DEVICE", "cpu")
        self.batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))


class SeleniumConfig:
    """Selenium web scraping configuration."""
    
    def __init__(self):
        self.headless = os.getenv("SELENIUM_HEADLESS", "true").lower() == "true"
        self.timeout = int(os.getenv("SELENIUM_TIMEOUT", "30"))
        self.max_posts = int(os.getenv("SELENIUM_MAX_POSTS", "100"))


class AppConfig:
    """Main application configuration."""

    def __init__(self):
        self.qdrant = QdrantConfig()
        self.google_ai = GoogleAIConfig()
        self.embedding = EmbeddingConfig()
        self.selenium = SeleniumConfig()
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        self.collection_posts = "x_posts"
        self.collection_knowledge = "knowledge_facts"
        self.collection_memory = "session_memory"

        self.default_search_limit = int(os.getenv("SEARCH_LIMIT", "10"))
        self.min_credibility = float(os.getenv("MIN_CREDIBILITY", "0.3"))

        import pathlib
        self.data_dir = pathlib.Path(os.getenv("DATA_DIR", "./data"))
        self.mock_data_path = pathlib.Path(os.getenv("MOCK_DATA_PATH", "./data/sample_x_data.csv"))


def get_config() -> AppConfig:
    """Get application configuration."""
    return AppConfig()


def validate_config(config: AppConfig) -> bool:
    """Validate required configuration values."""

    if not config.google_ai.api_key:
        print("Warning: GOOGLE_API_KEY not set. BAML features will be disabled.")

    config.data_dir.mkdir(parents=True, exist_ok=True)

    return True
