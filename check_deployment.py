#!/usr/bin/env python3
"""
Render Deployment Diagnostic Script
Run this to verify your environment is correctly configured for Render deployment.
"""

import os
import sys
import socket

# Load .env file if it exists (for local testing)
try:
    from dotenv import load_dotenv
    if os.path.exists(".env"):
        load_dotenv()
        print("📄 Loaded environment variables from .env file")
    else:
        print("ℹ️  No .env file found (this is OK for Render - env vars set in dashboard)")
except ImportError:
    print("ℹ️  python-dotenv not installed, skipping .env file loading")
    print("   Install with: pip install python-dotenv")

def check_environment():
    """Check if all required environment variables are set."""
    print("=" * 70)
    print("🔍 ENVIRONMENT VARIABLES CHECK")
    print("=" * 70)
    
    required_vars = {
        "GOOGLE_API_KEY": "Required for AI timeline generation",
        "QDRANT_URL": "Required for vector database connection",
        "QDRANT_API_KEY": "Required for Qdrant authentication",
    }
    
    optional_vars = {
        "PORT": "Port to bind (defaults to 10000)",
        "QDRANT_MODE": "Should be 'cloud' for production",
    }
    
    all_good = True
    
    print("\n📋 Required Variables:")
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked = f"{value[:8]}..." if len(value) > 8 else "***"
            print(f"  ✅ {var}: {masked} ({description})")
        else:
            print(f"  ❌ {var}: NOT SET - {description}")
            all_good = False
    
    print("\n📋 Optional Variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {value} ({description})")
        else:
            default = "10000" if var == "PORT" else "N/A"
            print(f"  ⚠️  {var}: NOT SET (will use default: {default}) - {description}")
    
    return all_good

def check_port():
    """Check if the port is available."""
    print("\n" + "=" * 70)
    print("🔌 PORT AVAILABILITY CHECK")
    print("=" * 70)
    
    port = int(os.getenv("PORT", "10000"))
    host = "0.0.0.0"
    
    print(f"\n🎯 Testing port binding: {host}:{port}")
    
    try:
        # Try to bind to the port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.close()
        print(f"  ✅ Port {port} is available and can be bound")
        return True
    except socket.error as e:
        print(f"  ❌ Port {port} is NOT available: {e}")
        print(f"  💡 Try a different port or stop the service using port {port}")
        return False

def check_dependencies():
    """Check if all required Python packages are installed."""
    print("\n" + "=" * 70)
    print("📦 DEPENDENCIES CHECK")
    print("=" * 70)
    
    # Map of display name -> actual import name
    required_packages = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "qdrant-client": "qdrant_client",
        "google-generativeai": "google.generativeai",
        "baml-py": "baml_py",
        "sentence-transformers": "sentence_transformers",
    }
    
    all_installed = True
    
    print("\n📚 Required Packages:")
    for display_name, import_name in required_packages.items():
        try:
            # Handle nested imports like google.generativeai
            if "." in import_name:
                parts = import_name.split(".")
                module = __import__(parts[0])
                for part in parts[1:]:
                    module = getattr(module, part)
            else:
                __import__(import_name)
            print(f"  ✅ {display_name}: installed")
        except (ImportError, AttributeError):
            print(f"  ❌ {display_name}: NOT INSTALLED")
            all_installed = False
    
    return all_installed

def check_files():
    """Check if required files exist."""
    print("\n" + "=" * 70)
    print("📁 FILES CHECK")
    print("=" * 70)
    
    required_files = [
        "start_production.py",
        "src/api.py",
        "baml_src",
        "requirements.txt",
    ]
    
    all_exist = True
    
    print("\n📄 Required Files:")
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}: exists")
        else:
            print(f"  ❌ {file}: NOT FOUND")
            all_exist = False
    
    return all_exist

def check_qdrant_connection():
    """Check if Qdrant is accessible."""
    print("\n" + "=" * 70)
    print("🗄️  QDRANT CONNECTION CHECK")
    print("=" * 70)
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    if not qdrant_url or not qdrant_api_key:
        print("  ⚠️  Qdrant credentials not set, skipping connection test")
        return False
    
    try:
        from qdrant_client import QdrantClient
        
        print(f"\n🔗 Connecting to: {qdrant_url}")
        client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=10
        )
        
        collections = client.get_collections()
        print(f"  ✅ Connected successfully!")
        print(f"  📊 Found {len(collections.collections)} collections")
        
        for collection in collections.collections:
            print(f"     - {collection.name} ({collection.vectors_count} vectors)")
        
        return True
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        print(f"  💡 Check your QDRANT_URL and QDRANT_API_KEY")
        return False

def main():
    """Run all diagnostic checks."""
    print("\n")
    print("🏥 " + "=" * 66)
    print("🏥  CHRONOFACT.AI - RENDER DEPLOYMENT DIAGNOSTIC")
    print("🏥 " + "=" * 66)
    print()
    
    checks = [
        ("Environment Variables", check_environment),
        ("Port Availability", check_port),
        ("Dependencies", check_dependencies),
        ("Files", check_files),
        ("Qdrant Connection", check_qdrant_connection),
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n  ❌ Error during {name} check: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    print("\n✅ Passed Checks:")
    for name, passed in results.items():
        if passed:
            print(f"  • {name}")
    
    print("\n❌ Failed Checks:")
    failed = [name for name, passed in results.items() if not passed]
    if failed:
        for name in failed:
            print(f"  • {name}")
    else:
        print("  None! All checks passed! 🎉")
    
    print("\n" + "=" * 70)
    
    if all(results.values()):
        print("✅ READY FOR DEPLOYMENT!")
        print("\nNext steps:")
        print("  1. Commit and push changes to GitHub")
        print("  2. Deploy to Render")
        print("  3. Monitor logs: Dashboard → Logs")
        print("  4. Test health endpoint: curl https://your-service.onrender.com/health")
        return 0
    else:
        print("⚠️  SOME CHECKS FAILED")
        print("\n💡 Tips:")
        print("  • Missing dependencies? Activate your venv first:")
        print("    - Windows: .venv\\Scripts\\activate")
        print("    - Linux/Mac: source .venv/bin/activate")
        print("  • Then run: pip install -r requirements.txt")
        print("  • Environment variables will be set in Render dashboard")
        print("  • Local .env file is NOT needed for Render deployment")
        return 1

if __name__ == "__main__":
    sys.exit(main())

