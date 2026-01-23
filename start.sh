#!/bin/bash

# Chronofact.ai - Complete Setup and Start Script
# Does everything needed to run the application

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting Chronofact.ai...${NC}"

# Check prerequisites
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

if ! command_exists python3 && ! command_exists python; then
    echo -e "${RED}❌ Python is not installed. Please install Python 3.11+${NC}"
    exit 1
fi

if ! command_exists uv; then
    echo -e "${YELLOW}⚠️  uv not found. Installing...${NC}"
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex" 2>/dev/null || {
            echo -e "${RED}❌ Failed to install uv. Please install manually from https://docs.astral.sh/uv/${NC}"
            exit 1
        }
    else
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Docker check - only required for local Qdrant mode
# Will be checked later if QDRANT_MODE=docker

# Setup virtual environment
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    cd "$PROJECT_DIR"
    uv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    source "$PROJECT_DIR/.venv/Scripts/activate"
else
    source "$PROJECT_DIR/.venv/bin/activate"
fi

# Install dependencies
if ! python -c "import fastapi" >/dev/null 2>&1; then
    echo -e "${YELLOW}📥 Installing dependencies...${NC}"
    cd "$PROJECT_DIR"
    uv sync
    echo -e "${GREEN}✅ Dependencies installed${NC}"
fi

# Generate BAML client
BAML_CLIENT_DIR="$PROJECT_DIR/baml_client/baml_client"
if [ ! -d "$BAML_CLIENT_DIR" ] || [ ! -f "$BAML_CLIENT_DIR/__init__.py" ]; then
    echo -e "${YELLOW}🔧 Generating BAML client...${NC}"
    cd "$PROJECT_DIR"
    
    # Check if baml-cli is available
    if ! uv run baml-cli --version >/dev/null 2>&1; then
        echo -e "${YELLOW}Installing baml-py...${NC}"
        uv pip install baml-py
    fi
    
    if ! uv run baml-cli generate; then
        echo -e "${RED}❌ BAML client generation failed${NC}"
        echo -e "${YELLOW}Please check baml_src/ for syntax errors${NC}"
        echo -e "${YELLOW}Or run manually: ./setup-qdrant.sh baml${NC}"
        exit 1
    fi
    
    # Verify generation
    if [ ! -f "$BAML_CLIENT_DIR/__init__.py" ]; then
        echo -e "${RED}❌ BAML client generation incomplete${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ BAML client generated${NC}"
fi

# Setup .env file if missing
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating template...${NC}"
    cat > "$PROJECT_DIR/.env" << EOF
GOOGLE_API_KEY=your-google-api-key-here
QDRANT_MODE=cloud
QDRANT_URL=https://cb88f687-08a5-4d37-83c6-87c4b9050f72.europe-west3-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key-here
EOF
    echo -e "${RED}❌ Please edit .env and add your GOOGLE_API_KEY and QDRANT_API_KEY, then run ./start.sh again${NC}"
    exit 1
fi

# Load .env
source "$PROJECT_DIR/.env"

# Check if GOOGLE_API_KEY is set
if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your-google-api-key-here" ]; then
    echo -e "${RED}❌ GOOGLE_API_KEY not set in .env file${NC}"
    echo -e "${YELLOW}Please edit .env and add your Google API key${NC}"
    exit 1
fi

# Setup Qdrant based on mode
cd "$PROJECT_DIR"
QDRANT_MODE="${QDRANT_MODE:-cloud}"

if [ "$QDRANT_MODE" = "docker" ]; then
    # Check Docker for local mode
    if ! command_exists docker; then
        echo -e "${RED}❌ Docker is required for local Qdrant mode. Please install Docker Desktop or use QDRANT_MODE=cloud${NC}"
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running. Please start Docker Desktop${NC}"
        exit 1
    fi
    
    # Setup Qdrant Docker
    echo -e "${YELLOW}🐳 Setting up Qdrant Docker...${NC}"
    
    # Start Qdrant container
    if ! docker ps --format '{{.Names}}' | grep -q "^chronofact-qdrant$"; then
        if command -v docker-compose >/dev/null 2>&1; then
            docker-compose -f docker-compose.simple.yml up -d qdrant
        elif docker compose version >/dev/null 2>&1; then
            docker compose -f docker-compose.simple.yml up -d qdrant
        fi
        
        echo -e "${YELLOW}⏳ Waiting for Qdrant to start...${NC}"
        for i in {1..30}; do
            if curl -f http://localhost:6333/ >/dev/null 2>&1; then
                break
            fi
            sleep 2
        done
        echo -e "${GREEN}✅ Qdrant Docker started${NC}"
    fi
