# Chronofact.ai

AI-powered fact-based timeline generator that builds accurate, verifiable event timelines using **Qdrant** vector search and **BAML** structured AI.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CHRONOFACT.AI                                      │
│         Discover Truth Through Time - AI Timeline Generator                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  Qdrant Vector DB  │  BAML Structured AI  │  Gemini AI  │  CLIP Multimodal  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**🚀 Live Demo:** https://chronofact-ai.onrender.com

> Built for Qdrant Convolve 4.0

---

## 🎯 Two Ways to Run

### Option 1: Quick Local Setup (3 Steps)

```bash
# 1. Clone the repository
git clone https://github.com/Ayush4513/Chronofact.ai.git
cd Chronofact.ai

# 2. Setup environment variables
cp env.template .env
# Edit .env with your API keys:
#   - GOOGLE_API_KEY (get from https://makersuite.google.com/app/apikey)
#   - QDRANT_URL and QDRANT_API_KEY (get from https://cloud.qdrant.io)

# 3. Run everything with one command
./start.sh
```

**✅ Done!** Access your app:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

The `start.sh` script automatically:
- ✅ Installs all dependencies (Python, Node.js packages)
- ✅ Generates BAML client
- ✅ Initializes Qdrant collections
- ✅ Ingests sample data
- ✅ Starts both frontend and backend

### Option 2: Deploy to Render (Production)

1. **Fork this repository** on GitHub
2. **Connect to Render**:
   - Go to https://render.com
   - Click "New" → "Blueprint"
   - Connect your forked repository
3. **Set Environment Variables** in Render Dashboard:
   - `GOOGLE_API_KEY`
   - `QDRANT_URL`
   - `QDRANT_API_KEY`
4. **Deploy!** Render auto-builds and deploys from `render.yaml`

**🌐 Your app will be live at**: `https://your-app-name.onrender.com`

---

## Prerequisites

| Tool | Installation |
|------|--------------|
| Python 3.11+ | https://python.org |
| Git Bash | https://git-scm.com (Windows) |
| Bun | https://bun.sh |
| Google AI API Key | https://makersuite.google.com/app/apikey |
| Qdrant Cloud | https://cloud.qdrant.io (free tier available) |

**Note**: `uv` package manager is auto-installed by `start.sh` if missing.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    React + TypeScript + Tailwind                     │   │
│  │  • Search Input (text + image)                                       │   │
│  │  • Timeline Visualization                                            │   │
│  │  • Credibility Meters                                                │   │
│  │  • Follow-up Questions                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ HTTP/REST
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI BACKEND                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   /timeline  │  │   /verify    │  │   /detect    │  │  /followup   │    │
│  │   Generate   │  │   Claims     │  │   Misinfo    │  │   Questions  │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │             │
│         └─────────────────┴─────────────────┴─────────────────┘             │
│                                     │                                        │
│                        ┌────────────┴────────────┐                          │
│                        ▼                         ▼                          │
│              ┌──────────────────┐      ┌──────────────────┐                 │
│              │  BAML Functions  │      │  Hybrid Search   │                 │
│              │  (Gemini AI)     │      │  (Vector + BM25) │                 │
│              └────────┬─────────┘      └────────┬─────────┘                 │
│                       │                         │                           │
└───────────────────────┼─────────────────────────┼───────────────────────────┘
                        │                         │
         ┌──────────────┴──────────────┐          │
         ▼                             ▼          ▼
┌─────────────────┐           ┌─────────────────────────┐
│   GEMINI AI     │           │      QDRANT CLOUD       │
│   (via BAML)    │           │   ┌─────────────────┐   │
│                 │           │   │   x_posts       │   │
│ • ProcessQuery  │           │   │   (text, image, │   │
│ • Timeline Gen  │           │   │    multimodal)  │   │
│ • Credibility   │           │   ├─────────────────┤   │
│ • Misinformation│           │   │ knowledge_facts │   │
│ • FollowUp Q's  │           │   ├─────────────────┤   │
│                 │           │   │ session_memory  │   │
└─────────────────┘           │   └─────────────────┘   │
                              └─────────────────────────┘
```

---

## Data Flow

### Timeline Generation Flow

```
┌──────────────┐     ┌───────────────┐     ┌────────────────┐
│  User Query  │────▶│ ProcessQuery  │────▶│ Hybrid Search  │
│  + Image     │     │    (BAML)     │     │   (Qdrant)     │
└──────────────┘     └───────────────┘     └───────┬────────┘
                                                   │
                     ┌─────────────────────────────┘
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    CONTEXT RETRIEVAL                        │
│  • Vector similarity search (text embeddings)               │
│  • BM25 keyword matching                                    │
│  • Image similarity (CLIP embeddings if image provided)     │
│  • Metadata filtering (location, credibility, time)         │
└────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                  TIMELINE GENERATION                        │
│  GenerateTimeline(BAML) + Gemini AI                        │
│  • Chronological ordering                                   │
│  • Source citation                                          │
│  • Credibility scoring                                      │
│  • Prediction generation                                    │
└────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                   POST-PROCESSING                           │
│  • DetectMisinformation → Risk assessment                   │
│  • GenerateFollowUpQuestions → Continue exploration         │
│  • GenerateRecommendations → Related queries                │
└────────────────────────────────────────────────────────────┘
                     │
                     ▼
              ┌──────────────┐
              │   Response   │
              │  • Timeline  │
              │  • Events    │
              │  • Questions │
              └──────────────┘
