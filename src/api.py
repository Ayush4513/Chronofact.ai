"""
Chronofact.ai - API Module
FastAPI endpoints for timeline generation and verification.
Supports multimodal queries with text and images.
"""

import sys
print("=" * 60, file=sys.stderr)
print("🚀 Chronofact.ai API Module Loading...", file=sys.stderr)
print("=" * 60, file=sys.stderr)

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import base64
import io

try:
    from baml_client.baml_client import b
    from baml_client.baml_client.types import Timeline, CredibilityAssessment, MisinformationAnalysis, Recommendation, FollowUpQuestion
except ImportError:
    b = None
    Timeline = None
    CredibilityAssessment = None
    MisinformationAnalysis = None
    Recommendation = None
    FollowUpQuestion = None

from .config import get_config
from .timeline_builder import TimelineBuilder
from .qdrant_setup import create_qdrant_client

# Configure logging to stdout for Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    import os
    port = os.getenv("PORT", "8000")
    logger.info(f"Starting Chronofact.ai API on PORT={port}...")
    
    try:
        config = get_config()
        logger.info(f"Config loaded: QDRANT_MODE={config.QDRANT_MODE}")
        
        # Setup Qdrant with error handling
        try:
            app.state.qdrant_client = create_qdrant_client(config)
            app.state.timeline_builder = TimelineBuilder(
                app.state.qdrant_client
            )
            logger.info("Qdrant client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            app.state.qdrant_client = None
            app.state.timeline_builder = None
        
        # Setup multimodal embedder
        try:
            from .multimodal import MultimodalEmbedder
            app.state.multimodal_embedder = MultimodalEmbedder()
            app.state.multimodal_available = True
            logger.info("Multimodal embedder (CLIP) loaded successfully")
        except Exception as e:
            logger.warning(f"Multimodal embedder not available: {e}")
            app.state.multimodal_embedder = None
            app.state.multimodal_available = False
        
        if b is None:
            logger.warning("BAML client not available. Run: baml-cli generate")
            app.state.baml_available = False
        else:
            logger.info("BAML client loaded successfully")
            app.state.baml_available = True
        
        logger.info("API startup complete")
        
    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        # Set minimal state to allow app to start
        app.state.qdrant_client = None
        app.state.timeline_builder = None
        app.state.multimodal_embedder = None
        app.state.multimodal_available = False
        app.state.baml_available = False
    
    yield  # App runs here
    
    # Shutdown
    logger.info("Shutting down API...")
    # Qdrant client cleanup is automatic


app = FastAPI(
    title="Chronofact.ai API",
    description="AI-powered fact-based news service using Qdrant and BAML",
    version="0.1.0",
    lifespan=lifespan
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
    image_base64: Optional[str] = Field(None, description="Base64 encoded image for multimodal search")


class VerifyRequest(BaseModel):
    text: str = Field(..., description="Text content to verify")
    author: Optional[str] = Field(None, description="Author information")
    engagement: Optional[str] = Field(None, description="Engagement metrics")


class DetectRequest(BaseModel):
    text: str = Field(..., description="Text to analyze for misinformation")


class RecommendRequest(BaseModel):
    query: str = Field(..., description="Query to get recommendations for")
    limit: int = Field(5, ge=1, le=20, description="Number of recommendations")


class FollowUpRequest(BaseModel):
    original_query: str = Field(..., description="The original search query")
    timeline_topic: str = Field(..., description="Topic from the timeline")
    events_summary: List[str] = Field(default=[], description="List of event summaries")
    avg_credibility: float = Field(0.5, description="Average credibility score")
    total_events: int = Field(0, description="Total number of events")
    total_sources: int = Field(0, description="Total number of sources")
    previous_questions: List[str] = Field(default=[], description="Previously asked questions to avoid repetition")


class HealthResponse(BaseModel):
    status: str
    baml_available: bool
    qdrant_connected: bool
    multimodal_available: bool = False


@app.get("/favicon.ico")
async def favicon():
    """Return empty favicon to prevent 404 errors."""
    from fastapi.responses import Response
    return Response(content="", media_type="image/x-icon")


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
    
    multimodal_available = getattr(app.state, 'multimodal_available', False)
    
    return HealthResponse(
        status="healthy" if qdrant_connected else "degraded",
        baml_available=app.state.baml_available,
        qdrant_connected=qdrant_connected,
        multimodal_available=multimodal_available
    )


@app.post("/api/timeline", response_model=Timeline)
async def generate_timeline(request: QueryRequest) -> Timeline:
    """
    Generate a timeline for a given topic.
    Supports multimodal queries with optional image input.
    
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
        
        # Process image if provided
        query_image = None
        image_context = None
        if request.image_base64 and app.state.multimodal_available:
            try:
                from PIL import Image
                
                # Decode base64 image
                image_data = base64.b64decode(request.image_base64)
                query_image = Image.open(io.BytesIO(image_data))
                
                logger.info(f"Processing multimodal query with image ({query_image.size})")
                
                # Generate image description for context
                image_context = await _analyze_image_for_timeline(query_image, request.topic)
                
            except Exception as e:
                logger.warning(f"Failed to process image: {e}")
                # Continue without image if processing fails
        
        # Enhance query with image context if available
        enhanced_query = request.topic
        if image_context:
            enhanced_query = f"{request.topic}. Visual context: {image_context}"
            logger.info(f"Enhanced query with image context: {enhanced_query[:100]}...")
        
        # Generate timeline
        try:
            timeline = await builder.build_timeline(
                query=enhanced_query,
                limit=request.limit,
                filters=filters if filters else None
            )
            
            if timeline is None:
                raise HTTPException(
                    status_code=500,
                    detail="Timeline builder returned None. Check backend logs for details."
                )
            
            return timeline
        except RuntimeError as e:
            # Re-raise RuntimeError from timeline_builder with better context
            logger.error(f"Timeline builder error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Timeline generation failed: {str(e)}"
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Timeline generation error: {e}", exc_info=True)
        # Provide more detailed error message
        error_detail = str(e)
        error_type = type(e).__name__
        
        # Add context based on error type
        if "BAML" in error_detail or "baml" in error_detail.lower() or "coroutine" in error_detail.lower():
            error_detail = f"BAML error: {error_detail}. Ensure BAML client is generated and functions are awaited."
        elif "Qdrant" in error_detail or "qdrant" in error_detail.lower():
            error_detail = f"Qdrant error: {error_detail}. Check Qdrant connection and data."
        elif "API" in error_detail or "api" in error_detail.lower() or "key" in error_detail.lower():
            error_detail = f"API error: {error_detail}. Check Google API key."
        elif "timeout" in error_detail.lower():
            error_detail = f"Timeout error: {error_detail}. The request took too long."
        else:
            # Include error type for debugging
            error_detail = f"{error_type}: {error_detail}"
        
        raise HTTPException(
            status_code=500,
            detail=f"Error generating timeline: {error_detail}"
        )


async def _analyze_image_for_timeline(image, topic: str) -> Optional[str]:
    """
    Analyze image using Gemini to extract relevant context for timeline generation.
    """
    try:
        import google.generativeai as genai
        from .config import get_config
        
        config = get_config()
        genai.configure(api_key=config.google_ai.api_key)
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""Analyze this image in the context of: "{topic}"

Describe what you see that is relevant to the topic. Focus on:
- Key visual elements (people, places, events, objects)
- Any text or signs visible
- The setting and context
- Time indicators (day/night, weather, season)
- Any notable actions or events happening

Be concise but specific. Return only the description, no preamble."""

        response = model.generate_content([prompt, image])
        
        if response.text:
            return response.text.strip()[:500]  # Limit context length
        return None
        
    except Exception as e:
        logger.warning(f"Image analysis failed: {e}")
        return None


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


@app.post("/api/followup")
async def get_follow_up_questions(request: FollowUpRequest) -> Dict[str, Any]:
    """
    Generate context-aware follow-up questions based on timeline results.
    
    These questions help users continue their investigation with relevant,
    intelligent follow-up queries derived from the current context.
    """
    if not app.state.baml_available:
        raise HTTPException(
            status_code=503,
            detail="BAML client not available"
        )
    
    try:
        # Build timeline summary
        timeline_summary = f"""
Topic: {request.timeline_topic}
Total Events: {request.total_events}
Total Sources: {request.total_sources}
Average Credibility: {request.avg_credibility:.1%}
"""
        
        # Build credibility summary
        if request.avg_credibility >= 0.7:
            credibility_summary = f"High credibility ({request.avg_credibility:.0%}) - Most sources are verified and consistent"
        elif request.avg_credibility >= 0.4:
            credibility_summary = f"Moderate credibility ({request.avg_credibility:.0%}) - Some claims need verification"
        else:
            credibility_summary = f"Low credibility ({request.avg_credibility:.0%}) - Many unverified claims, exercise caution"
        
        # Extract entities from events (simple extraction)
        entities = []
        for event in request.events_summary[:5]:  # Limit to first 5 events
            # Simple entity extraction from event summaries
            words = event.split()
            for word in words:
                if word[0].isupper() and len(word) > 2 and word not in entities:
                    entities.append(word)
            if len(entities) >= 10:
                break
        
        # Generate follow-up questions
        questions = await b.GenerateFollowUpQuestions(
            original_query=request.original_query,
            timeline_summary=timeline_summary,
            key_events=request.events_summary[:5],  # Limit events
            entities_found=entities[:10],  # Limit entities
            credibility_summary=credibility_summary,
            previous_questions=request.previous_questions if request.previous_questions else None
        )
        
        return {
            "query": request.original_query,
            "count": len(questions),
            "questions": [q.model_dump() for q in questions]
        }
        
    except Exception as e:
        logger.error(f"Follow-up generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating follow-up questions: {str(e)}"
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
    import os
    
    # Get port from environment variable (Render uses PORT env var)
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )
