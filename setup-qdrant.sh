#!/bin/bash

# Chronofact.ai - Qdrant Setup Script
# Supports multiple deployment modes for Qdrant
# Works with Git Bash on Windows

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Docker is running
docker_running() {
    docker info >/dev/null 2>&1
}

# Function to update .env file
update_env_file() {
    local mode=$1
    local env_file="$PROJECT_DIR/.env"
    
    if [ ! -f "$env_file" ]; then
        log_info "Creating .env file..."
        touch "$env_file"
    fi
    
    # Update or add QDRANT_MODE
    if grep -q "^QDRANT_MODE=" "$env_file"; then
        # Update existing line
        if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
            # Git Bash on Windows
            sed -i "s/^QDRANT_MODE=.*/QDRANT_MODE=$mode/" "$env_file"
        else
            # Linux/Mac
            sed -i.bak "s/^QDRANT_MODE=.*/QDRANT_MODE=$mode/" "$env_file"
        fi
    else
        # Add new line
        echo "QDRANT_MODE=$mode" >> "$env_file"
    fi
    
    log_success "Updated .env: QDRANT_MODE=$mode"
}

# Function to setup local Qdrant
setup_local() {
    log_info "Setting up Qdrant in local mode..."
    
    # Create data directory
    mkdir -p "$PROJECT_DIR/data/qdrant"
    
    # Update .env file
    update_env_file "local"
    
    log_success "Local Qdrant setup complete!"
    log_info "Data will be stored at: $PROJECT_DIR/data/qdrant"
    log_info "Run: python -m src.cli init"
}

# Function to setup Docker Qdrant
setup_docker() {
    log_info "Setting up Qdrant with Docker..."
    
    if ! command_exists docker; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker_running; then
        log_error "Docker daemon is not running. Please start Docker Desktop."
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    # Check if docker-compose exists
    if command_exists docker-compose; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        log_error "docker-compose is not installed."
        exit 1
    fi
    
    # Start Qdrant
    log_info "Starting Qdrant container..."
    $DOCKER_COMPOSE_CMD -f docker-compose.simple.yml up -d qdrant
    
    # Wait for Qdrant to be ready
    log_info "Waiting for Qdrant to be ready..."
    local max_attempts=30
    local attempt=0
    local ready=false
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:6333/ >/dev/null 2>&1; then
            ready=true
            break
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    
    if [ "$ready" = false ]; then
        log_error "Qdrant failed to start within 60 seconds"
        log_info "Check logs: docker logs chronofact-qdrant"
        exit 1
    fi
    
    # Update .env file
    update_env_file "docker"
    
    log_success "Docker Qdrant setup complete!"
    log_info "Qdrant is running at http://localhost:6333"
    log_info "To stop: $DOCKER_COMPOSE_CMD -f docker-compose.simple.yml down"
    log_info "Run: python -m src.cli init"
}

# Function to setup Qdrant Cloud
setup_cloud() {
    log_info "Setting up Qdrant Cloud connection..."
    
    # Load .env if exists
    if [ -f "$PROJECT_DIR/.env" ]; then
        set -a
        source "$PROJECT_DIR/.env"
        set +a
    fi
    
    if [ -z "$QDRANT_URL" ]; then
        log_error "QDRANT_URL environment variable is required for cloud mode"
        log_info "Get your cluster URL from https://cloud.qdrant.io"
        log_info "Add to .env: QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333"
        exit 1
    fi
    
    if [ -z "$QDRANT_API_KEY" ]; then
        log_error "QDRANT_API_KEY environment variable is required for cloud mode"
        log_info "Get your API key from https://cloud.qdrant.io"
        log_info "Add to .env: QDRANT_API_KEY=your-api-key"
        exit 1
    fi
    
    # Update .env file
    update_env_file "cloud"
    
    log_success "Qdrant Cloud setup complete!"
    log_info "Using cluster: $QDRANT_URL"
    log_info "Run: python -m src.cli init"
}

# Function to setup memory mode
setup_memory() {
    log_info "Setting up Qdrant in memory mode..."
    update_env_file "memory"
    log_success "Qdrant will run in memory mode (no persistence)"
    log_warning "Data will be lost on restart"
}

# Function to initialize collections
init_collections() {
    log_info "Initializing Qdrant collections..."
    
    cd "$PROJECT_DIR"
    
    # Load .env if exists
    if [ -f "$PROJECT_DIR/.env" ]; then
        set -a
        source "$PROJECT_DIR/.env"
        set +a
    fi
    
    # Activate virtual environment
    activate_venv
    
    # Ensure BAML is generated first
    if [ ! -d "$PROJECT_DIR/baml_client" ]; then
        log_info "BAML client not found. Generating..."
        generate_baml
    fi
    
    # Run init command
    python -m src.cli init
    
    log_success "Collections initialized!"
}

