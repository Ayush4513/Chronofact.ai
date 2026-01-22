# Docker Qdrant Setup

## Quick Start

```bash
# Start Qdrant container
docker-compose up -d qdrant

# Verify it's running
curl http://localhost:6333/health
```

## Configuration

```yaml
# docker-compose.simple.yml
services:
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
```

## Stopping

```bash
docker-compose down
```

## Production

For production, see the full [Qdrant documentation](https://qdrant.tech/documentation/guides/).
