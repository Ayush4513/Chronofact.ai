#!/usr/bin/env python3
"""
Production startup script for Render deployment.
Ensures proper port binding and error handling.
"""

import os
import sys
import logging
import time

# Configure logging first - send to stdout for Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True  # Override any existing logging config
)
logger = logging.getLogger(__name__)

def main():
    """Start the FastAPI application with proper port binding."""
    
    # Get port from environment - Render sets PORT automatically
    port = int(os.getenv("PORT", "10000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info("=" * 70)
    logger.info("🚀 CHRONOFACT.AI - PRODUCTION STARTUP")
    logger.info("=" * 70)
    logger.info(f"📍 Binding to: {host}:{port}")
    logger.info(f"🌍 Environment: PRODUCTION")
    logger.info(f"🐍 Python: {sys.version.split()[0]}")
    logger.info(f"⏰ Start time: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logger.info("=" * 70)
    
    # Verify critical environment variables
    required_vars = ["GOOGLE_API_KEY", "QDRANT_URL", "QDRANT_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("⚠️  Some features may not work properly")
    else:
        logger.info("✅ All required environment variables present")
    
    try:
        import uvicorn
        
        logger.info("🔧 Starting Uvicorn server...")
        
        # Start uvicorn with Render-optimized configuration
        uvicorn.run(
            "src.api:app",
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            workers=1,  # Single worker for free tier
            limit_concurrency=10,
            timeout_keep_alive=75,  # Render timeout is 95s
            forwarded_allow_ips="*",  # Trust Render's proxy headers
        )
        
    except ImportError as e:
        logger.error(f"❌ Import error - missing dependency: {e}", exc_info=True)
        logger.error("💡 Try: pip install uvicorn[standard]")
        sys.exit(1)
    except OSError as e:
        logger.error(f"❌ OS error - port binding failed: {e}", exc_info=True)
        logger.error(f"💡 Port {port} may be in use or permission denied")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

