"""
Chronofact.ai - Tweet Data Models
Pydantic models for multimodal tweet processing.
"""

from pydantic import BaseModel, Field, computed_field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ImageAnalysisType(str, Enum):
    """Types of image content."""
    PHOTO = "photo"
    SCREENSHOT = "screenshot"
    MEME = "meme"
    INFOGRAPHIC = "infographic"
    DOCUMENT = "document"
    VIDEO_THUMBNAIL = "video_thumbnail"
    UNKNOWN = "unknown"


class TweetImage(BaseModel):
    """Model for tweet image data."""
    
    url: str = Field(..., description="Original image URL")
    local_path: Optional[str] = Field(None, description="Local cached path")
    
    # Image metadata
    width: Optional[int] = Field(None, ge=1)
    height: Optional[int] = Field(None, ge=1)
    format: Optional[str] = Field(None, description="Image format (jpg, png, etc)")
    size_bytes: Optional[int] = Field(None, ge=0)
    
    # AI-generated analysis
    embedding: Optional[List[float]] = Field(None, description="CLIP embedding vector")
    caption: Optional[str] = Field(None, description="AI-generated caption")
    detected_text: Optional[str] = Field(None, description="OCR extracted text")
    image_type: ImageAnalysisType = Field(default=ImageAnalysisType.UNKNOWN)
    
    # Visual features
    dominant_colors: Optional[List[str]] = Field(None, description="Dominant hex colors")
    contains_face: Optional[bool] = Field(None)
    contains_text: Optional[bool] = Field(None)
    
    # Credibility signals
    is_manipulated: Optional[bool] = Field(None, description="Detected as edited/fake")
    manipulation_score: Optional[float] = Field(None, ge=0, le=1)
    reverse_search_matches: Optional[int] = Field(None, description="Similar images found online")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @computed_field
    @property
    def aspect_ratio(self) -> Optional[float]:
        """Calculate aspect ratio."""
        if self.width and self.height:
            return round(self.width / self.height, 2)
        return None
    
    @computed_field
    @property
    def has_embedding(self) -> bool:
        """Check if image has been embedded."""
        return self.embedding is not None and len(self.embedding) > 0


class TweetMetadata(BaseModel):
    """Additional tweet metadata."""
    
    # Engagement metrics
    like_count: int = Field(default=0, ge=0)
    retweet_count: int = Field(default=0, ge=0)
    reply_count: int = Field(default=0, ge=0)
    quote_count: int = Field(default=0, ge=0)
    view_count: Optional[int] = Field(None, ge=0)
    
    # Author info
    author_followers: Optional[int] = Field(None, ge=0)
    author_following: Optional[int] = Field(None, ge=0)
    author_tweet_count: Optional[int] = Field(None, ge=0)
    author_account_age_days: Optional[int] = Field(None, ge=0)
    
    # Content flags
    is_retweet: bool = Field(default=False)
    is_quote: bool = Field(default=False)
    is_reply: bool = Field(default=False)
    has_links: bool = Field(default=False)
    has_hashtags: bool = Field(default=False)
    has_mentions: bool = Field(default=False)
    
    # Language
    language: Optional[str] = Field(None, description="ISO language code")
    
    @computed_field
    @property
    def engagement_score(self) -> float:
        """Calculate normalized engagement score."""
        total = self.like_count + (self.retweet_count * 2) + (self.reply_count * 3)
        # Normalize with log scale
        import math
        return round(math.log10(total + 1) / 6, 3)  # Max ~6 for viral posts


