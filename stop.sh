#!/bin/bash

# Chronofact.ai - Stop Script
# Stops all running services

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Colors
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${YELLOW}🛑 Stopping Chronofact.ai services...${NC}"

# Stop backend (Python processes)
pkill -f "python -m src.api" 2>/dev/null && echo -e "${GREEN}✅ Backend stopped${NC}" || true

# Stop frontend (Bun processes)
pkill -f "bun.*server.ts" 2>/dev/null && echo -e "${GREEN}✅ Frontend stopped${NC}" || true

# Stop Qdrant Docker (only if in docker mode)
cd "$PROJECT_DIR"
if [ -f "$PROJECT_DIR/.env" ]; then
    source "$PROJECT_DIR/.env"
    if [ "$QDRANT_MODE" = "docker" ]; then
        if command -v docker-compose >/dev/null 2>&1; then
            docker-compose -f docker-compose.simple.yml down 2>/dev/null && echo -e "${GREEN}✅ Qdrant Docker stopped${NC}" || true
        elif docker compose version >/dev/null 2>&1; then
            docker compose -f docker-compose.simple.yml down 2>/dev/null && echo -e "${GREEN}✅ Qdrant Docker stopped${NC}" || true
        fi
    else
        echo -e "${GREEN}✅ Qdrant Cloud (no action needed)${NC}"
    fi
fi

# Deactivate virtual environment if active
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate 2>/dev/null || true
fi

echo -e "${GREEN}✅ All services stopped${NC}"