elif [ "$QDRANT_MODE" = "cloud" ]; then
    # Check Qdrant Cloud credentials
    if [ -z "$QDRANT_URL" ] || [ "$QDRANT_URL" = "your-qdrant-url-here" ]; then
        echo -e "${RED}❌ QDRANT_URL not set in .env file${NC}"
        echo -e "${YELLOW}Please edit .env and add your Qdrant Cloud URL${NC}"
        exit 1
    fi
    
    if [ -z "$QDRANT_API_KEY" ] || [ "$QDRANT_API_KEY" = "your-qdrant-api-key-here" ]; then
        echo -e "${RED}❌ QDRANT_API_KEY not set in .env file${NC}"
        echo -e "${YELLOW}Please edit .env and add your Qdrant Cloud API key${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}☁️  Using Qdrant Cloud: $QDRANT_URL${NC}"
    
    # Test Qdrant Cloud connection using Python (more reliable than curl)
    echo -e "${YELLOW}🔗 Testing Qdrant Cloud connection...${NC}"
    if python -c "
from src.qdrant_setup import create_qdrant_client
from src.config import get_config
try:
    client = create_qdrant_client(get_config())
    collections = client.get_collections()
    print('✅ Qdrant Cloud connection successful')
    exit(0)
except Exception as e:
    print(f'⚠️  Could not verify Qdrant Cloud connection: {e}')
    exit(1)
" 2>/dev/null; then
        echo -e "${GREEN}✅ Qdrant Cloud connection verified${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not verify Qdrant Cloud connection (will try during init)${NC}"
    fi
fi

# Initialize Qdrant collections (only if not already initialized)
cd "$PROJECT_DIR"
if ! python -c "from src.qdrant_setup import create_qdrant_client; from src.config import get_config; client = create_qdrant_client(get_config()); cols = client.get_collections(); exit(0 if len(cols.collections) >= 3 else 1)" 2>/dev/null; then
    echo -e "${YELLOW}📊 Initializing Qdrant collections...${NC}"
    python -m src.cli init
    echo -e "${GREEN}✅ Collections initialized${NC}"
fi

# Ingest mock data (only if collection is empty)
cd "$PROJECT_DIR"
POST_COUNT=$(python -c "from src.qdrant_setup import create_qdrant_client; from src.config import get_config; client = create_qdrant_client(get_config()); info = client.get_collection('x_posts'); print(info.points_count)" 2>/dev/null || echo "0")
if [ "$POST_COUNT" = "0" ]; then
    echo -e "${YELLOW}📥 Ingesting mock data...${NC}"
    python -m src.cli ingest mock
    echo -e "${GREEN}✅ Mock data ingested${NC}"
fi

# Start backend
echo -e "${GREEN}📡 Starting backend on http://localhost:8000${NC}"
cd "$PROJECT_DIR"
export PYTHONIOENCODING=utf-8

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

# Start backend and redirect output to log file
python -m src.api > "$PROJECT_DIR/logs/backend.log" 2>&1 &
BACKEND_PID=$!

echo -e "${YELLOW}📝 Backend logs: tail -f logs/backend.log${NC}"
echo -e "${YELLOW}   Or view in real-time: watch -n 1 tail -20 logs/backend.log${NC}"

# Wait for backend to start
sleep 3

# Start frontend
echo -e "${GREEN}🌐 Starting frontend on http://localhost:3000${NC}"
cd "$PROJECT_DIR/frontend"

if ! command_exists bun; then
    echo -e "${RED}❌ Bun is not installed. Install from https://bun.sh${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Install frontend dependencies if needed
if [ ! -d "$PROJECT_DIR/frontend/node_modules" ]; then
    echo -e "${YELLOW}📥 Installing frontend dependencies...${NC}"
    bun install
fi

bun run server.ts &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}✅ All services started!${NC}"
echo -e "   Frontend: http://localhost:3000"
echo -e "   Backend:  http://localhost:8000"
if [ "$QDRANT_MODE" = "cloud" ] && [ -n "$QDRANT_URL" ]; then
    echo -e "   Qdrant:   $QDRANT_URL (Cloud)"
else
    echo -e "   Qdrant:   http://localhost:6333/dashboard"
fi
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping services...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    
    # Deactivate virtual environment
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# Wait for interrupt
trap cleanup INT TERM
wait
