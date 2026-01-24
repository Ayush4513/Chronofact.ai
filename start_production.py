#!/usr/bin/env python3
"""
Production startup script for Render deployment.
Ensures proper port binding and error handling.
"""

import os
import sys
import time

# Force immediate output flushing
os.environ["PYTHONUNBUFFERED"] = "1"

# Print immediately to stdout (before any imports that might hang)
print("=" * 70, flush=True)
print("🚀 CHRONOFACT.AI - PRODUCTION STARTUP", flush=True)
print("=" * 70, flush=True)

# Get port FIRST
port = int(os.getenv("PORT", "10000"))
host = "0.0.0.0"

print(f"📍 Will bind to: {host}:{port}", flush=True)
print(f"🐍 Python: {sys.version.split()[0]}", flush=True)
print(f"⏰ Start time: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}", flush=True)
print("=" * 70, flush=True)

def main():
    """Start the FastAPI application with proper port binding."""
    
    # Verify critical environment variables
    required_vars = ["GOOGLE_API_KEY", "QDRANT_URL", "QDRANT_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Missing env vars: {', '.join(missing_vars)}", flush=True)
    else:
        print("✅ All required environment variables present", flush=True)
    
    print("🔧 Importing uvicorn...", flush=True)
    
    try:
        import uvicorn
        from uvicorn.config import Config
        from uvicorn.server import Server
        import asyncio
        
        print("✅ Uvicorn imported successfully", flush=True)
        print(f"🚀 Starting server on {host}:{port}...", flush=True)
        sys.stdout.flush()
        
        # Use Config + Server for more control over startup
        config = Config(
            app="src.api:app",
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            workers=1,
            timeout_keep_alive=75,
            lifespan="on",
        )
        
        server = Server(config)
        
        # Run the server
        asyncio.run(server.serve())
        
    except ImportError as e:
        print(f"❌ Import error: {e}", flush=True)
        sys.exit(1)
    except OSError as e:
        print(f"❌ OS error (port binding): {e}", flush=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

