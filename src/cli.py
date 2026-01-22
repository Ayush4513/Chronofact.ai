"""
Chronofact.ai - CLI Module
Command-line interface for timeline generation and querying.
"""

import typer
from typing import Optional
import sys
import asyncio

# Import BAML client
try:
    from baml_client.baml_client import b
    from baml_client.baml_client.types import Timeline, MisinformationAnalysis, CredibilityAssessment, Recommendation, ProcessedQuery
except ImportError:
    b = None
    Timeline = None
    MisinformationAnalysis = None
    CredibilityAssessment = None
    Recommendation = None
    ProcessedQuery = None

app = typer.Typer(
    name="xtimeline",
    help="Chronofact.ai - Build fact-based timelines from X data",
    add_completion=False
)


@app.command()
def query(
    topic: str = typer.Argument(..., help="Topic or query to search for"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of events in timeline"),
    location: Optional[str] = typer.Option(None, "--location", help="Filter by location"),
    min_credibility: Optional[float] = typer.Option(None, "--min-credibility", "-c", help="Minimum credibility score (0.0-1.0)"),
    output: str = typer.Option("json", "--output", "-o", help="Output format: json, pretty, or compact"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """
    Generate a timeline for a given topic.
    
    Example:
        xtimeline query "Mumbai floods 2026" --limit 15 --location Mumbai
    """
    if b is None:
        typer.echo("❌ BAML client not available. Run: uv run baml-cli generate", err=True)
        sys.exit(1)

    typer.echo(f"\n🔍 Generating timeline for: {topic}\n")
    typer.echo(f"   Limit: {limit}")
    if location:
        typer.echo(f"   Location filter: {location}")
    if min_credibility:
        typer.echo(f"   Min credibility: {min_credibility}")

    # First, search Qdrant for relevant context
    from .search import HybridSearcher
    from .qdrant_setup import create_qdrant_client
    
    try:
        client = create_qdrant_client()
        searcher = HybridSearcher(client)
        
        results = searcher.search(
            query=topic,
            limit=min(limit * 5, 50),
            filters={"location": location} if location else None
        )
        
        # Build context string from search results
        context_parts = []
        for r in results[:limit * 3]:
            payload = r.payload or {}
            context_parts.append(
                f"- [{payload.get('author', 'unknown')}] {payload.get('text', '')[:200]}"
            )
        retrieved_context = "\n".join(context_parts) if context_parts else "No relevant posts found."
        
    except Exception as e:
        typer.echo(f"⚠️  Search failed, using empty context: {e}")
        retrieved_context = ""

    async def generate_timeline():
        return await b.GenerateTimeline(
            query=topic,
            retrieved_context=retrieved_context,
            num_events=limit
        )

    timeline = run_async_baml(generate_timeline())

    typer.echo(f"\n📊 Timeline: {topic}")
    typer.echo(f"   Events: {len(timeline.events)}")
    typer.echo(f"   Avg Credibility: {timeline.avg_credibility * 100:.1f}%")
    typer.echo(f"   Total Sources: {timeline.total_sources}")

    typer.echo("\n📅 Events:\n")
    for i, event in enumerate(timeline.events, 1):
        cred_percent = event.credibility_score * 100
        typer.echo(f"{i}. [{cred_percent:.0f}%] {event.summary}")
        typer.echo(f"   📅 {event.timestamp}")
        if event.location:
            typer.echo(f"   📍 {event.location}")
        typer.echo(f"   📎 Sources: {', '.join(event.sources[:3])}")
        typer.echo()

    if verbose:
        typer.echo("\n📋 Full timeline:")
        typer.echo(timeline.model_dump_json(indent=2))


def run_async_baml(func):
    """Helper to run async BAML functions in sync context."""
    try:
        return asyncio.run(func)
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

@app.command()
def verify(
    text: str = typer.Option(..., "--text", "-t", help="Text to verify"),
    author: Optional[str] = typer.Option(None, "--author", "-a", help="Author information"),
    engagement: Optional[str] = typer.Option(None, "--engagement", "-e", help="Engagement metrics"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """
    Verify credibility of a claim or post.

    Example:
        xtimeline verify --text "Schools are closing tomorrow due to floods" --author randomuser123
    """
    if b is None:
        typer.echo("❌ BAML client not available. Run: uv run baml-cli generate", err=True)
        sys.exit(1)

    typer.echo(f"\n🔎 Verifying claim: {text[:50]}...\n")

    async def assess_credibility():
        return await b.AssessCredibility(
            post_text=text,
            author_info=author or "Unknown",
            engagement=engagement or "No engagement data",
            knowledge_context=None
        )

    # Use BAML to assess credibility
    assessment = run_async_baml(assess_credibility())

    typer.echo(f"\n📊 Credibility Score: {assessment.credibility_score * 100:.1f}%")

    typer.echo("\n📋 Factors:")
    for factor in assessment.factors:
        typer.echo(f"   • {factor}")

    typer.echo("\n💭 Reasoning:")
    typer.echo(f"   {assessment.reasoning}")

    if verbose:
        typer.echo("\n📋 Full assessment:")
        typer.echo(assessment.model_dump_json(indent=2))


@app.command()
def detect(
    text: str = typer.Option(..., "--text", "-t", help="Text to analyze"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """
    Detect potential misinformation patterns in text.

    Example:
        xtimeline detect --text "This is HUGE news they're hiding from you!!!"
    """
    if b is None:
        typer.echo("❌ BAML client not available. Run: uv run baml-cli generate", err=True)
        sys.exit(1)

    typer.echo("\n🔍 Analyzing for misinformation patterns...\n")

    async def detect_misinfo():
        return await b.DetectMisinformation(text=text)

    # Use BAML to detect misinformation
    result = run_async_baml(detect_misinfo())

    typer.echo(f"\n🎯 Risk Level: {result.risk_level.upper()}")

    if result.is_suspicious:
        typer.echo("\n⚠️  Suspicious patterns detected:")
        for pattern in result.suspicious_patterns:
            typer.echo(f"   • {pattern}")
    else:
        typer.echo("\n✅ No obvious suspicious patterns")

    typer.echo("\n💡 Recommendation:")
    typer.echo(f"   {result.recommendation}")

    if verbose:
        typer.echo("\n📋 Full analysis:")
        typer.echo(result.model_dump_json(indent=2))


@app.command()
def recommend(
    query: str = typer.Argument(..., help="Query to get recommendations for"),
    limit: int = typer.Option(3, "--limit", "-l", help="Number of recommendations"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """
    Get context-aware recommendations for a query.

    Example:
        xtimeline recommend "Maharashtra elections" --limit 5
    """
    if b is None:
        typer.echo("❌ BAML client not available. Run: uv run baml-cli generate", err=True)
        sys.exit(1)

    typer.echo(f"\n💡 Generating recommendations for: {query}\n")

    async def get_recommendations():
        return await b.GenerateRecommendations(
            query=query,
            timeline=None,
            user_session=None
        )

    # Use BAML to generate recommendations
    recommendations = run_async_baml(get_recommendations())

    typer.echo("\n💡 Recommendations:\n")
    for i, rec in enumerate(recommendations, 1):
        typer.echo(f"{i}. {rec.action}")
        typer.echo(f"   Why: {rec.reason}")
        typer.echo()

    if verbose:
        typer.echo("\n📋 Full recommendations:")
        for rec in recommendations:
            typer.echo(rec.model_dump_json(indent=2))
            typer.echo()


@app.command()
def ingest(
    source: str = typer.Argument(..., help="Data source: 'mock' or 'scrape'"),
    topic: Optional[str] = typer.Option(None, "--topic", "-t", help="Topic for scraping"),
    max_posts: int = typer.Option(100, "--max", "-m", help="Maximum posts to scrape"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output CSV path")
):
    """
    Ingest X data into the system.
    
    Example:
        xtimeline ingest mock
        xtimeline ingest scrape --topic "Mumbai floods" --max 50
    """
    import os
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    typer.echo(f"\n📥 Ingesting data from: {source}\n")
    
    if source == "mock":
        from .ingestion import create_sample_mock_data, XDataIngestor
        from .qdrant_setup import create_qdrant_client
        from .embeddings import get_embedding_model
        from qdrant_client import models
        import hashlib
        
        output_path = output or "./data/sample_x_data.csv"
        create_sample_mock_data(output_path)
        typer.echo(f"✅ Created: {output_path}")
        
        # Now upsert to Qdrant
        typer.echo("\n📤 Upserting mock data to Qdrant...")
        try:
            from .config import get_config
            config = get_config()
            client = create_qdrant_client(config)
            ingestor = XDataIngestor(use_mock=True)
            df = ingestor.load_mock_data(output_path)
            
            if df.empty:
                typer.echo("❌ No data to upsert", err=True)
                return
            
            embedding_model = get_embedding_model()
            points = []
            
            for idx, row in df.iterrows():
                text = str(row.get("text", ""))
                if not text:
                    continue
                
                embedding = embedding_model.encode(text)
                tweet_id = str(row.get("tweet_id", f"mock_{idx}"))
                point_id = int(hashlib.md5(tweet_id.encode()).hexdigest()[:8], 16)
                
                import ast
                media_urls = row.get("media_urls", "[]")
                if isinstance(media_urls, str):
                    try:
                        media_urls = ast.literal_eval(media_urls)
                    except:
                        media_urls = []
                
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
            
            if points:
                client.upsert(
                    collection_name=config.collection_posts,
                    points=points
                )
                typer.echo(f"✅ Upserted {len(points)} records to Qdrant collection 'x_posts'")
            else:
                typer.echo("❌ No valid points to upsert", err=True)
                
        except Exception as e:
            typer.echo(f"❌ Error upserting to Qdrant: {e}", err=True)
            import traceback
            traceback.print_exc()
    
    elif source == "scrape":
        if not topic:
            typer.echo("❌ --topic is required for scraping", err=True)
            sys.exit(1)
        
        from .ingestion import XDataIngestor
        ingestor = XDataIngestor()
        df = ingestor.scrape_topic(topic, max_posts=max_posts)
        
        output_path = output or f"./data/{topic.replace(' ', '_')}_posts.csv"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        typer.echo(f"✅ Scraped {len(df)} posts to: {output_path}")
    
    else:
        typer.echo(f"❌ Unknown source: {source}. Use 'mock' or 'scrape'", err=True)
        sys.exit(1)


@app.command()
def init():
    """
    Initialize XTimeline environment.
    
    Sets up Qdrant collections and downloads embedding model.
    """
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    typer.echo("\n🚀 Initializing Chronofact.ai...\n")
    
    # Setup Qdrant
    typer.echo("Setting up Qdrant collections...")
    from .qdrant_setup import setup_collections
    
    try:
        setup_collections()
        typer.echo("✅ Collections ready")
    except Exception as e:
        typer.echo(f"⚠️  Qdrant setup skipped: {e}")
    
    # Initialize embedding model
    typer.echo("\nLoading embedding model...")
    from .embeddings import get_embedding_model
    
    try:
        model = get_embedding_model()
        typer.echo(f"✅ Model loaded: {model.model_name}")
        typer.echo(f"   Vector size: {model.vector_size}")
    except Exception as e:
        typer.echo(f"⚠️  Model loading skipped: {e}")
    
    typer.echo("\n✨ Initialization complete!\n")
    
    typer.echo("\n📝 Note: BAML integration is currently disabled.")
    typer.echo("   To enable BAML functionality:")
    typer.echo("   1. Fix BAML syntax issues in baml_src/")
    typer.echo("   2. Run: uv run baml-cli generate")
    typer.echo("   3. Restart the application")


if __name__ == "__main__":
    app()
