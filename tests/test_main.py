"""
Tests for Chronofact.ai
"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def config():
    """Test configuration fixture."""
    from src.config import get_config
    return get_config()


@pytest.fixture
def qdrant_client(config):
    """Qdrant client fixture."""
    from src.qdrant_setup import create_qdrant_client
    return create_qdrant_client(config)


class TestConfig:
    """Tests for configuration module."""
    
    def test_config_initialization(self, config):
        """Test that configuration initializes correctly."""
        assert config is not None
        assert config.collection_posts == "x_posts"
        assert config.collection_knowledge == "knowledge_facts"
        assert config.collection_memory == "session_memory"
        assert config.default_search_limit == 10
    
    def test_qdrant_config(self, config):
        """Test Qdrant configuration."""
        assert config.qdrant is not None
        assert config.qdrant.use_local is True
    
    def test_embedding_config(self, config):
        """Test embedding configuration."""
        assert config.embedding is not None
        assert config.embedding.model_name is not None


class TestEmbeddings:
    """Tests for embedding module."""
    
    def test_embedding_model_creation(self):
        """Test creating embedding model."""
        from src.embeddings import EmbeddingModel
        
        # Skip test if sentence-transformers not installed
        pytest.importorskip("sentence_transformers")
        
        model = EmbeddingModel(model_name="all-MiniLM-L6-v2")
        assert model is not None
        assert model.vector_size > 0
    
    def test_text_encoding(self):
        """Test encoding text to vectors."""
        from src.embeddings import get_embedding_model
        
        pytest.importorskip("sentence_transformers")
        
        model = get_embedding_model()
        vector = model.encode("test text")
        
        assert isinstance(vector, list)
        assert len(vector) == model.vector_size
    
    def test_batch_encoding(self):
        """Test encoding multiple texts."""
        from src.embeddings import get_embedding_model
        
        pytest.importorskip("sentence_transformers")
        
        model = get_embedding_model()
        texts = ["test one", "test two", "test three"]
        vectors = model.encode_batch(texts, batch_size=2)
        
        assert isinstance(vectors, list)
        assert len(vectors) == 3
    
    def test_similarity_calculation(self):
        """Test similarity calculation."""
        from src.embeddings import EmbeddingModel
        
        pytest.importorskip("sentence_transformers")
        
        model = EmbeddingModel(model_name="all-MiniLM-L6-v2")
        
        sim = model.similarity("test text", "test text")
        assert sim > 0.9  # Should be very similar
        
        diff = model.similarity("test text", "different text")
        assert 0 <= diff < 0.9


class TestIngestion:
    """Tests for data ingestion module."""
    
    def test_mock_data_loading(self, config):
        """Test loading mock data."""
        from src.ingestion import XDataIngestor
        
        ingestor = XDataIngestor(use_mock=True)
        df = ingestor.load_mock_data()
        
        assert df is not None
        assert isinstance(df, pd.DataFrame) or len(df.columns) > 0
    
    def test_sample_data_creation(self):
        """Test creating sample mock data."""
        from src.ingestion import create_sample_mock_data
        import os
        
        test_path = "/tmp/test_sample_x_data.csv"
        create_sample_mock_data(test_path)
        
        assert os.path.exists(test_path)
        
        # Clean up
        os.remove(test_path)
    
    def test_empty_dataframe_creation(self):
        """Test creating empty dataframe."""
        from src.ingestion import XDataIngestor
        import pandas as pd
        
        ingestor = XDataIngestor(use_mock=True)
        df = ingestor._create_empty_dataframe()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert "tweet_id" in df.columns
        assert "text" in df.columns


class TestQdrantSetup:
    """Tests for Qdrant setup module."""
    
    def test_client_creation(self, config):
        """Test creating Qdrant client."""
        from src.qdrant_setup import create_qdrant_client
        
        client = create_qdrant_client(config)
        assert client is not None
    
    def test_collection_creation(self, qdrant_client, config):
        """Test creating collections."""
        from src.qdrant_setup import _create_collection_if_not_exists
        
        # Test creating test collection
        test_collection = "test_collection"
        _create_collection_if_not_exists(
            qdrant_client,
            test_collection,
            384,  # Typical embedding size
            "Test collection"
        )
        
        assert qdrant_client.collection_exists(test_collection)
        
        # Clean up
        qdrant_client.delete_collection(test_collection)
    
    def test_list_collections(self, qdrant_client):
        """Test listing collections."""
        from src.qdrant_setup import list_collections
        
        collections = list_collections(qdrant_client)
        assert isinstance(collections, list)


class TestSearch:
    """Tests for search module."""
    
    def test_hybrid_searcher_creation(self, qdrant_client):
        """Test creating hybrid searcher."""
        from src.search import HybridSearcher
        
        searcher = HybridSearcher(qdrant_client)
        assert searcher is not None
        assert searcher.config is not None
    
    def test_filter_building(self, qdrant_client):
        """Test building Qdrant filters."""
        from src.search import HybridSearcher
        
        searcher = HybridSearcher(qdrant_client)
        
        # Test location filter
        filter_obj = searcher._build_filter({"location": "Mumbai"})
        assert filter_obj is not None
        
        # Test empty filter
        empty_filter = searcher._build_filter({})
        assert empty_filter is None
    
    def test_post_processing(self, qdrant_client):
        """Test post-processing search results."""
        from src.search import HybridSearcher
        from qdrant_client import models
        
        pytest.importorskip("sentence_transformers")
        
        searcher = HybridSearcher(qdrant_client)
        
        # Create mock results
        mock_results = [
            models.ScoredPoint(
                id="1",
                version=0,
                score=0.9,
                payload={"text": "test"}
            ),
            models.ScoredPoint(
                id="2",
                version=0,
                score=0.7,
                payload={"text": "test"}
            ),
            models.ScoredPoint(
                id="3",
                version=0,
                score=0.5,
                payload={"text": "test"}
            )
        ]
        
        filtered = searcher._post_process(
            mock_results,
            score_threshold=0.6,
            limit=2
        )
        
        assert len(filtered) == 2
        assert filtered[0].score >= filtered[1].score


class TestTimelineBuilder:
    """Tests for timeline builder module."""
    
    def test_timeline_builder_creation(self, qdrant_client):
        """Test creating timeline builder."""
        from src.timeline_builder import TimelineBuilder
        
        builder = TimelineBuilder(qdrant_client)
        assert builder is not None
        assert builder.search_limit == 10
    
    @pytest.mark.skipif(
        sys.version_info < (3, 8),
        reason="Requires Python 3.8+"
    )
    def test_query_processing(self):
        """Test query processing."""
        try:
            from baml_client.sync_client import b
        except ImportError:
            pytest.skip("BAML client not available")
        
        processed = b.ProcessQuery("test query")
        
        assert processed is not None
        assert hasattr(processed, "original_query")
        assert hasattr(processed, "rewritten_query")


class TestAPI:
    """Tests for FastAPI endpoints."""
    
    from fastapi.testclient import TestClient
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from src.api import app
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert data["name"] == "Chronofact.ai"
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
    
    def test_config_endpoint(self, client):
        """Test config endpoint."""
        response = client.get("/api/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "collections" in data
        assert "search" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
