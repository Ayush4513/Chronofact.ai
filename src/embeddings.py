"""
Chronofact.ai - Embeddings Module
Handles vector embeddings using sentence-transformers.
"""

from sentence_transformers import SentenceTransformer
from typing import List, Optional
import numpy as np


class EmbeddingModel:
    """Wrapper for sentence-transformers embedding model."""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "cpu"
    ):
        """Initialize the embedding model."""
        self.model_name = model_name
        self.model = SentenceTransformer(model_name, device=device)
        self.vector_size = self.model.get_sentence_embedding_dimension()
    
    def encode(
        self,
        texts: str | List[str],
        normalize: bool = True
    ) -> List[float] | List[List[float]]:
        """
        Encode text(s) to vector embeddings.
        
        Args:
            texts: Single text string or list of texts
            normalize: Whether to normalize vectors (L2 normalization)
        
        Returns:
            Embedding vector or list of vectors
        """
        if isinstance(texts, str):
            texts = [texts]
            single_input = True
        else:
            single_input = False
        
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )
        
        if single_input:
            return embeddings[0].tolist()
        
        return [emb.tolist() for emb in embeddings]
    
    def encode_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Encode multiple texts in batches.
        
        Args:
            texts: List of text strings
            batch_size: Number of texts to process at once
            show_progress: Whether to show progress bar
        
        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=True
        )
        
        return [emb.tolist() for emb in embeddings]
    
    def similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Calculate cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            Cosine similarity score (0 to 1)
        """
        vec1 = np.array(self.encode(text1))
        vec2 = np.array(self.encode(text2))
        
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
    
    def get_vector_size(self) -> int:
        """Get the embedding vector dimension."""
        return self.vector_size


# Global model instance (lazy loaded)
_model_instance: Optional[EmbeddingModel] = None


def get_embedding_model(
    model_name: Optional[str] = None,
    device: Optional[str] = None
) -> EmbeddingModel:
    """
    Get or create a global embedding model instance.
    
    Args:
        model_name: Name of the sentence-transformers model
        device: Device to run on ('cpu' or 'cuda')
    
    Returns:
        EmbeddingModel instance
    """
    global _model_instance
    
    if _model_instance is None:
        from .config import get_config
        config = get_config()
        
        _model_instance = EmbeddingModel(
            model_name=model_name or config.embedding.model_name,
            device=device or config.embedding.device
        )
    
    return _model_instance
