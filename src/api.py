"""
Chronofact.ai - API Module
FastAPI endpoints for timeline generation and verification.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

try:
    from baml_client.baml_client import b
    from baml_client.baml_client.types import Timeline, CredibilityAssessment, MisinformationAnalysis, Recommendation
except ImportError:
    b = None
    Timeline = None
    CredibilityAssessment = None
    MisinformationAnalysis = None
    Recommendation = None

from .config import get_config
from .timeline_builder import TimelineBuilder
from .qdrant_setup import create_qdrant_client

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Chronofact.ai API",
    description="AI-powered fact-based news service using Qdrant and BAML",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API
class QueryRequest(BaseModel):
    topic: str = Field(..., description="Topic or query to search for")
    limit: int = Field(10, ge=1, le=50, description="Number of events in timeline")
    location: Optional[str] = Field(None, description="Filter by location")
    min_credibility: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum credibility score")
    include_media_only: bool = Field(False, description="Only include events with media")


class VerifyRequest(BaseModel):
    text: str = Field(..., description="Text content to verify")
    author: Optional[str] = Field(None, description="Author information")
    engagement: Optional[str] = Field(None, description="Engagement metrics")


class DetectRequest(BaseModel):
    text: str = Field(..., description="Text to analyze for misinformation")


class RecommendRequest(BaseModel):
    query: str = Field(..., description="Query to get recommendations for")
    limit: int = Field(5, ge=1, le=20, description="Number of recommendations")


class HealthResponse(BaseModel):
    status: str
    baml_available: bool
    qdrant_connected: bool


# Initialize components on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application components."""
    logger.info("Starting Chronofact.ai API...")
    
    config = get_config()
    
    # Setup Qdrant
    app.state.qdrant_client = create_qdrant_client(config)
    app.state.timeline_builder = TimelineBuilder(
        app.state.qdrant_client
    )
    
    if b is None:
        logger.warning("BAML client not available. Run: uv run baml-cli generate")
        app.state.baml_available = False
    else:
        logger.info("BAML client loaded successfully")
        app.state.baml_available = True
    
    logger.info("API startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down API...")
    # Qdrant client cleanup is automatic


@app.get("/", response_model=Dict[str, str])
async def root() -> Dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "Chronofact.ai",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    qdrant_connected = False
    
    try:
        app.state.qdrant_client.get_collections()
        qdrant_connected = True
    except Exception as e:
        logger.warning(f"Qdrant health check failed: {e}")
    
    return HealthResponse(
        status="healthy" if qdrant_connected else "degraded",
        baml_available=app.state.baml_available,
        qdrant_connected=qdrant_connected
    )


@app.post("/api/timeline", response_model=Timeline)
async def generate_timeline(request: QueryRequest) -> Timeline:
    """
    Generate a timeline for a given topic.
    
    Returns a Timeline object with chronological events and metadata.
    """
    if not app.state.baml_available:
        raise HTTPException(
            status_code=503,
            detail="BAML client not available. Run: uv run baml-cli generate"
        )
    
    try:
        builder = app.state.timeline_builder
        
        # Build filters
        filters = {}
        if request.location:
            filters["location"] = request.location
        if request.min_credibility:
            filters["min_credibility"] = request.min_credibility
        if request.include_media_only:
            filters["include_media_only"] = True
        
        # Generate timeline
        timeline = builder.build_timeline(
            query=request.topic,
            limit=request.limit,
            filters=filters if filters else None
        )
        
        if timeline is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate timeline"
            )
        
        return timeline
        
    except Exception as e:
        logger.error(f"Timeline generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating timeline: {str(e)}"
        )


@app.post("/api/verify")
async def verify_claim(request: VerifyRequest) -> Dict[str, Any]:
    """
    Verify credibility of a claim or post.
    
    Returns credibility assessment with factors and reasoning.
    """
    if not app.state.baml_available:
        raise HTTPException(
            status_code=503,
            detail="BAML client not available"
        )
    
    try:
        assessment = await b.AssessCredibility(
            post_text=request.text,
            author_info=request.author or "Unknown",
            engagement=request.engagement or "No engagement data",
            knowledge_context=None
        )
        
        return assessment.model_dump()
        
    except Exception as e:
        logger.error(f"Verification error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error verifying claim: {str(e)}"
        )


@app.post("/api/detect")
async def detect_misinformation(request: DetectRequest) -> Dict[str, Any]:
    """
    Detect potential misinformation patterns in text.
    
    Returns analysis with risk level and detected patterns.
    """
    if not app.state.baml_available:
        raise HTTPException(
            status_code=503,
            detail="BAML client not available"
        )
    
    try:
        result = await b.DetectMisinformation(text=request.text)
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"Detection error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error detecting misinformation: {str(e)}"
        )


@app.post("/api/recommend")
async def get_recommendations(request: RecommendRequest) -> Dict[str, Any]:
    """
    Get context-aware recommendations for a query.
    
    Returns list of recommendations with reasons.
    """
    if not app.state.baml_available:
        raise HTTPException(
            status_code=503,
            detail="BAML client not available"
        )
    
    try:
        recommendations = await b.GenerateRecommendations(
            query=request.query,
            timeline=None,
            user_session=None
        )
        
        return {
            "query": request.query,
            "count": len(recommendations),
            "recommendations": [r.model_dump() for r in recommendations]
        }
        
    except Exception as e:
        logger.error(f"Recommendation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )


@app.get("/api/config")
async def get_config_info() -> Dict[str, Any]:
    """
    Get current configuration.
    
    Returns configuration settings (excluding sensitive data).
    """
    config = get_config()
    
    return {
        "collections": {
            "posts": config.collection_posts,
            "knowledge": config.collection_knowledge,
            "memory": config.collection_memory
        },
        "search": {
            "default_limit": config.default_search_limit,
            "min_credibility": config.min_credibility
        },
        "qdrant": {
            "mode": config.qdrant.mode,
            "host": config.qdrant.host,
            "port": config.qdrant.port
        },
        "baml_available": app.state.baml_available
    }


@app.post("/api/search")
async def search_posts(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    filters: Optional[str] = Query(None, description="JSON filter string")
) -> Dict[str, Any]:
    """
    Search posts in Qdrant.
    
    Returns search results with scores and payloads.
    """
    from .search import HybridSearcher
    
    try:
        searcher = HybridSearcher(app.state.qdrant_client)
        
        # Parse filters
        filter_dict = {}
        if filters:
            import json
            filter_dict = json.loads(filters)
        
        results = searcher.search(
            query=query,
            limit=limit,
            filters=filter_dict if filter_dict else None
        )
        
        return {
            "query": query,
            "count": len(results),
            "results": [
                {
                    "id": r.id,
                    "score": r.score,
                    "payload": r.payload
                }
                for r in results
            ]
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error searching: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
