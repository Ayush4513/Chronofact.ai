#!/bin/bash

# Chronofact.ai - Qdrant Setup Script
# Supports multiple deployment modes for Qdrant

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

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

# Function to setup local Qdrant
setup_local() {
    log_info "Setting up Qdrant in local mode..."

    # Create data directory
    mkdir -p "$PROJECT_DIR/data/qdrant"

    # Set environment variables
    export QDRANT_MODE=local
    export QDRANT_STORAGE_PATH="$PROJECT_DIR/data/qdrant"

    log_success "Local Qdrant setup complete!"
    log_info "Data will be stored at: $PROJECT_DIR/data/qdrant"
}

# Function to setup Docker Qdrant
setup_docker() {
    log_info "Setting up Qdrant with Docker..."

    if ! command_exists docker; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! docker_running; then
        log_error "Docker daemon is not running. Please start Docker."
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
    $DOCKER_COMPOSE_CMD up -d qdrant

    # Wait for Qdrant to be ready
    log_info "Waiting for Qdrant to be ready..."
    for i in {1..30}; do
        if curl -f http://localhost:6333/health >/dev/null 2>&1; then
            break
        fi
        sleep 2
        if [ $i -eq 30 ]; then
            log_error "Qdrant failed to start within 60 seconds"
            exit 1
        fi
    done

    log_success "Docker Qdrant setup complete!"
    log_info "Qdrant is running at http://localhost:6333"
    log_info "To stop: $DOCKER_COMPOSE_CMD down"
}

# Function to setup Qdrant Cloud
setup_cloud() {
    log_info "Setting up Qdrant Cloud connection..."

    if [ -z "$QDRANT_URL" ]; then
        log_error "QDRANT_URL environment variable is required for cloud mode"
        log_info "Get your cluster URL from https://cloud.qdrant.io"
        exit 1
    fi

    if [ -z "$QDRANT_API_KEY" ]; then
        log_error "QDRANT_API_KEY environment variable is required for cloud mode"
        log_info "Get your API key from https://cloud.qdrant.io"
        exit 1
    fi

    log_success "Qdrant Cloud setup complete!"
    log_info "Using cluster: $QDRANT_URL"
}

# Function to test Qdrant connection
test_connection() {
    log_info "Testing Qdrant connection..."

    # Set environment variables from .env if it exists
    if [ -f "$PROJECT_DIR/.env" ]; then
        set -a
        source "$PROJECT_DIR/.env"
        set +a
    fi

    # Determine mode and test accordingly
    MODE="${QDRANT_MODE:-local}"

    case $MODE in
        memory)
            log_info "Testing in-memory Qdrant..."
            cd "$PROJECT_DIR"
            PYTHONPATH="$PROJECT_DIR/src" python3 -c "
from qdrant_setup import create_qdrant_client
try:
    client = create_qdrant_client()
    collections = client.get_collections()
    print('✅ In-memory Qdrant connection successful')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    import sys
    sys.exit(1)
"
            ;;
        local)
            log_info "Testing local Qdrant..."
            cd "$PROJECT_DIR"
            PYTHONPATH="$PROJECT_DIR/src" python3 -c "
from qdrant_setup import create_qdrant_client
try:
    client = create_qdrant_client()
    collections = client.get_collections()
    print('✅ Local Qdrant connection successful')
    print(f'Found {len(collections.collections)} collections')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    import sys
    sys.exit(1)
"
            ;;
        cloud)
            log_info "Testing Qdrant Cloud..."
            cd "$PROJECT_DIR"
            PYTHONPATH="$PROJECT_DIR/src" python3 -c "
from qdrant_setup import create_qdrant_client
try:
    client = create_qdrant_client()
    collections = client.get_collections()
    print('✅ Qdrant Cloud connection successful')
    print(f'Found {len(collections.collections)} collections')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    import sys
    sys.exit(1)
"
            ;;
        local)
            log_info "Testing local Qdrant..."
            python3 -c "
import sys
sys.path.insert(0, '$PROJECT_DIR/src')
from qdrant_setup import create_qdrant_client
try:
    client = create_qdrant_client()
    collections = client.get_collections()
    print('✅ Local Qdrant connection successful')
    print(f'Found {len(collections.collections)} collections')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    sys.exit(1)
"
            ;;
        docker)
            log_info "Testing Docker Qdrant..."
            if curl -f http://localhost:6333/health >/dev/null 2>&1; then
                echo "✅ Docker Qdrant health check passed"
                # Test with Python client
    cd "$PROJECT_DIR"
    python3 -c "
import sys
sys.path.insert(0, 'src')
from qdrant_setup import create_qdrant_client
try:
    client = create_qdrant_client()
    collections = client.get_collections()
    print(f'✅ Docker Qdrant connected. Found {len(collections.collections)} collections')
except Exception as e:
    print(f'❌ Python client connection failed: {e}')
    sys.exit(1)
"
            else
                echo "❌ Docker Qdrant health check failed"
                exit 1
            fi
            ;;
        cloud)
            log_info "Testing Qdrant Cloud..."
            python3 -c "
import sys
sys.path.insert(0, '$PROJECT_DIR/src')
from qdrant_setup import create_qdrant_client
try:
    client = create_qdrant_client()
    collections = client.get_collections()
    print('✅ Qdrant Cloud connection successful')
    print(f'Found {len(collections.collections)} collections')
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
    test        Test current Qdrant connection
    help        Show this help message

Environment Variables:
    QDRANT_MODE         Deployment mode (memory/local/docker/cloud)
    QDRANT_STORAGE_PATH Local storage path (for local mode)
    QDRANT_URL          Cloud cluster URL (for cloud mode)
    QDRANT_API_KEY      API key for authentication
    QDRANT_HOST         Host for remote connections
    QDRANT_PORT         Port for remote connections

Examples:
    # Setup local persistent Qdrant
    $0 local

    # Setup Docker Qdrant
    $0 docker

    # Setup Qdrant Cloud
    export QDRANT_URL="https://your-cluster.aws.cloud.qdrant.io:6333"
    export QDRANT_API_KEY="your-api-key"
    $0 cloud

    # Test connection
    $0 test

For more information, see docs/qdrant-setup.md
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
        export QDRANT_MODE=memory
        log_success "Qdrant will run in memory mode (no persistence)"
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