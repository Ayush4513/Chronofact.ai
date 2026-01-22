# Qdrant as Core Component - Chronofact.ai

## Overview

**Qdrant is the primary vector search engine** for Chronofact.ai, powering all semantic search, memory storage, and recommendation capabilities. This document outlines how Qdrant is integrated as a core component following best practices from [Qdrant Demos](https://qdrant.tech/demo/), [Qdrant Articles](https://qdrant.tech/articles/), and the [Qdrant GitHub Repository](https://github.com/qdrant/qdrant).

## Qdrant Cloud Configuration

Chronofact.ai is configured to use **Qdrant Cloud** as the production vector database:

```python
from qdrant_client import QdrantClient

qdrant_client = QdrantClient(
    url="https://cb88f687-08a5-4d37-83c6-87c4b9050f72.europe-west3-0.gcp.cloud.qdrant.io:6333",
    api_key="your_api_key",
    prefer_grpc=True  # Optimized for cloud performance
)
```

## Core Collections

Qdrant stores three main collections that form the backbone of Chronofact.ai:

### 1. `x_posts` Collection
**Purpose**: Stores X (Twitter) post embeddings for semantic search

**Vector Configuration**:
- **Size**: 384 (all-MiniLM-L6-v2 embeddings)
- **Distance**: Cosine similarity
- **HNSW Index**: Optimized for fast approximate nearest neighbor search

**Payload Schema**:
```python
{
    "tweet_id": str,
    "text": str,
    "author": str,
    "timestamp": str,
    "fave_count": int,
    "retweet_count": int,
    "is_verified": bool,
    "media_urls": List[str],
    "location": Optional[str],
    "credibility_score": float
}
```

**Use Cases**:
- Semantic search for timeline generation
- Cross-modal search (text + images via CLIP)
- Credibility-based filtering

### 2. `knowledge_facts` Collection
**Purpose**: Stores verified facts for timeline verification

**Vector Configuration**:
- **Size**: 384
- **Distance**: Cosine similarity

**Payload Schema**:
```python
{
    "fact_id": str,
    "statement": str,
    "sources": List[str],
    "verification_status": str,  # "verified", "disputed", "unverified"
    "verified_at": str
}
```

**Use Cases**:
- Fact-checking against verified knowledge base
- Cross-referencing claims
- Credibility assessment

### 3. `session_memory` Collection
**Purpose**: Long-term memory with evolution (decay, reinforcement)

**Vector Configuration**:
- **Size**: 384
- **Distance**: Cosine similarity

**Payload Schema**:
```python
{
    "content": str,
    "memory_type": str,  # "interaction", "fact", "preference"
    "created_at": str,
    "last_accessed": str,
    "access_count": int,
    "relevance_score": float,  # Evolves over time
    "decay_rate": float,
    "is_consolidated": bool,
    "parent_memories": List[str]
}
```

**Use Cases**:
- Session-based personalization
- Memory evolution (temporal decay)
- User preference learning

## Qdrant Features Used

### 1. Hybrid Search
Following [Qdrant's hybrid search best practices](https://qdrant.tech/articles/):

```python
# Dense vector search + metadata filtering
results = client.search(
    collection_name="x_posts",
    query_vector=embedding,
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="credibility_score",
                range=models.Range(gte=0.7)
            ),
            models.FieldCondition(
                key="location",
                match=models.MatchValue(value="Mumbai")
            )
        ]
    ),
    limit=10
)
```

### 2. Payload Indexing
Optimized queries using payload indexes:

```python
# Fast filtering by verified status
filter = models.Filter(
    must=[
        models.FieldCondition(
            key="is_verified",
            match=models.MatchValue(value=True)
        )
    ]
)
```

### 3. Batch Operations
Efficient bulk upserts for data ingestion:

```python
client.upsert(
    collection_name="x_posts",
    points=[
        models.PointStruct(
            id=point_id,
            vector=embedding,
            payload=metadata
        )
        for point_id, embedding, metadata in batch
    ]
)
```

### 4. Multi-Vector Search
For multimodal embeddings (text + images):

```python
# Search with multiple query vectors
results = client.search_batch(
    collection_name="x_posts",
    requests=[
        models.SearchRequest(
            vector=text_embedding,
            limit=10
        ),
        models.SearchRequest(
            vector=image_embedding,
            limit=10
        )
    ]
)
```

## Performance Optimizations

Based on [Qdrant performance best practices](https://qdrant.tech/articles/vector-search-in-production):

### 1. HNSW Configuration
```python
hnsw_config=models.HnswConfigDiff(
    m=16,           # Number of bi-directional links
    ef_construct=100 # Size of dynamic candidate list
)
```

### 2. gRPC for Cloud
```python
QdrantClient(
    url=cloud_url,
    prefer_grpc=True  # Faster than REST for cloud
)
```

### 3. Query Planning
Leverages Qdrant's automatic query planning based on payload indexes.

## Integration Points

### Search Module (`src/search.py`)
- **HybridSearcher**: Primary search interface using Qdrant
- **Hybrid search**: Combines dense vectors + sparse filters
- **Re-ranking**: Post-processing with cross-encoder

### Timeline Builder (`src/timeline_builder.py`)
- Retrieves context from Qdrant collections
- Uses search results to build chronological timelines
- Filters by credibility, location, time range

### Memory Evolution (`src/memory_evolution.py`)
- Stores evolving memories in `session_memory` collection
- Implements temporal decay and reinforcement
- Consolidates similar memories

### Multimodal Search (`src/multimodal.py`)
- Uses Qdrant for cross-modal search (text ↔ images)
- CLIP embeddings stored in Qdrant
- Multi-vector search for combined queries

## Qdrant Cloud Benefits

1. **Scalability**: Handles millions of vectors
2. **Performance**: Low-latency search (<10ms)
3. **Reliability**: Managed service with 99.9% uptime
4. **Security**: Encrypted connections, API key authentication
5. **Global**: Deployed in Europe (GCP) for low latency

## Monitoring & Maintenance

### Health Checks
```python
collections = client.get_collections()
collection_info = client.get_collection("x_posts")
print(f"Points: {collection_info.points_count}")
print(f"Status: {collection_info.status}")
```

### Collection Statistics
```python
stats = client.get_collection("x_posts")
print(f"Vector size: {stats.config.params.vectors.size}")
print(f"Distance: {stats.config.params.vectors.distance}")
```

## Best Practices Implemented

Based on [Qdrant documentation](https://github.com/qdrant/qdrant):

1. ✅ **Proper vector dimensions**: 384 for text, 512 for CLIP
2. ✅ **Cosine distance**: Optimal for semantic similarity
3. ✅ **Payload indexing**: Fast metadata filtering
4. ✅ **Batch operations**: Efficient bulk upserts
5. ✅ **Connection pooling**: Reused client instances
6. ✅ **Error handling**: Graceful degradation
7. ✅ **gRPC for cloud**: Optimized protocol

## References

- [Qdrant Demos](https://qdrant.tech/demo/) - Interactive examples
- [Qdrant Articles](https://qdrant.tech/articles/) - Best practices
- [Qdrant GitHub](https://github.com/qdrant/qdrant) - Source code & docs
- [Qdrant Python Client](https://github.com/qdrant/qdrant-client) - API reference

## Conclusion

Qdrant is the **core vector search engine** for Chronofact.ai, enabling:
- Fast semantic search over millions of posts
- Real-time memory evolution
- Multimodal cross-modal search
- Scalable production deployment

All search, memory, and recommendation features depend on Qdrant as the primary data store and search engine.

