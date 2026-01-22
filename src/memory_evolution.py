"""
Chronofact.ai - Memory Evolution Module
Implements evolving memory with decay, reinforcement, and updates.
Addresses the hackathon requirement for "Memory Beyond a Single Prompt".
"""

from qdrant_client import QdrantClient, models
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import uuid
import math

logger = logging.getLogger(__name__)


class MemoryEvolution:
    """
    Manages evolving memory in Qdrant with:
    - Temporal decay (older memories lose relevance)
    - Reinforcement (frequently accessed memories gain strength)
    - Updates (memories can be modified with new information)
    - Consolidation (merge similar memories)
    """
    
    # Memory metadata fields
    CREATED_AT = "created_at"
    LAST_ACCESSED = "last_accessed"
    ACCESS_COUNT = "access_count"
    RELEVANCE_SCORE = "relevance_score"
    DECAY_RATE = "decay_rate"
    IS_CONSOLIDATED = "is_consolidated"
    PARENT_MEMORIES = "parent_memories"
    
    # Default parameters
    DEFAULT_DECAY_RATE = 0.05  # 5% decay per day
    DEFAULT_REINFORCEMENT = 0.1  # 10% boost per access
    DECAY_THRESHOLD = 0.2  # Memories below this are candidates for deletion
    CONSOLIDATION_SIMILARITY = 0.85  # Similarity threshold for merging
    
    def __init__(
        self,
        client: QdrantClient,
        collection_name: str = "session_memory",
        decay_rate: float = DEFAULT_DECAY_RATE,
        reinforcement_factor: float = DEFAULT_REINFORCEMENT
    ):
        """
        Initialize memory evolution manager.
        
        Args:
            client: Qdrant client instance
            collection_name: Name of memory collection
            decay_rate: Daily decay rate (0.0 to 1.0)
            reinforcement_factor: Relevance boost per access (0.0 to 1.0)
        """
        self.client = client
        self.collection_name = collection_name
        self.decay_rate = decay_rate
        self.reinforcement_factor = reinforcement_factor
    
    def store_memory(
        self,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        initial_relevance: float = 1.0,
        memory_type: str = "interaction"
    ) -> str:
        """
        Store a new memory with evolution metadata.
        
        Args:
            content: Memory content/text
            embedding: Vector embedding
            metadata: Additional metadata
            initial_relevance: Starting relevance score (0.0 to 1.0)
            memory_type: Type of memory ('interaction', 'fact', 'preference')
        
        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        payload = {
            "content": content,
            "memory_type": memory_type,
            self.CREATED_AT: now,
            self.LAST_ACCESSED: now,
            self.ACCESS_COUNT: 0,
            self.RELEVANCE_SCORE: initial_relevance,
            self.DECAY_RATE: self.decay_rate,
            self.IS_CONSOLIDATED: False,
            self.PARENT_MEMORIES: [],
            **(metadata or {})
        }
        
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=memory_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            logger.info(f"Stored memory {memory_id} with relevance {initial_relevance}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
    
    def retrieve_and_reinforce(
        self,
        query_embedding: List[float],
        limit: int = 10,
        min_relevance: float = 0.0,
        apply_decay: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories and reinforce accessed ones.
        
        This is the core memory access method that:
        1. Applies temporal decay to all retrieved memories
        2. Reinforces memories that match the query
        3. Returns memories sorted by relevance
        
        Args:
            query_embedding: Query vector
            limit: Maximum memories to return
            min_relevance: Minimum relevance threshold
            apply_decay: Whether to apply temporal decay
        
        Returns:
            List of memory dicts with updated relevance
        """
        try:
            # Search for relevant memories
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit * 2,  # Fetch more for filtering
                with_payload=True,
                with_vectors=True
            )
            
            memories = []
            points_to_update = []
            
            for result in results:
                if not result.payload:
                    continue
                
                payload = dict(result.payload)
                memory_id = result.id
                
                # Calculate decayed relevance
                if apply_decay:
                    decayed_relevance = self._calculate_decayed_relevance(payload)
                else:
                    decayed_relevance = payload.get(self.RELEVANCE_SCORE, 1.0)
                
                # Skip memories below threshold
                if decayed_relevance < min_relevance:
                    continue
                
                # Reinforce this memory (it was accessed)
                reinforced_relevance = min(1.0, decayed_relevance + self.reinforcement_factor)
                
                # Update access metadata
                now = datetime.utcnow().isoformat()
                payload[self.LAST_ACCESSED] = now
                payload[self.ACCESS_COUNT] = payload.get(self.ACCESS_COUNT, 0) + 1
                payload[self.RELEVANCE_SCORE] = reinforced_relevance
                
                # Queue update
                points_to_update.append(
                    models.PointStruct(
                        id=memory_id,
                        vector=result.vector,
                        payload=payload
                    )
                )
                
                memories.append({
                    "id": memory_id,
                    "content": payload.get("content", ""),
                    "relevance": reinforced_relevance,
                    "similarity": result.score,
                    "access_count": payload[self.ACCESS_COUNT],
                    "memory_type": payload.get("memory_type", "unknown"),
                    "payload": payload
                })
            
            # Batch update reinforced memories
            if points_to_update:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points_to_update
                )
                logger.debug(f"Reinforced {len(points_to_update)} memories")
            
            # Sort by combined score (relevance * similarity)
            memories.sort(
                key=lambda x: x["relevance"] * x["similarity"],
                reverse=True
            )
            
            return memories[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []
    
    def apply_global_decay(
        self,
        batch_size: int = 100
    ) -> Tuple[int, int]:
        """
        Apply decay to all memories in the collection.
        Should be run periodically (e.g., daily cron job).
        
        Args:
            batch_size: Number of points to process per batch
        
        Returns:
            Tuple of (updated_count, deleted_count)
        """
        updated_count = 0
        deleted_count = 0
        offset = None
        
        try:
            while True:
                # Scroll through all memories
                records, offset = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=True
                )
                
                if not records:
                    break
                
                points_to_update = []
                points_to_delete = []
                
                for record in records:
                    if not record.payload:
                        continue
                    
                    payload = dict(record.payload)
                    
                    # Calculate new decayed relevance
                    new_relevance = self._calculate_decayed_relevance(payload)
                    
                    if new_relevance < self.DECAY_THRESHOLD:
                        # Mark for deletion
                        points_to_delete.append(record.id)
                    else:
                        # Update relevance
                        payload[self.RELEVANCE_SCORE] = new_relevance
                        points_to_update.append(
                            models.PointStruct(
                                id=record.id,
                                vector=record.vector,
                                payload=payload
                            )
                        )
                
                # Apply updates
                if points_to_update:
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=points_to_update
                    )
                    updated_count += len(points_to_update)
                
                # Apply deletions
                if points_to_delete:
                    self.client.delete(
                        collection_name=self.collection_name,
                        points_selector=models.PointIdsList(
                            points=points_to_delete
                        )
                    )
                    deleted_count += len(points_to_delete)
                
                if offset is None:
                    break
            
            logger.info(f"Global decay: updated {updated_count}, deleted {deleted_count} memories")
            return updated_count, deleted_count
            
        except Exception as e:
            logger.error(f"Error applying global decay: {e}")
            return updated_count, deleted_count
    
    def update_memory(
        self,
        memory_id: str,
        new_content: Optional[str] = None,
        new_embedding: Optional[List[float]] = None,
        metadata_updates: Optional[Dict[str, Any]] = None,
        boost_relevance: bool = True
    ) -> bool:
        """
        Update an existing memory with new information.
        
        Args:
            memory_id: ID of memory to update
            new_content: Updated content
            new_embedding: Updated embedding vector
            metadata_updates: Additional metadata changes
            boost_relevance: Whether to boost relevance on update
        
        Returns:
            True if successful
        """
        try:
            # Retrieve existing memory
            results = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id],
                with_payload=True,
                with_vectors=True
            )
            
            if not results:
                logger.warning(f"Memory {memory_id} not found")
                return False
            
            record = results[0]
            payload = dict(record.payload) if record.payload else {}
            vector = new_embedding or record.vector
            
            # Update content if provided
            if new_content:
                payload["content"] = new_content
            
            # Update metadata
            if metadata_updates:
                payload.update(metadata_updates)
            
            # Boost relevance on update
            if boost_relevance:
                current_relevance = payload.get(self.RELEVANCE_SCORE, 0.5)
                payload[self.RELEVANCE_SCORE] = min(1.0, current_relevance + 0.2)
            
            # Mark update time
            payload["updated_at"] = datetime.utcnow().isoformat()
            
            # Upsert updated memory
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=memory_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )
            
            logger.info(f"Updated memory {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {e}")
            return False
    
    def consolidate_similar_memories(
        self,
        similarity_threshold: float = CONSOLIDATION_SIMILARITY,
        max_consolidations: int = 50
    ) -> int:
        """
        Merge highly similar memories to reduce redundancy.
        
        Args:
            similarity_threshold: Minimum similarity for merging
            max_consolidations: Maximum number of consolidations
        
        Returns:
            Number of consolidations performed
        """
        consolidation_count = 0
        processed_ids = set()
        
        try:
            # Get all memories
            records, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=True,
                with_vectors=True
            )
            
            for record in records:
                if record.id in processed_ids:
                    continue
                if consolidation_count >= max_consolidations:
                    break
                
                # Find similar memories
                similar = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=record.vector,
                    limit=5,
                    score_threshold=similarity_threshold,
                    with_payload=True
                )
                
                # Filter to unprocessed, non-self memories
                candidates = [
                    s for s in similar 
                    if s.id != record.id and s.id not in processed_ids
                ]
                
                if candidates:
                    # Merge with highest scoring candidate
                    best_match = candidates[0]
                    
                    # Create consolidated memory
                    merged_content = self._merge_contents(
                        record.payload.get("content", ""),
                        best_match.payload.get("content", "")
                    )
                    
                    # Average the vectors
                    merged_vector = [
                        (a + b) / 2 
                        for a, b in zip(record.vector, best_match.vector)
                    ]
                    
                    # Combine relevance scores
                    merged_relevance = max(
                        record.payload.get(self.RELEVANCE_SCORE, 0.5),
                        best_match.payload.get(self.RELEVANCE_SCORE, 0.5)
                    )
                    
                    # Update the original with merged content
                    self.update_memory(
                        memory_id=record.id,
                        new_content=merged_content,
                        new_embedding=merged_vector,
                        metadata_updates={
                            self.IS_CONSOLIDATED: True,
                            self.PARENT_MEMORIES: [str(record.id), str(best_match.id)],
                            self.RELEVANCE_SCORE: merged_relevance
                        }
                    )
                    
                    # Delete the merged memory
                    self.client.delete(
                        collection_name=self.collection_name,
                        points_selector=models.PointIdsList(
                            points=[best_match.id]
                        )
                    )
                    
                    processed_ids.add(record.id)
                    processed_ids.add(best_match.id)
                    consolidation_count += 1
            
            logger.info(f"Consolidated {consolidation_count} memory pairs")
            return consolidation_count
            
        except Exception as e:
            logger.error(f"Error consolidating memories: {e}")
            return consolidation_count
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about memory collection.
        
        Returns:
            Dictionary with memory statistics
        """
        try:
            info = self.client.get_collection(self.collection_name)
            
            # Sample memories for stats
            records, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=100,
                with_payload=True
            )
            
            relevance_scores = []
            access_counts = []
            memory_types = {}
            
            for record in records:
                if record.payload:
                    relevance_scores.append(
                        record.payload.get(self.RELEVANCE_SCORE, 0.5)
                    )
                    access_counts.append(
                        record.payload.get(self.ACCESS_COUNT, 0)
                    )
                    mem_type = record.payload.get("memory_type", "unknown")
                    memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
            
            return {
                "total_memories": info.points_count,
                "avg_relevance": sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0,
                "avg_access_count": sum(access_counts) / len(access_counts) if access_counts else 0,
                "low_relevance_count": sum(1 for r in relevance_scores if r < self.DECAY_THRESHOLD),
                "memory_types": memory_types,
                "collection_status": info.status
            }
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {}
    
    def _calculate_decayed_relevance(
        self,
        payload: Dict[str, Any]
    ) -> float:
        """Calculate relevance after applying temporal decay."""
        try:
            last_accessed = payload.get(self.LAST_ACCESSED)
            if not last_accessed:
                return payload.get(self.RELEVANCE_SCORE, 0.5)
            
            last_dt = datetime.fromisoformat(last_accessed.replace('Z', '+00:00'))
            now = datetime.utcnow()
            
            # Handle timezone-naive comparison
            if last_dt.tzinfo:
                last_dt = last_dt.replace(tzinfo=None)
            
            days_elapsed = (now - last_dt).total_seconds() / 86400
            
            current_relevance = payload.get(self.RELEVANCE_SCORE, 1.0)
            decay_rate = payload.get(self.DECAY_RATE, self.decay_rate)
            
            # Exponential decay: R(t) = R(0) * e^(-λt)
            decayed = current_relevance * math.exp(-decay_rate * days_elapsed)
            
            return max(0.0, min(1.0, decayed))
            
        except Exception as e:
            logger.warning(f"Error calculating decay: {e}")
            return payload.get(self.RELEVANCE_SCORE, 0.5)
    
    def _merge_contents(
        self,
        content1: str,
        content2: str
    ) -> str:
        """Merge two memory contents."""
        if content1 == content2:
            return content1
        
        # Simple merge - in practice, could use LLM for smarter merging
        return f"{content1}\n---\n{content2}"


def create_memory_manager(
    client: QdrantClient,
    collection_name: str = "session_memory"
) -> MemoryEvolution:
    """
    Create a memory evolution manager.
    
    Args:
        client: Qdrant client
        collection_name: Memory collection name
    
    Returns:
        MemoryEvolution instance
    """
    return MemoryEvolution(client, collection_name)

