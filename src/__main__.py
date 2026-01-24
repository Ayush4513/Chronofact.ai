#!/usr/bin/env python3
"""
Chronofact.ai - Module Entry Point
Allows running with: python -m src
"""

import os
import sys

def main():
    """Start the FastAPI application."""
    import uvicorn
    
    # Get port from environment variable (Render uses PORT env var, defaults to 10000)
    port = int(os.getenv("PORT", "10000"))
    host = "0.0.0.0"
    
    print("=" * 70, file=sys.stdout, flush=True)
    print("🚀 CHRONOFACT.AI - MODULE STARTUP", file=sys.stdout, flush=True)
    print(f"📍 Binding to: {host}:{port}", file=sys.stdout, flush=True)
    print(f"📍 PORT env var: {os.getenv('PORT', 'not set (using 10000)')}", file=sys.stdout, flush=True)
    print("=" * 70, file=sys.stdout, flush=True)
    sys.stdout.flush()
    
    uvicorn.run(
        "src.api:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
        access_log=True,
    )

if __name__ == "__main__":
    main()

