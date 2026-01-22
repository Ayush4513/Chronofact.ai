"""
Chronofact.ai - Search Module
Implements hybrid search combining dense, sparse, and metadata filtering.
"""

from qdrant_client import QdrantClient, models
from typing import List, Dict, Optional, Any
import logging

from .config import get_config
from .embeddings import get_embedding_model

logger = logging.getLogger(__name__)


class HybridSearcher:
    """Hybrid search combining semantic and keyword search."""
    
    def __init__(self, qdrant_client: Optional[QdrantClient] = None):
        """Initialize hybrid searcher.
        
        Args:
            qdrant_client: Optional QdrantClient instance
        """
        self.config = get_config()
        self.client = qdrant_client
        self.embedding_model = get_embedding_model()
    
    def search(
        self,
        query: str,
        collection_name: Optional[str] = None,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None
    ) -> List[models.ScoredPoint]:
        """
        Perform hybrid search in Qdrant.
        
        Args:
            query: Search query text
            collection_name: Name of collection to search
            limit: Maximum number of results
            filters: Metadata filters dictionary
            score_threshold: Minimum similarity score
        
        Returns:
            List of scored points
        """
        if collection_name is None:
            collection_name = self.config.collection_posts
        if limit is None:
            limit = self.config.default_search_limit
        if filters is None:
            filters = {}
        
        logger.info(f"Searching for: {query} (limit: {limit})")
        
        # Generate query embedding
        query_vector = self.embedding_model.encode(query)
        
        # Build Qdrant filter
        qdrant_filter = self._build_filter(filters)
        
        # Perform search
        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=limit * 2,  # Fetch more for re-ranking
                with_payload=True,
                with_vectors=False
            )
            
            # Apply post-processing
            filtered_results = self._post_process(
                results,
                score_threshold,
                limit
            )
            
            logger.info(f"Found {len(filtered_results)} results after filtering")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def search_with_rerank(
        self,
        query: str,
        collection_name: Optional[str] = None,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[models.ScoredPoint]:
        """
        Perform search with cross-encoder re-ranking.
        
        Args:
            query: Search query text
            collection_name: Name of collection to search
            limit: Maximum number of results
            filters: Metadata filters dictionary
        
        Returns:
            Re-ranked list of scored points
        """
        # Initial search
        initial_results = self.search(
            query=query,
            collection_name=collection_name,
            limit=limit * 3 if limit else 30,
            filters=filters,
            score_threshold=None
        )
        
        if not initial_results:
            return []
        
        # Re-rank using semantic similarity to query
        reranked = self._rerank(query, initial_results)
        
        limit = limit or self.config.default_search_limit
        return reranked[:limit]
    
    def multi_vector_search(
        self,
        query_vectors: List[List[float]],
        collection_name: str,
        limit: int = 10
    ) -> List[models.ScoredPoint]:
        """
        Search using multiple query vectors (ensembles).
        
        Args:
            query_vectors: List of query vectors
            collection_name: Name of collection
            limit: Maximum number of results
        
        Returns:
            List of scored points
        """
        try:
            results = self.client.search_batch(
                collection_name=collection_name,
                requests=[
                    models.SearchRequest(
                        vector=vec,
                        limit=limit,
                        with_payload=True,
                        with_vectors=False
                    )
                    for vec in query_vectors
                ]
            )
            
            # Combine and deduplicate results
            combined = self._combine_results(results)
            return combined[:limit]
            
        except Exception as e:
            logger.error(f"Multi-vector search error: {e}")
            return []
    
    def _build_filter(
        self,
        filters: Dict[str, Any]
    ) -> Optional[models.Filter]:
        """
        Build Qdrant filter from dictionary.
        
        Args:
            filters: Filter dictionary with keys like:
                - location: string match
                - min_credibility: float comparison
                - is_verified: boolean match
                - time_range: tuple of (start, end) timestamps
        
        Returns:
            Qdrant Filter object or None
        """
        if not filters:
            return None
        
        must_conditions = []
        
        # Location filter
        if "location" in filters and filters["location"]:
            must_conditions.append(
                models.FieldCondition(
                    key="location",
                    match=models.MatchValue(value=filters["location"])
                )
            )
        
        # Credibility filter
        if "min_credibility" in filters:
            must_conditions.append(
                models.FieldCondition(
                    key="credibility_score",
                    range=models.Range(
                        gte=float(filters["min_credibility"])
                    )
                )
            )
        
        # Verified filter
        if "is_verified" in filters:
            must_conditions.append(
                models.FieldCondition(
                    key="is_verified",
                    match=models.MatchValue(value=bool(filters["is_verified"]))
                )
            )
        
        # Time range filter
        if "time_range" in filters:
            start_time, end_time = filters["time_range"]
            must_conditions.append(
                models.FieldCondition(
                    key="timestamp",
                    range=models.Range(
                        gte=start_time,
                        lte=end_time
                    )
                )
            )
        
        if must_conditions:
            return models.Filter(must=must_conditions)
        return None
    
    def _post_process(
        self,
        results: List[models.ScoredPoint],
        score_threshold: Optional[float],
        limit: int
    ) -> List[models.ScoredPoint]:
        """
        Post-process search results.
        
        Args:
            results: Raw search results
            score_threshold: Minimum score threshold
            limit: Maximum number to return
        
        Returns:
            Filtered and limited results
        """
        filtered = results
        
        # Apply score threshold
        if score_threshold is not None:
            filtered = [r for r in filtered if r.score >= score_threshold]
        
        # Sort by score descending
        filtered = sorted(filtered, key=lambda x: x.score, reverse=True)
        
        # Apply limit
        return filtered[:limit]
    
    def _rerank(
        self,
        query: str,
        results: List[models.ScoredPoint]
    ) -> List[models.ScoredPoint]:
        """
        Re-rank results using semantic similarity.
        
        Args:
            query: Original query text
            results: Initial search results
        
        Returns:
            Re-ranked results
        """
        for result in results:
            if result.payload and "text" in result.payload:
                text = result.payload["text"]
                new_score = self.embedding_model.similarity(query, text)
                result.score = (result.score + new_score) / 2  # Average
        
        return sorted(results, key=lambda x: x.score, reverse=True)
    
    def _combine_results(
        self,
        batch_results: List[List[models.ScoredPoint]]
    ) -> List[models.ScoredPoint]:
        """
        Combine results from multiple search requests.
        
        Args:
            batch_results: List of result lists from multiple vectors
        
        Returns:
            Combined and deduplicated results
        """
        seen_ids = set()
        combined = []
        
        for results in batch_results:
            for result in results:
                if result.id not in seen_ids:
                    seen_ids.add(result.id)
                    combined.append(result)
        
        return sorted(combined, key=lambda x: x.score, reverse=True)
    
    def get_similar_posts(
        self,
        post_id: str,
        collection_name: Optional[str] = None,
        limit: int = 5
    ) -> List[models.ScoredPoint]:
        """
        Find posts similar to a given post.
        
        Args:
            post_id: ID of the reference post
            collection_name: Name of collection
            limit: Maximum number of similar posts
        
        Returns:
            List of similar posts
        """
        if collection_name is None:
            collection_name = self.config.collection_posts
        
        try:
            # Get the post vector
            post = self.client.retrieve(
                collection_name=collection_name,
                ids=[post_id],
                with_vectors=True
            )
            
            if not post:
                logger.warning(f"Post {post_id} not found")
                return []
            
            post_vector = post[0].vector
            
            # Search for similar posts
            results = self.client.search(
                collection_name=collection_name,
                query_vector=post_vector,
                limit=limit + 1,  # +1 to exclude self
                with_payload=True
            )
            
            # Filter out the original post
            similar = [r for r in results if r.id != post_id]
            
            return similar[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar posts: {e}")
            return []
