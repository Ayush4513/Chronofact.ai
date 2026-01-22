"""
Chronofact.ai - Timeline Builder Module
Builds timelines using BAML functions and Qdrant search.
"""

import json
from typing import Optional, Dict, Any
import logging

# Import BAML client (will be auto-generated)
try:
    from baml_client.sync_client import b
    from baml_client.types import Timeline
except ImportError:
    b = None
    Timeline = None

from .config import get_config
from .search import HybridSearcher
from .ingestion import XDataIngestor

logger = logging.getLogger(__name__)


class TimelineBuilder:
    """Builds verified timelines using BAML and Qdrant."""
    
    def __init__(
        self,
        qdrant_client=None,
        search_limit: int = 10
    ):
        """Initialize timeline builder.
        
        Args:
            qdrant_client: QdrantClient instance
            search_limit: Default number of events to include
        """
        self.config = get_config()
        self.client = qdrant_client
        self.searcher = HybridSearcher(qdrant_client)
        self.search_limit = search_limit
        
        if b is None:
            logger.warning(
                "BAML client not available. "
                "Run 'uv run baml-cli generate' to generate client."
            )
    
    def build_timeline(
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
            logger.error("Cannot build timeline: BAML client not available")
            return None
        
        if limit is None:
            limit = self.search_limit
        
        logger.info(f"Building timeline for query: {query}")
        
        try:
            # Step 1: Process query with BAML
            processed = self._process_query(query)
            logger.info(f"Processed query: {processed.rewritten_query}")
            
            # Step 2: Retrieve context from Qdrant
            context = self._retrieve_context(
                processed.rewritten_query,
                filters,
                limit * 3  # Fetch more context
            )
            
            if not context:
                logger.warning("No context retrieved from Qdrant")
                # Try ingesting mock data
                if use_mock_data:
                    self._ingest_mock_data()
                    context = self._retrieve_context(
                        processed.rewritten_query,
                        filters,
                        limit * 3
                    )
            
            logger.info(f"Retrieved {len(context)} context items")
            
            # Step 3: Build context string
            context_str = self._format_context(context)
            
            # Step 4: Generate timeline with BAML
            timeline = b.GenerateTimeline(
                query=processed.rewritten_query,
                retrieved_context=context_str,
                num_events=limit
            )
            
            logger.info(f"Generated timeline with {len(timeline.events)} events")
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error building timeline: {e}", exc_info=True)
            return None
    
    def build_timeline_with_filters(
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
            processed = self._process_query(query)
            
            # Retrieve filtered context
            context = self._retrieve_context(
                processed.rewritten_query,
                filters,
                limit * 3
            )
            
            context_str = self._format_context(context)
            
            # Generate timeline with filters
            timeline = b.GenerateTimelineWithFilters(
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
    
    def compare_timelines(
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
            comparison = b.CompareTimelines(timeline1, timeline2)
            return comparison
        except Exception as e:
            logger.error(f"Error comparing timelines: {e}", exc_info=True)
            return None
    
    def _process_query(self, query: str):
        """Process query using BAML."""
        try:
            return b.ProcessQuery(original_query=query)
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
            ingestor = XDataIngestor(use_mock=True)
            df = ingestor.load_mock_data()
            
            if not df.empty:
                # Upsert to Qdrant
                from .ingestion import create_sample_mock_data
                import os
                if not os.path.exists(self.config.mock_data_path):
                    create_sample_mock_data(self.config.mock_data_path)
                    df = ingestor.load_mock_data()
                
                # TODO: Implement actual upsert logic
                logger.info(f"Loaded {len(df)} mock records")
        except Exception as e:
            logger.error(f"Error ingesting mock data: {e}")


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