```

### Multimodal Query Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│    Text     │     │   Image     │     │   Gemini AI     │
│   Query     │     │   Upload    │────▶│  Image Analysis │
└──────┬──────┘     └──────┬──────┘     └────────┬────────┘
       │                   │                     │
       │                   │            "Visual context:
       │                   │             flood waters,
       │                   │             damaged roads..."
       │                   │                     │
       ▼                   ▼                     ▼
┌─────────────────────────────────────────────────────────┐
│              ENHANCED QUERY                              │
│  "Mumbai floods" + "Visual context: flood waters,        │
│   damaged infrastructure, rescue operations visible"     │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   Better Results       │
              │   Context-aware search │
              └────────────────────────┘
```

---

## Features

| Feature | Description |
|---------|-------------|
| Timeline Generation | Chronological event timelines with sources |
| Credibility Scoring | AI-powered trustworthiness (0-100%) |
| Misinformation Detection | Risk assessment (Low/Medium/High) |
| Image Context | Upload images for visual context |
| Follow-up Questions | AI suggests next investigation steps |
| Hybrid Search | Vector + keyword matching |
| Legal Data Pipeline | Academic datasets + synthetic generation |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health check |
| POST | `/api/timeline` | Generate timeline (supports image) |
| POST | `/api/verify` | Verify claim credibility |
| POST | `/api/detect` | Detect misinformation |
| POST | `/api/followup` | Get follow-up questions |
| POST | `/api/recommend` | Get recommendations |
| POST | `/api/search` | Search vector DB |

### Example: Generate Timeline

```bash
curl -X POST http://localhost:8000/api/timeline \
  -H "Content-Type: application/json" \
  -d '{"topic": "Mumbai floods 2024", "limit": 10}'
```

---

## Project Structure

```
Chronofact.ai/
├── src/                          # Python backend
│   ├── api.py                    # FastAPI endpoints
│   ├── timeline_builder.py       # Timeline logic
│   ├── search.py                 # Hybrid search
│   ├── multimodal.py             # CLIP embeddings
│   ├── qdrant_setup.py           # Vector DB setup
│   └── data/                     # Legal data pipeline
│       ├── academic_datasets.py
│       ├── synthetic_generator.py
│       └── event_focus.py
├── frontend/                     # React frontend
│   ├── src/App.tsx               # Main UI
│   └── src/lib/api.ts            # API client
├── baml_src/                     # BAML AI functions
│   ├── main.baml                 # Core functions
│   └── clients.baml              # AI client config
├── config/                       # Configuration
├── start.sh                      # Start script
└── stop.sh                       # Stop script
```

---

## Manual Setup (If start.sh Fails)

### Windows PowerShell

```powershell
# 1. Navigate to project
cd Chronofact.ai

# 2. Install Python dependencies
pip install uv
uv sync

# 3. Generate BAML client
uv run baml-cli generate

# 4. Build frontend
cd frontend
npm install -g bun   # If bun not installed
bun install
bun run build
cd ..

# 5. Set environment variables
$env:GOOGLE_API_KEY = "your-key"
$env:QDRANT_MODE = "cloud"
$env:QDRANT_URL = "your-qdrant-url"
$env:QDRANT_API_KEY = "your-qdrant-key"

# 6. Start backend (Terminal 1)
uv run python -m src.api

# 7. Start frontend (Terminal 2)
cd frontend
bun server.ts
```

### Linux/Mac

```bash
# If ./start.sh has permission issues:
chmod +x start.sh
./start.sh

# Or run manually:
uv sync
uv run baml-cli generate
cd frontend && bun install && bun run build && cd ..
uv run python -m src.api &
cd frontend && bun server.ts
```

---

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| `./start.sh: Permission denied` | Run `chmod +x start.sh` |
| `uv: command not found` | Install: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `bun: command not found` | Install: `curl -fsSL https://bun.sh/install \| bash` |
| Port 3000/8000 in use | Kill process: `lsof -ti:3000 \| xargs kill -9` (Mac/Linux) or `netstat -ano \| findstr :3000` (Windows) |
| BAML client not available | `uv sync && uv run baml-cli generate` |
| BAML version mismatch | `uv add baml-py==0.218.0 && uv run baml-cli generate` |
| Blank frontend | Rebuild: `cd frontend && bun run build` |
| API connection failed | Check `.env` has correct API keys |
| Config attribute error | Verify `config.qdrant.mode` not `config.QDRANT_MODE` |

### View Backend Logs

```bash
# Real-time logs
tail -f logs/backend.log

# Last 50 lines
tail -50 logs/backend.log
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google AI API key | Yes |
| `QDRANT_MODE` | `cloud` or `docker` | Yes |
| `QDRANT_URL` | Qdrant Cloud URL | If cloud |
| `QDRANT_API_KEY` | Qdrant API key | If cloud |

---

## Tech Stack

```
┌─────────────────────────────────────────────────────────┐
│                       FRONTEND                           │
│  React 19 • TypeScript • Tailwind CSS • Framer Motion   │
├─────────────────────────────────────────────────────────┤
│                       BACKEND                            │
│  Python • FastAPI • BAML • Sentence Transformers        │
├─────────────────────────────────────────────────────────┤
│                       AI/ML                              │
│  Google Gemini • CLIP (OpenAI) • Hybrid Search          │
├─────────────────────────────────────────────────────────┤
│                       DATABASE                           │
│  Qdrant Cloud (Vector Search + BM25)                    │
├─────────────────────────────────────────────────────────┤
│                       RUNTIME                            │
│  Bun (frontend) • uv (Python) • Git Bash (scripts)      │
└─────────────────────────────────────────────────────────┘
```

---

## License

MIT License

---

**Author**: Ayush4513

Built for Qdrant Convolve 4.0