class MultimodalTweet(BaseModel):
    """
    Complete multimodal tweet model with text and images.
    Designed for vector storage in Qdrant.
    """
    
    # Core identifiers
    id: str = Field(..., description="Tweet ID")
    text: str = Field(..., description="Tweet text content")
    
    # Author info
    author_id: str = Field(..., description="Author user ID")
    author_username: str = Field(..., description="Author @username")
    author_display_name: Optional[str] = Field(None)
    author_verified: bool = Field(default=False)
    author_profile_image: Optional[str] = Field(None)
    
    # Temporal
    timestamp: datetime = Field(..., description="Tweet creation time")
    
    # Location
    location: Optional[str] = Field(None, description="Geo location or place name")
    coordinates: Optional[Dict[str, float]] = Field(None, description="lat/lng coordinates")
    
    # Images
    images: List[TweetImage] = Field(default_factory=list)
    
    # Embeddings
    text_embedding: Optional[List[float]] = Field(None, description="Text-only embedding")
    multimodal_embedding: Optional[List[float]] = Field(None, description="Combined text+image CLIP embedding")
    
    # Metadata
    metadata: TweetMetadata = Field(default_factory=TweetMetadata)
    
    # Credibility
    credibility_score: float = Field(default=0.5, ge=0, le=1)
    credibility_factors: List[str] = Field(default_factory=list)
    
    # Processing status
    processed: bool = Field(default=False)
    processing_errors: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @computed_field
    @property
    def has_images(self) -> bool:
        """Check if tweet has images."""
        return len(self.images) > 0
    
    @computed_field
    @property
    def image_count(self) -> int:
        """Get number of images."""
        return len(self.images)
    
    @computed_field
    @property
    def has_embeddings(self) -> bool:
        """Check if embeddings are computed."""
        return (
            (self.text_embedding is not None and len(self.text_embedding) > 0) or
            (self.multimodal_embedding is not None and len(self.multimodal_embedding) > 0)
        )
    
    @computed_field
    @property
    def all_image_urls(self) -> List[str]:
        """Get all image URLs."""
        return [img.url for img in self.images]
    
    def get_combined_text(self) -> str:
        """Get text combined with image captions for enhanced search."""
        parts = [self.text]
        for img in self.images:
            if img.caption:
                parts.append(f"[Image: {img.caption}]")
            if img.detected_text:
                parts.append(f"[Text in image: {img.detected_text}]")
        return " ".join(parts)
    
    def to_qdrant_payload(self) -> Dict[str, Any]:
        """Convert to Qdrant-compatible payload dict."""
        return {
            "tweet_id": self.id,
            "text": self.text,
            "combined_text": self.get_combined_text(),
            "author_id": self.author_id,
            "author_username": self.author_username,
            "author_verified": self.author_verified,
            "timestamp": self.timestamp.isoformat(),
            "location": self.location,
            "has_images": self.has_images,
            "image_count": self.image_count,
            "image_urls": self.all_image_urls,
            "image_captions": [img.caption for img in self.images if img.caption],
            "credibility_score": self.credibility_score,
            "credibility_factors": self.credibility_factors,
            "like_count": self.metadata.like_count,
            "retweet_count": self.metadata.retweet_count,
            "engagement_score": self.metadata.engagement_score,
            "is_verified": self.author_verified,
        }


class ProcessedTweet(BaseModel):
    """
    Fully processed tweet ready for Qdrant insertion.
    Contains all computed embeddings and analysis results.
    """
    
    tweet: MultimodalTweet
    
    # Vector data for Qdrant
    text_vector: List[float] = Field(..., description="Text embedding vector")
    multimodal_vector: Optional[List[float]] = Field(None, description="Combined multimodal vector")
    image_vectors: List[List[float]] = Field(default_factory=list, description="Individual image vectors")
    
    # Analysis results
    misinformation_risk: Optional[str] = Field(None, description="low/medium/high")
    detected_claims: List[str] = Field(default_factory=list)
    sentiment: Optional[str] = Field(None, description="positive/negative/neutral")
    topics: List[str] = Field(default_factory=list)
    
    # Qdrant point ID
    point_id: Optional[int] = Field(None, description="Qdrant point ID (hash of tweet_id)")
    
    def get_qdrant_point_id(self) -> int:
        """Generate deterministic Qdrant point ID from tweet ID."""
        import hashlib
        return int(hashlib.md5(self.tweet.id.encode()).hexdigest()[:8], 16)
    
    def to_qdrant_point(self) -> Dict[str, Any]:
        """Convert to Qdrant point structure."""
        from qdrant_client import models
        
        return models.PointStruct(
            id=self.get_qdrant_point_id(),
            vector={
                "text": self.text_vector,
                "multimodal": self.multimodal_vector or self.text_vector,
            },
            payload=self.tweet.to_qdrant_payload()
        )

