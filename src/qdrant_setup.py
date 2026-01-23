"""
Chronofact.ai - Qdrant Setup Module
Creates and manages Qdrant collections with multimodal vector support.
"""

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
from typing import Optional, Dict
import logging

from .config import get_config, AppConfig
from .embeddings import get_embedding_model

logger = logging.getLogger(__name__)

# Vector dimensions
TEXT_VECTOR_SIZE = 384  # all-MiniLM-L6-v2
CLIP_VECTOR_SIZE = 512  # clip-ViT-B-32


def setup_collections(client: Optional[QdrantClient] = None) -> QdrantClient:
    """
    Create Qdrant collections for XTimeline with multimodal support.
    
    Args:
        client: Optional QdrantClient instance. Creates new one if not provided.
    
    Returns:
        Configured QdrantClient instance
    """
    config = get_config()
    
    if client is None:
        client = create_qdrant_client(config)
    
    embedding_model = get_embedding_model()
    text_vector_size = embedding_model.get_vector_size()
    
    logger.info(f"Setting up collections with text vector size: {text_vector_size}, CLIP size: {CLIP_VECTOR_SIZE}")
    
    # Create posts collection with multimodal vectors
    _create_multimodal_collection_if_not_exists(
        client,
        config.collection_posts,
        text_vector_size,
        "X posts with text, images, metadata, and credibility scores"
    )
    
    # Create knowledge facts collection (text-only is fine)
    _create_collection_if_not_exists(
        client,
        config.collection_knowledge,
        text_vector_size,
        "Verified facts for timeline verification"
    )
    
    # Create session memory collection (text-only is fine)
    _create_collection_if_not_exists(
        client,
        config.collection_memory,
        text_vector_size,
        "User query history and session memory"
    )
    
    logger.info("All collections ready")
    
    return client


def _create_multimodal_collection_if_not_exists(
    client: QdrantClient,
    collection_name: str,
    text_vector_size: int,
    description: str
) -> None:
    """
    Create a Qdrant collection with multiple named vectors for multimodal data.
    
    Vectors:
        - "text": Text embedding (all-MiniLM-L6-v2, 384 dim)
        - "multimodal": Combined text+image CLIP embedding (512 dim)
        - "image": Image-only CLIP embedding for cross-modal search (512 dim)
    
    Args:
        client: QdrantClient instance
        collection_name: Name of the collection
        text_vector_size: Dimension of text vectors
        description: Collection description
    """
    try:
        if client.collection_exists(collection_name):
            logger.info(f"Collection '{collection_name}' already exists")
            # Check if it has multimodal vectors, if not we may need to recreate
            return
        
        logger.info(f"Creating multimodal collection: {collection_name}")
        
        # Named vectors configuration for multimodal support
        vectors_config = {
            "text": models.VectorParams(
                size=text_vector_size,
                distance=models.Distance.COSINE,
                hnsw_config=models.HnswConfigDiff(m=16, ef_construct=100)
            ),
            "multimodal": models.VectorParams(
                size=CLIP_VECTOR_SIZE,
                distance=models.Distance.COSINE,
                hnsw_config=models.HnswConfigDiff(m=16, ef_construct=100)
            ),
            "image": models.VectorParams(
                size=CLIP_VECTOR_SIZE,
                distance=models.Distance.COSINE,
                hnsw_config=models.HnswConfigDiff(m=16, ef_construct=100)
            ),
        }
        
        client.create_collection(
            collection_name=collection_name,
            vectors_config=vectors_config,
            optimizers_config=models.OptimizersConfigDiff(
                indexing_threshold=20000
            ),
            replication_factor=1,
            write_consistency_factor=1
        )
        
        # Create payload indexes for efficient filtering
        _create_payload_indexes(client, collection_name)
        
        logger.info(f"✓ Created multimodal collection: {collection_name}")
        
    except UnexpectedResponse as e:
        logger.error(f"Error creating collection '{collection_name}': {e}")
        raise


def _create_payload_indexes(client: QdrantClient, collection_name: str) -> None:
    """Create payload field indexes for efficient filtering."""
    try:
        # Index commonly filtered fields
        indexed_fields = [
            ("has_images", models.PayloadSchemaType.BOOL),
            ("author_verified", models.PayloadSchemaType.BOOL),
            ("credibility_score", models.PayloadSchemaType.FLOAT),
            ("location", models.PayloadSchemaType.KEYWORD),
            ("timestamp", models.PayloadSchemaType.DATETIME),
        ]
        
        for field_name, field_type in indexed_fields:
            try:
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=field_type
                )
                logger.debug(f"Created index for field: {field_name}")
            except Exception as e:
                logger.debug(f"Index for {field_name} may already exist: {e}")
                
    except Exception as e:
        logger.warning(f"Could not create payload indexes: {e}")


def _create_collection_if_not_exists(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
    description: str
) -> None:
    """
    Create a standard Qdrant collection if it doesn't exist.
    
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
            # Docker container mode - no API key needed for local Docker
            protocol = "https" if qdrant_config.https else "http"
            url = f"{protocol}://{qdrant_config.host}:{qdrant_config.port}"

            # Docker Qdrant doesn't require API key for local connections
            client_kwargs = {
                "url": url,
                "timeout": qdrant_config.timeout,
                "prefer_grpc": True
            }
            # Only add API key if explicitly provided (for secured Docker setups)
            if qdrant_config.api_key:
                client_kwargs["api_key"] = qdrant_config.api_key
            
            client = QdrantClient(**client_kwargs)
            logger.info(f"Using Docker Qdrant at: {url}")

        elif mode == "cloud":
            # Qdrant Cloud mode - Core component for vector search
            if qdrant_config.url:
                # Ensure URL has proper format
                url = qdrant_config.url
                if not url.startswith(("http://", "https://")):
                    url = f"https://{url}"
                
                client = QdrantClient(
                    url=url,
                    api_key=qdrant_config.api_key,
                    timeout=qdrant_config.timeout,
                    prefer_grpc=True  # Use gRPC for better performance with Qdrant Cloud
                )
                logger.info(f"✅ Connected to Qdrant Cloud (Core Component) at: {url}")
                logger.info("Qdrant is the primary vector search engine for Chronofact.ai")
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
