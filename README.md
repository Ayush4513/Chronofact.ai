# Chronofact.ai

AI-powered fact-based news service that builds accurate, verifiable event timelines from X (Twitter) data using **Qdrant** as the core vector search engine and **BAML** for structured LLM output.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [Bun](https://bun.sh/) (for frontend)
- Google AI API key
- Qdrant Cloud API key (provided)

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Ayush4513/Chronofact.ai.git
cd Chronofact.ai

# 2. Create .env file and add your API keys
cat > .env << EOF
GOOGLE_API_KEY=your-google-api-key-here
QDRANT_MODE=cloud
QDRANT_URL=https://cb88f687-08a5-4d37-83c6-87c4b9050f72.europe-west3-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key-here
EOF

# 3. Start everything (auto-setup on first run)
./start.sh
```

That's it! The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **Qdrant Cloud**: https://cb88f687-08a5-4d37-83c6-87c4b9050f72.europe-west3-0.gcp.cloud.qdrant.io

## Stop the Application

Press `Ctrl+C` in the terminal, or run:
```bash
./stop.sh
```

## What `start.sh` Does

On first run, it automatically:
- ✅ Creates virtual environment
- ✅ Installs all dependencies
- ✅ Generates BAML client
- ✅ Connects to Qdrant Cloud
- ✅ Initializes Qdrant collections
- ✅ Ingests mock data
- ✅ Starts backend and frontend

On subsequent runs, it just starts the services.

## Features

- **Timeline Generation** - Build chronological event timelines from X posts
- **Credibility Assessment** - Evaluate trustworthiness of claims and sources
- **Misinformation Detection** - Identify potential misinformation patterns
- **Hybrid Search** - Combine vector similarity with keyword matching
- **Multimodal Embeddings** - CLIP-based image-text cross-modal search
- **Memory Evolution** - Temporal decay, reinforcement, and memory consolidation
- **Bias Mitigation** - Source diversity enforcement and bias detection

## Project Structure

```
Chronofact.ai/
├── start.sh              # Start everything (run this)
├── stop.sh               # Stop everything
├── src/                  # Python backend
├── frontend/             # React frontend
├── baml_src/             # BAML definitions
└── docker-compose.simple.yml  # Qdrant Docker config
```

## Troubleshooting

**Port already in use:**
```bash
# Find and kill process using port
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
lsof -ti:6333 | xargs kill -9  # Qdrant
```

**Qdrant Cloud connection issues:**
```bash
# Verify your .env has correct QDRANT_URL and QDRANT_API_KEY
# Check: https://cloud.qdrant.io
```

**BAML errors:**
```bash
# Regenerate BAML client
uv run baml-cli generate
```

---

**Author**: Ayush4513 (sharmayush045@gmail.com)