# Function to ingest mock data
ingest_mock() {
    log_info "Ingesting mock data..."
    
    cd "$PROJECT_DIR"
    
    # Load .env if exists
    if [ -f "$PROJECT_DIR/.env" ]; then
        set -a
        source "$PROJECT_DIR/.env"
        set +a
    fi
    
    # Activate virtual environment if exists
    activate_venv
    
    # Run ingest command
    python -m src.cli ingest mock
    
    log_success "Mock data ingested!"
}

# Function to activate virtual environment
activate_venv() {
    if [ -d "$PROJECT_DIR/.venv" ]; then
        if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
            source "$PROJECT_DIR/.venv/Scripts/activate" 2>/dev/null || true
        else
            source "$PROJECT_DIR/.venv/bin/activate" 2>/dev/null || true
        fi
        # Only log if not already activated
        if [ -z "$VIRTUAL_ENV" ]; then
            log_warning "Failed to activate virtual environment"
        fi
    else
        log_warning "Virtual environment not found at .venv"
        log_info "Create it with: uv venv"
        return 1
    fi
}

# Function to generate BAML client
generate_baml() {
    log_info "Generating BAML client..."
    
    cd "$PROJECT_DIR"
    
    # Activate virtual environment
    activate_venv
    
    # Check if uv is available
    if ! command_exists uv; then
        log_error "uv is not installed. Install from https://docs.astral.sh/uv/"
        exit 1
    fi
    
    # Check if baml-cli is available
    if ! uv run baml-cli --version >/dev/null 2>&1; then
        log_warning "baml-cli not found. Installing baml-py..."
        uv pip install baml-py
    fi
    
    # Generate BAML client
    log_info "Running: uv run baml-cli generate"
    if uv run baml-cli generate; then
        log_success "BAML client generated successfully!"
    else
        log_error "BAML client generation failed"
        log_info "Check baml_src/ for syntax errors"
        exit 1
    fi
}

# Function to test Qdrant connection
test_connection() {
    log_info "Testing Qdrant connection..."
    
    # Load .env if exists
    if [ -f "$PROJECT_DIR/.env" ]; then
        set -a
        source "$PROJECT_DIR/.env"
        set +a
    fi
    
    # Determine mode and test accordingly
    MODE="${QDRANT_MODE:-local}"
    
    cd "$PROJECT_DIR"
    
    # Activate virtual environment
    activate_venv
    
    case $MODE in
        memory|local|docker|cloud)
            log_info "Testing Qdrant connection in $MODE mode..."
            python -c "
import sys
sys.path.insert(0, 'src')
from src.qdrant_setup import create_qdrant_client
from src.config import get_config
try:
    client = create_qdrant_client(get_config())
    collections = client.get_collections()
    print(f'✅ Qdrant connected successfully!')
    print(f'   Mode: $MODE')
    print(f'   Collections: {len(collections.collections)}')
    for col in collections.collections:
        info = client.get_collection(col.name)
        print(f'   - {col.name}: {info.points_count} points')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    sys.exit(1)
"
            ;;
        *)
            log_error "Unknown Qdrant mode: $MODE"
            exit 1
            ;;
    esac
}

# Function to show usage
show_usage() {
    cat << EOF
Chronofact.ai - Qdrant Setup Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    local       Setup Qdrant in local persistent mode
    docker      Setup Qdrant with Docker container
    cloud       Setup Qdrant Cloud connection
    memory      Setup Qdrant in-memory mode (no persistence)
    init        Initialize Qdrant collections
    ingest      Ingest mock data into Qdrant
    baml        Generate BAML client
    test        Test current Qdrant connection
    help        Show this help message

Environment Variables (in .env):
    QDRANT_MODE         Deployment mode (memory/local/docker/cloud)
    QDRANT_STORAGE_PATH Local storage path (for local mode)
    QDRANT_URL          Cloud cluster URL (for cloud mode)
    QDRANT_API_KEY      API key for authentication
    QDRANT_HOST         Host for remote connections
    QDRANT_PORT         Port for remote connections

Examples:
    # Setup local persistent Qdrant
    $0 local
    $0 init
    $0 ingest

    # Setup Docker Qdrant
    $0 docker
    $0 init
    $0 ingest

    # Setup Qdrant Cloud
    # Add to .env: QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333
    # Add to .env: QDRANT_API_KEY=your-api-key
    $0 cloud
    $0 init

    # Test connection
    $0 test

For more information, see docs/qdrant-deployment.md
EOF
}

# Main script logic
case "${1:-help}" in
    local)
        setup_local
        ;;
    docker)
        setup_docker
        ;;
    cloud)
        setup_cloud
        ;;
    memory)
        setup_memory
        ;;
    init)
        init_collections
        ;;
    ingest)
        ingest_mock
        ;;
    baml)
        generate_baml
        ;;
    test)
        test_connection
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        log_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
