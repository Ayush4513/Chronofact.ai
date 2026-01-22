"""
Chronofact.ai
AI-powered fact-based news service using Qdrant and BAML.
"""

__version__ = "0.1.0"
__author__ = "Ayush4513"

from .config import get_config, AppConfig, QdrantConfig
from .embeddings import EmbeddingModel, get_embedding_model
from .qdrant_setup import (
    setup_collections,
    create_qdrant_client,
    delete_collection,
    get_collection_info,
    list_collections
)
from .ingestion import XDataIngestor, create_sample_mock_data
from .search import HybridSearcher
from .timeline_builder import TimelineBuilder, create_timeline

__all__ = [
    "get_config",
    "AppConfig",
    "QdrantConfig",
    "EmbeddingModel",
    "get_embedding_model",
    "setup_collections",
    "create_qdrant_client",
    "delete_collection",
    "get_collection_info",
    "list_collections",
    "XDataIngestor",
    "create_sample_mock_data",
    "HybridSearcher",
    "TimelineBuilder",
    "create_timeline",
]
