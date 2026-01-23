# Chronofact.ai Backend Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml uv.lock ./
COPY baml_src/ ./baml_src/
COPY src/ ./src/
COPY data/ ./data/
COPY config/ ./config/

# Install dependencies
RUN /root/.local/bin/uv sync

# Generate BAML client
RUN /root/.local/bin/uv run baml-cli generate

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["/root/.local/bin/uv", "run", "python", "-m", "src.api"]
