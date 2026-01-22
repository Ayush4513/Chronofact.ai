# Qdrant Deployment Guide

## Overview

Chronofact.ai supports multiple Qdrant deployment modes.

## Modes

### Local Mode (Development)

```bash
./setup-qdrant.sh local
```

Data stored at: `./data/qdrant`

### Docker Mode

```bash
# Start Qdrant container
docker-compose up -d qdrant

# Test connection
./setup-qdrant.sh docker
```

### Memory Mode (Testing)

```bash
./setup-qdrant.sh memory
```

Data lost on restart.

### Cloud Mode (Production)

```bash
export QDRANT_URL="https://your-cluster.cloud.qdrant.io:6333"
export QDRANT_API_KEY="your-api-key"
./setup-qdrant.sh cloud
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `QDRANT_MODE` | Deployment mode |
| `QDRANT_STORAGE_PATH` | Local storage path |
| `QDRANT_URL` | Cloud cluster URL |
| `QDRANT_API_KEY` | Cloud API key |
| `QDRANT_HOST` | Remote host |
| `QDRANT_PORT` | Remote port |

## Health Check

```bash
./setup-qdrant.sh test
```
