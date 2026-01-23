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

# Generate BAML client
RUN baml-cli generate

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["python", "-m", "src.api"]
