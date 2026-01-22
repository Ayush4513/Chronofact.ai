"""
Chronofact.ai - Qdrant Setup Module
Creates and manages Qdrant collections.
"""

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
from typing import Optional
import logging

from .config import get_config, AppConfig
from .embeddings import get_embedding_model

logger = logging.getLogger(__name__)


def setup_collections(client: Optional[QdrantClient] = None) -> QdrantClient:
    """
    Create Qdrant collections for XTimeline.
    
    Args:
        client: Optional QdrantClient instance. Creates new one if not provided.
    
    Returns:
        Configured QdrantClient instance
    """
    config = get_config()
    
    if client is None:
        client = create_qdrant_client(config)
    
    embedding_model = get_embedding_model()
    vector_size = embedding_model.get_vector_size()
    
    logger.info(f"Setting up collections with vector size: {vector_size}")
    
    # Create posts collection
    _create_collection_if_not_exists(
        client,
        config.collection_posts,
        vector_size,
        "X posts with text, metadata, and credibility scores"
    )
    
    # Create knowledge facts collection
    _create_collection_if_not_exists(
        client,
        config.collection_knowledge,
        vector_size,
        "Verified facts for timeline verification"
    )
    
    # Create session memory collection
    _create_collection_if_not_exists(
        client,
        config.collection_memory,
        vector_size,
        "User query history and session memory"
    )
    
    logger.info("All collections ready")
    
    return client


def _create_collection_if_not_exists(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
    description: str
) -> None:
    """
    Create a Qdrant collection if it doesn't exist.
    
    Args:
        client: QdrantClient instance
            collection_name: Name of the collection
            vector_size: Dimension of vectors
            description: Collection description
    """
    try:
        if client.collection_exists(collection_name):
            logger.info(f"Collection '{collection_name}' already exists")
            return
        
        logger.info(f"Creating collection: {collection_name}")
        
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
                hnsw_config=models.HnswConfigDiff(
                    m=16,
                    ef_construct=100
                )
            ),
            optimizers_config=models.OptimizersConfigDiff(
                indexing_threshold=20000
            ),
            replication_factor=1,
            write_consistency_factor=1
        )
        
        logger.info(f"✓ Created collection: {collection_name}")
        
    except UnexpectedResponse as e:
        logger.error(f"Error creating collection '{collection_name}': {e}")
        raise


def create_qdrant_client(config: Optional[AppConfig] = None) -> QdrantClient:
    """
    Create and configure Qdrant client for different deployment modes.

    Args:
        config: Optional AppConfig. Uses default if not provided.

    Returns:
        Configured QdrantClient instance
    """
    if config is None:
        config = get_config()

    qdrant_config = config.qdrant
    mode = qdrant_config.mode

    try:
        if mode == "memory":
            # In-memory mode (no persistence)
            client = QdrantClient(":memory:")
            logger.info("Using in-memory Qdrant (data will not persist)")

        elif mode == "local":
            # Local persistent storage
            if qdrant_config.storage_path:
                client = QdrantClient(path=qdrant_config.storage_path)
                logger.info(f"Using local persistent Qdrant at: {qdrant_config.storage_path}")
            else:
                client = QdrantClient(":memory:")
                logger.warning("No storage path provided for local mode, using in-memory")

        elif mode == "docker":
            # Docker container mode
            protocol = "https" if qdrant_config.https else "http"
            url = f"{protocol}://{qdrant_config.host}:{qdrant_config.port}"

            client = QdrantClient(
                url=url,
                api_key=qdrant_config.api_key,
                timeout=qdrant_config.timeout,
                prefer_grpc=True
            )
            logger.info(f"Using Docker Qdrant at: {url}")

        elif mode == "cloud":
            # Qdrant Cloud mode
            if qdrant_config.url:
                client = QdrantClient(
                    url=qdrant_config.url,
                    api_key=qdrant_config.api_key,
                    timeout=qdrant_config.timeout,
                    prefer_grpc=True
                )
                logger.info(f"Using Qdrant Cloud at: {qdrant_config.url}")
            else:
                raise ValueError("QDRANT_URL is required for cloud mode")

        elif mode == "hybrid":
            # Hybrid mode (REST + gRPC)
            protocol = "https" if qdrant_config.https else "http"
            url = f"{protocol}://{qdrant_config.host}:{qdrant_config.port}"

            client = QdrantClient(
                url=url,
                api_key=qdrant_config.api_key,
                timeout=qdrant_config.timeout,
                prefer_grpc=False,  # Use both REST and gRPC
                grpc_port=qdrant_config.grpc_port
            )
            logger.info(f"Using hybrid Qdrant (REST + gRPC) at: {url}")

        else:
            raise ValueError(f"Unknown Qdrant mode: {mode}")

        # Test connection
        try:
            collections = client.get_collections()
            logger.info(f"Successfully connected to Qdrant. Found {len(collections.collections)} collections.")
        except Exception as e:
            logger.warning(f"Could not test Qdrant connection: {e}")

        return client

    except Exception as e:
        logger.error(f"Failed to create Qdrant client: {e}")
        raise


def delete_collection(client: QdrantClient, collection_name: str) -> None:
    """
    Delete a Qdrant collection.
    
    Args:
        client: QdrantClient instance
        collection_name: Name of collection to delete
    """
    try:
        if client.collection_exists(collection_name):
            client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
        else:
            logger.warning(f"Collection '{collection_name}' does not exist")
    except UnexpectedResponse as e:
        logger.error(f"Error deleting collection '{collection_name}': {e}")


def get_collection_info(client: QdrantClient, collection_name: str) -> Optional[dict]:
    """
    Get information about a collection.
    
    Args:
        client: QdrantClient instance
        collection_name: Name of collection
    
    Returns:
        Collection info dict or None if collection doesn't exist
    """
    try:
        info = client.get_collection(collection_name)
        return {
            "name": info.config.params.vectors.size,
            "vector_size": info.config.params.vectors.size,
            "points_count": info.points_count,
            "status": info.status
        }
    except UnexpectedResponse as e:
        if "not found" in str(e).lower():
            return None
        raise


def list_collections(client: QdrantClient) -> list[str]:
    """
    List all collections in Qdrant.
    
    Args:
        client: QdrantClient instance
    
    Returns:
        List of collection names
    """
    collections = client.get_collections()
    return [col.name for col in collections.collections]
