"""
Chronofact.ai - Timeline Builder Module
Builds timelines using BAML functions and Qdrant search.
Supports multimodal queries (text + images).
"""

import json
from typing import Optional, Dict, Any, List, Union
import logging

# Import BAML client (will be auto-generated)
try:
    from baml_client.baml_client import b
    from baml_client.baml_client.types import Timeline
except ImportError:
    b = None
    Timeline = None

from .config import get_config
from .search import HybridSearcher
from .ingestion import XDataIngestor

logger = logging.getLogger(__name__)

# Optional multimodal imports
try:
    from .multimodal_processor import MultimodalTweetProcessor
    from .multimodal import get_multimodal_embedder
    MULTIMODAL_AVAILABLE = True
except ImportError:
    MULTIMODAL_AVAILABLE = False
    logger.debug("Multimodal processing not available")


class TimelineBuilder:
    """Builds verified timelines using BAML and Qdrant with multimodal support."""
    
    def __init__(
        self,
        qdrant_client=None,
        search_limit: int = 10,
        use_multimodal: bool = True
    ):
        """Initialize timeline builder.
        
        Args:
            qdrant_client: QdrantClient instance
            search_limit: Default number of events to include
            use_multimodal: Enable multimodal (image) search capabilities
        """
        self.config = get_config()
        self.client = qdrant_client
        self.searcher = HybridSearcher(qdrant_client)
        self.search_limit = search_limit
        
        # Initialize multimodal processor if available
        self.use_multimodal = use_multimodal and MULTIMODAL_AVAILABLE
        self.multimodal_processor = None
        if self.use_multimodal:
            try:
                self.multimodal_processor = MultimodalTweetProcessor(
                    qdrant_client=qdrant_client,
                    use_clip=True
                )
                logger.info("Multimodal search enabled with CLIP")
            except Exception as e:
                logger.warning(f"Could not initialize multimodal processor: {e}")
                self.use_multimodal = False
        
        if b is None:
            logger.warning(
                "BAML client not available. "
                "Run 'uv run baml-cli generate' to generate client."
            )
    
    async def build_timeline(
        self,
        query: str,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        use_mock_data: bool = False
    ) -> Optional[Timeline]:
        """
        Build a verified timeline for a given query.
        
        Args:
            query: User's query or topic
            limit: Number of events to include in timeline
            filters: Optional search filters (location, min_credibility, etc.)
            use_mock_data: Whether to use mock data instead of live search
        
        Returns:
            Timeline object or None if BAML client unavailable
        """
        if b is None:
            error_msg = "Cannot build timeline: BAML client not available. Run: uv run baml-cli generate"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        if limit is None:
            limit = self.search_limit
        
        logger.info(f"Building timeline for query: {query}")
        
        try:
            # Step 1: Process query with BAML
            processed = await self._process_query(query)
            logger.info(f"Processed query: {processed.rewritten_query}")
            
            # Step 2: Retrieve context from Qdrant
            context = self._retrieve_context(
                processed.rewritten_query,
                filters,
                limit * 3  # Fetch more context
            )
            
            if not context:
                logger.warning("No context retrieved from Qdrant - attempting to ingest mock data")
                # Auto-ingest mock data if none exists
                try:
                    self._ingest_mock_data()
                    context = self._retrieve_context(
                        processed.rewritten_query,
                        filters,
                        limit * 3
                    )
                except Exception as e:
                    logger.error(f"Failed to ingest mock data: {e}")
            
            # If still no context, create a minimal context message
            if not context:
                logger.warning("No data available in Qdrant. Creating timeline with minimal context.")
                context = [{
                    "text": f"No specific data found for '{query}'. This is a placeholder timeline.",
                    "author": "system",
                    "timestamp": "2026-01-22T00:00:00Z",
                    "credibility_score": 0.5
                }]
            
            logger.info(f"Retrieved {len(context)} context items")
            
            # Step 3: Build context string
            context_str = self._format_context(context)
            
            # Step 4: Generate timeline with BAML
            try:
                timeline = await b.GenerateTimeline(
                    query=processed.rewritten_query,
                    retrieved_context=context_str,
                    num_events=limit
                )
            except Exception as baml_error:
                logger.error(f"BAML GenerateTimeline error: {baml_error}", exc_info=True)
                # Return a fallback timeline structure
                from baml_client.baml_client.types import Timeline, Event
                return Timeline(
                    topic=query,
                    events=[
                        Event(
                            timestamp="2026-01-22T00:00:00Z",
                            summary=f"Timeline generation encountered an error. Original query: {query}",
                            sources=[],
                            media=None,
                            credibility_score=0.0,
                            verified_sources=0
                        )
                    ],
                    total_sources=0,
                    avg_credibility=0.0,
                    predictions=None
                )
            
            logger.info(f"Generated timeline with {len(timeline.events)} events")
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error building timeline: {e}", exc_info=True)
            # Log more details for debugging
            logger.error(f"Query: {query}, Limit: {limit}, Filters: {filters}")
            logger.error(f"BAML available: {b is not None}")
            logger.error(f"Qdrant client available: {self.client is not None}")
            if self.client:
                try:
                    collections = self.client.get_collections()
                    logger.error(f"Qdrant collections: {[c.name for c in collections.collections]}")
                except Exception as qe:
                    logger.error(f"Failed to get collections: {qe}")
            # Re-raise the exception with more context instead of returning None
            raise RuntimeError(f"Failed to build timeline for query '{query}': {str(e)}") from e
    
    async def build_timeline_with_filters(
        self,
        query: str,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        use_mock_data: bool = False
    ) -> Optional[Timeline]:
        """
        Build timeline with specific filters.
        
        Args:
            query: User's query
            filters: Dictionary of filters:
                - time_range: str (e.g., "last 24 hours")
                - location: str
                - min_credibility: float (0.0 to 1.0)
                - include_media_only: bool
            limit: Number of events
            use_mock_data: Use mock data
        
        Returns:
            Timeline object or None
        """
        if b is None:
            return None
        
        if limit is None:
            limit = self.search_limit
        
        logger.info(f"Building filtered timeline for: {query}")
        
        try:
            # Process query
            processed = await self._process_query(query)
            
            # Retrieve filtered context
            context = self._retrieve_context(
                processed.rewritten_query,
                filters,
                limit * 3
            )
            
            context_str = self._format_context(context)
            
            # Generate timeline with filters
            timeline = await b.GenerateTimelineWithFilters(
                query=processed.rewritten_query,
                retrieved_context=context_str,
                filters=filters,
                num_events=limit
            )
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error building filtered timeline: {e}", exc_info=True)
            return None
    
    def update_timeline(
        self,
        timeline: Timeline,
        new_query: Optional[str] = None
    ) -> Optional[Timeline]:
        """
        Update an existing timeline with new information.
        
        Args:
            timeline: Existing timeline to update
            new_query: Optional new query for additional context
        
        Returns:
            Updated timeline or None
        """
        if b is None:
            return None
        
        try:
            # Retrieve new context
            if new_query:
                processed = self._process_query(new_query)
                context = self._retrieve_context(processed.rewritten_query, {}, 10)
            else:
                context = self._retrieve_context(timeline.topic, {}, 10)
            
            context_str = self._format_context(context)
            
            # Update timeline using BAML
            updated = b.UpdateTimeline(
                existing_timeline=timeline,
                new_context=context_str
            )
            
            logger.info("Updated timeline successfully")
            return updated
            
        except Exception as e:
            logger.error(f"Error updating timeline: {e}", exc_info=True)
            return None
    
    async def compare_timelines(
        self,
        timeline1: Timeline,
        timeline2: Timeline
    ) -> Optional[Dict[str, Any]]:
        """
        Compare two timelines and identify conflicts.
        
        Args:
            timeline1: First timeline
            timeline2: Second timeline to compare
        
        Returns:
            Comparison result or None
        """
        if b is None:
            return None
        
        try:
            comparison = await b.CompareTimelines(timeline1, timeline2)
            return comparison
        except Exception as e:
            logger.error(f"Error comparing timelines: {e}", exc_info=True)
            return None
    
    async def build_multimodal_timeline(
        self,
        query: str,
        image_path_or_url: Optional[str] = None,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        filter_has_images: Optional[bool] = None
    ) -> Optional[Timeline]:
        """
        Build a timeline using multimodal search (text + optional image).
        
        This enables:
        - Searching with both text and image queries
        - Finding visually similar content
        - Cross-modal matching (find text matching an image)
        
        Args:
            query: Text query
            image_path_or_url: Optional image for multimodal query
            limit: Number of events in timeline
            filters: Additional search filters
            filter_has_images: If True, only include tweets with images
        
        Returns:
            Timeline object or None
        """
        if b is None:
            error_msg = "Cannot build timeline: BAML client not available"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        if limit is None:
            limit = self.search_limit
        
        logger.info(f"Building multimodal timeline for: {query}")
        if image_path_or_url:
            logger.info(f"  with image: {image_path_or_url[:50]}...")
        
        try:
            # Step 1: Process text query
            processed = await self._process_query(query)
            
            # Step 2: Retrieve context using multimodal search
            if self.use_multimodal and self.multimodal_processor:
                context = self._retrieve_multimodal_context(
                    query=processed.rewritten_query,
                    image=image_path_or_url,
                    filters=filters,
                    limit=limit * 3,
                    filter_has_images=filter_has_images
                )
            else:
                # Fallback to text-only search
                context = self._retrieve_context(
                    processed.rewritten_query,
                    filters,
                    limit * 3
                )
            
            if not context:
                logger.warning("No multimodal context found")
                context = [{
                    "text": f"No visual or textual matches found for '{query}'",
                    "author": "system",
                    "timestamp": "2026-01-22T00:00:00Z",
                    "credibility_score": 0.5,
                    "has_images": False
                }]
            
            logger.info(f"Retrieved {len(context)} multimodal context items")
            
            # Step 3: Format context with image information
            context_str = self._format_multimodal_context(context)
            
            # Step 4: Generate timeline
            timeline = await b.GenerateTimeline(
                query=processed.rewritten_query,
                retrieved_context=context_str,
                num_events=limit
            )
            
            logger.info(f"Generated multimodal timeline with {len(timeline.events)} events")
            return timeline
            
        except Exception as e:
            logger.error(f"Error building multimodal timeline: {e}", exc_info=True)
            raise RuntimeError(f"Failed to build multimodal timeline: {str(e)}") from e
    
    def _retrieve_multimodal_context(
        self,
        query: str,
        image: Optional[str],
        filters: Optional[Dict[str, Any]],
        limit: int,
        filter_has_images: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve context using multimodal search."""
        if not self.multimodal_processor:
            return self._retrieve_context(query, filters, limit)
        
        results = self.multimodal_processor.search_multimodal(
            query=query,
            query_image=image,
            limit=limit,
            filter_has_images=filter_has_images
        )
        
        # Extract payloads with scores
        context = []
        for r in results:
            payload = r.get("payload", {})
            payload["_search_score"] = r.get("score", 0)
            context.append(payload)
        
        return context
    
    def _format_multimodal_context(self, context: List[Dict[str, Any]]) -> str:
        """Format multimodal context for BAML prompt with image info."""
        formatted_items = []
        
        for item in context:
            formatted = {
                "text": item.get("text", ""),
                "author": item.get("author_username", item.get("author", "unknown")),
                "timestamp": item.get("timestamp", ""),
                "credibility_score": item.get("credibility_score", 0.5),
                "has_images": item.get("has_images", False),
                "image_count": item.get("image_count", 0),
                "verified": item.get("author_verified", item.get("is_verified", False)),
            }
            
            # Include image captions if available
            if item.get("image_captions"):
                formatted["image_descriptions"] = item["image_captions"]
            
            # Include search relevance
            if "_search_score" in item:
                formatted["relevance_score"] = round(item["_search_score"], 3)
            
            formatted_items.append(formatted)
        
        return json.dumps(formatted_items, indent=2, ensure_ascii=False)
    
    async def search_by_image(
        self,
        image_path_or_url: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for tweets visually similar to an image.
        
        Args:
            image_path_or_url: Path to image or URL
            limit: Number of results
        
        Returns:
            List of matching tweets
        """
        if not self.use_multimodal or not self.multimodal_processor:
            logger.warning("Multimodal search not available")
            return []
        
        return self.multimodal_processor.search_by_image(
            image_path_or_url=image_path_or_url,
            limit=limit
        )
    
    async def _process_query(self, query: str):
        """Process query using BAML."""
        try:
            return await b.ProcessQuery(original_query=query)
        except Exception as e:
            logger.warning(f"Query processing failed: {e}")
            # Return fallback processed query
            class ProcessedQuery:
                original_query = query
                rewritten_query = query
                entities = []
                time_range = None
            
            return ProcessedQuery()
    
    def _retrieve_context(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        limit: int
    ) -> list:
        """Retrieve context from Qdrant."""
        results = self.searcher.search(
            query=query,
            limit=limit,
            filters=filters or {}
        )
        
        # Extract payloads
        context = []
        for result in results:
            if result.payload:
                context.append(result.payload)
        
        return context
    
    def _format_context(self, context: list) -> str:
        """Format context for BAML prompt."""
        return json.dumps(context, indent=2, ensure_ascii=False)
    
    def _ingest_mock_data(self) -> None:
        """Ingest mock data into Qdrant."""
        try:
            from .ingestion import create_sample_mock_data, XDataIngestor
            from .embeddings import get_embedding_model
            from qdrant_client import models
            import os
            import hashlib
            
            # Create mock data file if it doesn't exist
            if not os.path.exists(self.config.mock_data_path):
                create_sample_mock_data(str(self.config.mock_data_path))
            
            # Load mock data
            ingestor = XDataIngestor(use_mock=True)
            df = ingestor.load_mock_data()
            
            if df.empty:
                logger.warning("Mock data file is empty")
                return
            
            logger.info(f"Upserting {len(df)} mock records to Qdrant...")
            
            # Get embedding model
            embedding_model = get_embedding_model()
            
            # Prepare points for upsert
            points = []
            for idx, row in df.iterrows():
                # Generate embedding for text
                text = str(row.get("text", ""))
                if not text:
                    continue
                
                embedding = embedding_model.encode(text)
                
                # Generate point ID from tweet_id
                tweet_id = str(row.get("tweet_id", f"mock_{idx}"))
                point_id = int(hashlib.md5(tweet_id.encode()).hexdigest()[:8], 16)
                
                # Parse media_urls if it's a string
                media_urls = row.get("media_urls", "[]")
                if isinstance(media_urls, str):
                    try:
                        import ast
                        media_urls = ast.literal_eval(media_urls)
                    except:
                        media_urls = []
                
                # Create payload
                payload = {
                    "tweet_id": tweet_id,
                    "text": text,
                    "author": str(row.get("author", "unknown")),
                    "timestamp": str(row.get("timestamp", "")),
                    "fave_count": int(row.get("fave_count", 0)),
                    "retweet_count": int(row.get("retweet_count", 0)),
                    "is_verified": bool(row.get("is_verified", False)),
                    "media_urls": media_urls if isinstance(media_urls, list) else [],
                    "location": str(row.get("location", "")) if row.get("location") else None,
                    "credibility_score": float(row.get("credibility_score", 0.5))
                }
                
                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                )
            
            # Upsert to Qdrant
            if points and self.client:
                self.client.upsert(
                    collection_name=self.config.collection_posts,
                    points=points
                )
                logger.info(f"✅ Successfully upserted {len(points)} mock records to Qdrant")
            else:
                logger.warning("No points to upsert or Qdrant client unavailable")
                
        except Exception as e:
            logger.error(f"Error ingesting mock data: {e}", exc_info=True)


def create_timeline(
    query: str,
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None
) -> Optional[Timeline]:
    """
    Convenience function to create a timeline.
    
    Args:
        query: Search query or topic
        limit: Number of events
        filters: Optional search filters
    
    Returns:
        Timeline object or None
    """
    from .qdrant_setup import setup_collections
    
    client = setup_collections()
    builder = TimelineBuilder(client, search_limit=limit)
    
    return builder.build_timeline(
        query=query,
        limit=limit,
        filters=filters
    )
