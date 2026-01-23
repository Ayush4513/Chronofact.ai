#!/usr/bin/env python3
"""
Production startup script for Render deployment.
Ensures proper port binding and error handling.
"""

import os
import sys
import logging

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    """Start the FastAPI application with proper port binding."""
    
    # Get port from environment
    port = int(os.getenv("PORT", "10000"))
    logger.info("=" * 60)
    logger.info(f"🚀 Starting Chronofact.ai on PORT={port}")
    logger.info(f"   Host: 0.0.0.0")
    logger.info(f"   Environment: PRODUCTION")
    logger.info("=" * 60)
    
    try:
        import uvicorn
        
        # Start uvicorn with proper configuration
        uvicorn.run(
            "src.api:app",
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True,
            workers=1,  # Single worker for free tier
            limit_concurrency=10,
            timeout_keep_alive=5
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

