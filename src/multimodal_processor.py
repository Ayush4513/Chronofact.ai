"""
Chronofact.ai - Multimodal Tweet Processor
Processes tweets with text and images, generates embeddings, and stores in Qdrant.
"""

import logging
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime

from qdrant_client import QdrantClient, models

from .models.tweet import (
    TweetImage,
    MultimodalTweet,
    TweetMetadata,
    ProcessedTweet,
    ImageAnalysisType,
)
from .utils.image_processor import ImageProcessor, process_tweet_images
from .multimodal import get_multimodal_embedder, MultimodalEmbedder
from .embeddings import get_embedding_model
from .config import get_config

logger = logging.getLogger(__name__)


class MultimodalTweetProcessor:
    """
    Processes tweets with multimodal content (text + images).
    Generates embeddings and prepares data for Qdrant storage.
    """
    
    def __init__(
        self,
        qdrant_client: Optional[QdrantClient] = None,
        use_clip: bool = True,
        cache_images: bool = True
    ):
        """
        Initialize the multimodal processor.
        
        Args:
            qdrant_client: Optional Qdrant client for storage
            use_clip: Whether to use CLIP for multimodal embeddings
            cache_images: Whether to cache downloaded images
        """
        self.config = get_config()
        self.client = qdrant_client
        self.use_clip = use_clip
        self.cache_images = cache_images
        
        # Initialize embedders
        self.text_embedder = get_embedding_model()
        self.multimodal_embedder = get_multimodal_embedder(use_clip=use_clip) if use_clip else None
        
        # Initialize image processor
        self.image_processor = ImageProcessor()
        
        # Stats
        self.stats = {
            "processed": 0,
            "with_images": 0,
            "images_processed": 0,
            "errors": 0,
        }
    
    def process_raw_tweet(
        self,
        tweet_data: Dict[str, Any]
    ) -> Optional[ProcessedTweet]:
        """
        Process a raw tweet dict into a fully processed multimodal tweet.
        
        Args:
            tweet_data: Raw tweet data dict with keys like:
                - tweet_id, text, author, timestamp
                - media_urls (list of image URLs)
                - fave_count, retweet_count, is_verified
        
        Returns:
            ProcessedTweet ready for Qdrant or None if processing failed
        """
        try:
            # Parse raw data into MultimodalTweet
            tweet = self._parse_raw_tweet(tweet_data)
            
            # Process images if present
            if tweet.has_images and self.use_clip:
                self._process_tweet_images(tweet)
            
            # Generate embeddings
            processed = self._generate_embeddings(tweet)
            
            self.stats["processed"] += 1
            if tweet.has_images:
                self.stats["with_images"] += 1
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing tweet {tweet_data.get('tweet_id', 'unknown')}: {e}")
            self.stats["errors"] += 1
            return None
    
    def process_batch(
        self,
        tweets: List[Dict[str, Any]],
        upsert_to_qdrant: bool = True
    ) -> List[ProcessedTweet]:
        """
        Process a batch of tweets.
        
        Args:
            tweets: List of raw tweet dicts
            upsert_to_qdrant: Whether to upsert processed tweets to Qdrant
        
        Returns:
            List of successfully processed tweets
        """
        processed_tweets = []
        
        for tweet_data in tweets:
            processed = self.process_raw_tweet(tweet_data)
            if processed:
                processed_tweets.append(processed)
        
        if upsert_to_qdrant and self.client and processed_tweets:
            self._upsert_to_qdrant(processed_tweets)
        
        logger.info(f"Processed {len(processed_tweets)}/{len(tweets)} tweets")
        return processed_tweets
    
    def _parse_raw_tweet(self, data: Dict[str, Any]) -> MultimodalTweet:
        """Parse raw tweet data into MultimodalTweet model."""
        
        # Parse media URLs
        media_urls = data.get("media_urls", [])
        if isinstance(media_urls, str):
            import ast
            try:
                media_urls = ast.literal_eval(media_urls)
            except:
                media_urls = []
        
        # Create TweetImage objects
        images = [
            TweetImage(url=url)
            for url in media_urls
            if isinstance(url, str) and url.startswith("http")
        ]
        
        # Parse timestamp
        timestamp = data.get("timestamp", "")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except:
                timestamp = datetime.now()
        
        # Create metadata
        metadata = TweetMetadata(
            like_count=int(data.get("fave_count", 0) or 0),
            retweet_count=int(data.get("retweet_count", 0) or 0),
        )
        
        # Build MultimodalTweet
        tweet = MultimodalTweet(
            id=str(data.get("tweet_id", f"unknown_{hash(str(data))}")),
            text=str(data.get("text", "")),
            author_id=str(data.get("author_id", data.get("author", "unknown"))),
            author_username=str(data.get("author", "unknown")),
            author_verified=bool(data.get("is_verified", False)),
            timestamp=timestamp,
            location=data.get("location"),
            images=images,
            metadata=metadata,
            credibility_score=float(data.get("credibility_score", 0.5) or 0.5),
        )
        
        return tweet
    
    def _process_tweet_images(self, tweet: MultimodalTweet) -> None:
        """Download and process all images in a tweet."""
        
        for image in tweet.images:
            try:
                # Download image
                pil_image = self.image_processor.download_image(
                    image.url,
                    save_local=self.cache_images
                )
                
                if pil_image is None:
                    continue
                
                # Analyze image
                analysis = self.image_processor.analyze_image(pil_image)
                
                # Update TweetImage with analysis
                image.width = analysis.get("width")
                image.height = analysis.get("height")
                image.dominant_colors = analysis.get("dominant_colors")
                image.contains_text = analysis.get("likely_contains_text")
                image.image_type = ImageAnalysisType(analysis.get("image_type", "unknown"))
                
                # Generate image embedding
                if self.multimodal_embedder:
                    image.embedding = self.multimodal_embedder.encode_image(pil_image)
                
                # Set local path
                image.local_path = str(self.image_processor._get_cache_path(image.url))
                
                self.stats["images_processed"] += 1
                
            except Exception as e:
                logger.warning(f"Error processing image {image.url}: {e}")
                tweet.processing_errors.append(f"Image error: {str(e)[:100]}")
    
    def _generate_embeddings(self, tweet: MultimodalTweet) -> ProcessedTweet:
        """Generate all embeddings for a tweet."""
        
        # Text embedding (always generated)
        text_vector = self.text_embedder.encode(tweet.text)
        tweet.text_embedding = text_vector
        
        # Multimodal embedding (if CLIP available and tweet has images)
        multimodal_vector = None
        image_vectors = []
        
        if self.multimodal_embedder:
            # Get image embeddings
            for image in tweet.images:
                if image.embedding:
                    image_vectors.append(image.embedding)
            
            # Generate combined multimodal embedding
            if tweet.has_images and image_vectors:
                # Use first image for combined embedding
                first_image_path = tweet.images[0].local_path
                if first_image_path:
                    multimodal_vector = self.multimodal_embedder.encode_multimodal(
                        text=tweet.text,
                        image=first_image_path,
                        fusion_method="average"
                    )
            else:
                # Text-only through CLIP for cross-modal compatibility
                multimodal_vector = self.multimodal_embedder.encode_text(
                    tweet.text,
                    use_clip=True
                )
        
        tweet.multimodal_embedding = multimodal_vector
        tweet.processed = True
        
        # Create ProcessedTweet
        return ProcessedTweet(
            tweet=tweet,
            text_vector=text_vector,
            multimodal_vector=multimodal_vector,
            image_vectors=image_vectors,
        )
    
    def _upsert_to_qdrant(self, processed_tweets: List[ProcessedTweet]) -> None:
        """Upsert processed tweets to Qdrant."""
        
        if not self.client:
            logger.warning("No Qdrant client configured, skipping upsert")
            return
        
        points = []
        
        for pt in processed_tweets:
            point_id = pt.get_qdrant_point_id()
            
            # Build named vectors dict
            vectors = {
                "text": pt.text_vector,
            }
            
            # Add multimodal vector if available
            if pt.multimodal_vector:
                vectors["multimodal"] = pt.multimodal_vector
                vectors["image"] = pt.multimodal_vector  # Use same for image search
            else:
                # Pad text vector to CLIP size for compatibility
                # Or use text vector through CLIP
                pass
            
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vectors,
                    payload=pt.tweet.to_qdrant_payload()
                )
            )
        
        try:
            self.client.upsert(
                collection_name=self.config.collection_posts,
                points=points,
                wait=True
            )
            logger.info(f"Upserted {len(points)} multimodal tweets to Qdrant")
            
        except Exception as e:
            logger.error(f"Error upserting to Qdrant: {e}")
            raise
    
    def search_by_image(
        self,
        image_path_or_url: str,
        limit: int = 10,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search for tweets similar to an image (cross-modal search).
        
        Args:
            image_path_or_url: Path to image file or URL
            limit: Number of results
            min_score: Minimum similarity score
        
        Returns:
            List of matching tweets with scores
        """
        if not self.multimodal_embedder or not self.client:
            logger.warning("Multimodal search not available")
            return []
        
        # Encode image
        image_embedding = self.multimodal_embedder.encode_image(image_path_or_url)
        if not image_embedding:
            return []
        
        # Search using multimodal vector
        results = self.client.search(
            collection_name=self.config.collection_posts,
            query_vector=("multimodal", image_embedding),
            limit=limit,
            score_threshold=min_score
        )
        
        return [
            {
                "id": r.id,
                "score": r.score,
                "payload": r.payload
            }
            for r in results
        ]
    
    def search_multimodal(
        self,
        query: str,
        query_image: Optional[str] = None,
        limit: int = 10,
        filter_has_images: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Search with combined text and optional image query.
        
        Args:
            query: Text query
            query_image: Optional image path/URL for multimodal query
            limit: Number of results
            filter_has_images: If True, only return tweets with images
        
        Returns:
            List of matching tweets with scores
        """
        if not self.client:
            return []
        
        # Build query vector
        if query_image and self.multimodal_embedder:
            query_vector = self.multimodal_embedder.encode_multimodal(
                text=query,
                image=query_image,
                fusion_method="average"
            )
            vector_name = "multimodal"
        elif self.multimodal_embedder:
            query_vector = self.multimodal_embedder.encode_text(query, use_clip=True)
            vector_name = "multimodal"
        else:
            query_vector = self.text_embedder.encode(query)
            vector_name = "text"
        
        # Build filter
        query_filter = None
        if filter_has_images is not None:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="has_images",
                        match=models.MatchValue(value=filter_has_images)
                    )
                ]
            )
        
        # Search
        results = self.client.search(
            collection_name=self.config.collection_posts,
            query_vector=(vector_name, query_vector),
            query_filter=query_filter,
            limit=limit
        )
        
        return [
            {
                "id": r.id,
                "score": r.score,
                "payload": r.payload
            }
            for r in results
        ]
    
    def get_stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        return {
            **self.stats,
            **self.image_processor.get_stats()
        }


# Convenience function
def process_tweets_multimodal(
    tweets: List[Dict[str, Any]],
    qdrant_client: Optional[QdrantClient] = None,
    use_clip: bool = True
) -> List[ProcessedTweet]:
    """
    Process a list of tweets with multimodal support.
    
    Args:
        tweets: List of raw tweet dicts
        qdrant_client: Optional Qdrant client for storage
        use_clip: Whether to use CLIP for images
    
    Returns:
        List of processed tweets
    """
    processor = MultimodalTweetProcessor(
        qdrant_client=qdrant_client,
        use_clip=use_clip
    )
    return processor.process_batch(tweets, upsert_to_qdrant=qdrant_client is not None)

