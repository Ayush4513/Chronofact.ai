"""
Chronofact.ai - Multimodal Embeddings Module
Handles multimodal embeddings for text, images, and combined content.
Supports CLIP for image-text alignment and cross-modal search.
"""

from sentence_transformers import SentenceTransformer
from typing import List, Optional, Union, Dict, Any
from PIL import Image
import numpy as np
import requests
from io import BytesIO
import logging
import hashlib

logger = logging.getLogger(__name__)


class MultimodalEmbedder:
    """
    Multimodal embedding model supporting text and images.
    Uses CLIP for cross-modal embeddings enabling image-text search.
    """
    
    # CLIP model for multimodal embeddings
    CLIP_MODEL = "clip-ViT-B-32"
    # Text-only model for high-quality text embeddings
    TEXT_MODEL = "all-MiniLM-L6-v2"
    
    def __init__(
        self,
        device: str = "cpu",
        use_clip: bool = True,
        image_cache_size: int = 100
    ):
        """
        Initialize multimodal embedder.
        
        Args:
            device: Device to run models on ('cpu' or 'cuda')
            use_clip: Whether to load CLIP model for image embeddings
            image_cache_size: Maximum number of images to cache
        """
        self.device = device
        self.use_clip = use_clip
        
        # Initialize text model
        logger.info(f"Loading text model: {self.TEXT_MODEL}")
        self.text_model = SentenceTransformer(self.TEXT_MODEL, device=device)
        self.text_vector_size = self.text_model.get_sentence_embedding_dimension()
        
        # Initialize CLIP model for multimodal
        self.clip_model = None
        self.clip_vector_size = None
        if use_clip:
            try:
                logger.info(f"Loading CLIP model: {self.CLIP_MODEL}")
                self.clip_model = SentenceTransformer(self.CLIP_MODEL, device=device)
                self.clip_vector_size = self.clip_model.get_sentence_embedding_dimension()
                logger.info(f"CLIP model loaded. Vector size: {self.clip_vector_size}")
            except Exception as e:
                logger.warning(f"Failed to load CLIP model: {e}. Image embeddings disabled.")
                self.use_clip = False
        
        # Simple LRU cache for image embeddings
        self._image_cache: Dict[str, List[float]] = {}
        self._cache_order: List[str] = []
        self._cache_size = image_cache_size
    
    def encode_text(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
        use_clip: bool = False
    ) -> Union[List[float], List[List[float]]]:
        """
        Encode text to vector embeddings.
        
        Args:
            texts: Single text or list of texts
            normalize: Whether to L2 normalize vectors
            use_clip: Use CLIP model for cross-modal compatible embeddings
        
        Returns:
            Embedding vector(s)
        """
        single_input = isinstance(texts, str)
        if single_input:
            texts = [texts]
        
        model = self.clip_model if (use_clip and self.clip_model) else self.text_model
        
        embeddings = model.encode(
            texts,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )
        
        if single_input:
            return embeddings[0].tolist()
        return [emb.tolist() for emb in embeddings]
    
    def encode_image(
        self,
        image: Union[str, Image.Image],
        normalize: bool = True
    ) -> Optional[List[float]]:
        """
        Encode an image to vector embedding using CLIP.
        
        Args:
            image: PIL Image, file path, or URL
            normalize: Whether to L2 normalize vector
        
        Returns:
            Embedding vector or None if encoding fails
        """
        if not self.clip_model:
            logger.warning("CLIP model not available for image encoding")
            return None
        
        try:
            # Load image if needed
            pil_image = self._load_image(image)
            if pil_image is None:
                return None
            
            # Check cache
            cache_key = self._get_image_hash(pil_image)
            if cache_key in self._image_cache:
                return self._image_cache[cache_key]
            
            # Encode with CLIP
            embedding = self.clip_model.encode(
                pil_image,
                normalize_embeddings=normalize,
                show_progress_bar=False
            )
            
            result = embedding.tolist()
            
            # Cache result
            self._cache_embedding(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            return None
    
    def encode_image_batch(
        self,
        images: List[Union[str, Image.Image]],
        normalize: bool = True
    ) -> List[Optional[List[float]]]:
        """
        Encode multiple images to vector embeddings.
        
        Args:
            images: List of PIL Images, file paths, or URLs
            normalize: Whether to L2 normalize vectors
        
        Returns:
            List of embedding vectors (None for failed encodings)
        """
        if not self.clip_model:
            logger.warning("CLIP model not available for image encoding")
            return [None] * len(images)
        
        results = []
        valid_images = []
        valid_indices = []
        
        # Load and filter valid images
        for i, img in enumerate(images):
            pil_image = self._load_image(img)
            if pil_image:
                valid_images.append(pil_image)
                valid_indices.append(i)
        
        # Batch encode valid images
        if valid_images:
            try:
                embeddings = self.clip_model.encode(
                    valid_images,
                    normalize_embeddings=normalize,
                    show_progress_bar=False
                )
                
                embedding_map = {
                    valid_indices[i]: emb.tolist() 
                    for i, emb in enumerate(embeddings)
                }
            except Exception as e:
                logger.error(f"Error batch encoding images: {e}")
                embedding_map = {}
        else:
            embedding_map = {}
        
        # Build result list
        for i in range(len(images)):
            results.append(embedding_map.get(i))
        
        return results
    
    def encode_multimodal(
        self,
        text: Optional[str] = None,
        image: Optional[Union[str, Image.Image]] = None,
        fusion_method: str = "average"
    ) -> Optional[List[float]]:
        """
        Encode combined text and image content.
        
        Args:
            text: Optional text content
            image: Optional image (PIL, path, or URL)
            fusion_method: How to combine embeddings ('average', 'concat', 'text_weighted')
        
        Returns:
            Combined embedding vector or None
        """
        if not text and not image:
            return None
        
        text_emb = None
        image_emb = None
        
        # Get text embedding (use CLIP for compatibility)
        if text:
            text_emb = np.array(self.encode_text(text, use_clip=True))
        
        # Get image embedding
        if image and self.clip_model:
            img_result = self.encode_image(image)
            if img_result:
                image_emb = np.array(img_result)
        
        # Fuse embeddings
        if text_emb is not None and image_emb is not None:
            if fusion_method == "average":
                combined = (text_emb + image_emb) / 2
            elif fusion_method == "text_weighted":
                # 70% text, 30% image
                combined = 0.7 * text_emb + 0.3 * image_emb
            elif fusion_method == "concat":
                combined = np.concatenate([text_emb, image_emb])
            else:
                combined = (text_emb + image_emb) / 2
            
            # Normalize
            combined = combined / np.linalg.norm(combined)
            return combined.tolist()
        
        elif text_emb is not None:
            return text_emb.tolist()
        elif image_emb is not None:
            return image_emb.tolist()
        
        return None
    
    def similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
        
        Returns:
            Cosine similarity score (-1 to 1)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
    
    def cross_modal_search(
        self,
        query: Union[str, Image.Image],
        candidates: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search across modalities - find images with text or vice versa.
        
        Args:
            query: Text string or PIL Image
            candidates: List of dicts with 'embedding' key
            top_k: Number of results to return
        
        Returns:
            Top-k candidates sorted by similarity
        """
        # Encode query
        if isinstance(query, str):
            query_emb = self.encode_text(query, use_clip=True)
        else:
            query_emb = self.encode_image(query)
        
        if query_emb is None:
            return []
        
        # Calculate similarities
        results = []
        for candidate in candidates:
            if 'embedding' in candidate:
                sim = self.similarity(query_emb, candidate['embedding'])
                results.append({**candidate, 'similarity': sim})
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:top_k]
    
    def get_vector_size(self, modality: str = "text") -> int:
        """
        Get embedding dimension for specified modality.
        
        Args:
            modality: 'text', 'image', or 'clip'
        
        Returns:
            Vector dimension
        """
        if modality == "image" or modality == "clip":
            return self.clip_vector_size or self.text_vector_size
        return self.text_vector_size
    
    def _load_image(
        self,
        image: Union[str, Image.Image]
    ) -> Optional[Image.Image]:
        """Load image from various sources."""
        try:
            if isinstance(image, Image.Image):
                return image.convert("RGB")
            
            if isinstance(image, str):
                if image.startswith(('http://', 'https://')):
                    # Load from URL
                    response = requests.get(image, timeout=10)
                    response.raise_for_status()
                    return Image.open(BytesIO(response.content)).convert("RGB")
                else:
                    # Load from file path
                    return Image.open(image).convert("RGB")
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to load image: {e}")
            return None
    
    def _get_image_hash(self, image: Image.Image) -> str:
        """Generate hash for image caching."""
        img_bytes = image.tobytes()
        return hashlib.md5(img_bytes).hexdigest()
    
    def _cache_embedding(self, key: str, embedding: List[float]) -> None:
        """Cache embedding with LRU eviction."""
        if key in self._image_cache:
            return
        
        # Evict oldest if at capacity
        while len(self._cache_order) >= self._cache_size:
            oldest = self._cache_order.pop(0)
            self._image_cache.pop(oldest, None)
        
        self._image_cache[key] = embedding
        self._cache_order.append(key)


# Global instance
_multimodal_instance: Optional[MultimodalEmbedder] = None


def get_multimodal_embedder(
    device: Optional[str] = None,
    use_clip: bool = True
) -> MultimodalEmbedder:
    """
    Get or create global multimodal embedder instance.
    
    Args:
        device: Device to run on ('cpu' or 'cuda')
        use_clip: Whether to enable CLIP for images
    
    Returns:
        MultimodalEmbedder instance
    """
    global _multimodal_instance
    
    if _multimodal_instance is None:
        from .config import get_config
        config = get_config()
        
        _multimodal_instance = MultimodalEmbedder(
            device=device or config.embedding.device,
            use_clip=use_clip
        )
    
    return _multimodal_instance

