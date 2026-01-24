# Chronofact.ai Backend Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY pyproject.toml ./

# Install Python dependencies using pip
RUN pip install --upgrade pip && \
    pip install baml-py fastapi uvicorn[standard] \
    qdrant-client sentence-transformers \
    typer pandas numpy python-dotenv \
    openai pydantic httpx Pillow requests \
    google-generativeai datasets PyYAML \
    selenium webdriver-manager

# Copy project files
COPY baml_src/ ./baml_src/
COPY src/ ./src/
COPY data/ ./data/
COPY config/ ./config/
COPY start_production.py ./

# Generate BAML client
RUN baml-cli generate

# Expose port (Render uses PORT env variable, defaults to 10000)
EXPOSE 10000

# Health check - use PORT env variable
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-10000}/health || exit 1

# Start the application using production script
CMD ["python", "start_production.py"]
