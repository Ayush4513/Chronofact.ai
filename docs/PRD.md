# Final Combined Product Requirements Document (PRD) and Technical Specification (SPEC) for Chronofact.ai

**Product Name**: Chronofact.ai  
**Version**: 1.2 (Final Hackathon Prototype – Incorporating BAML for Structured Output Verification)  
**Author**: Ayush4513  
**Date**: January 21, 2026  
**Purpose**: This document combines the complete Product Requirements Document (PRD) and Technical Specification (SPEC) for Chronofact.ai, an AI-powered fact-based news service that ethically ingests data from X (formerly Twitter), constructs accurate and verifiable event timelines for any topic, and maintains long-term, evolving memory using Qdrant. It directly addresses the Convolve 4.0 hackathon's focus on search, memory, and recommendations for societal impact—specifically tackling misinformation and digital trust. The system ensures reliable, traceable outputs with BAML for structured verification, making it robust, ethical, and competition-ready.

## 1. Product Requirements Document (PRD)

### 1.1 Problem Statement
In the fast-paced, fragmented world of social media, users face distorted narratives from misinformation, especially on critical topics like elections, disasters, or public health (e.g., Mumbai floods or Maharashtra politics in 2026). Traditional news aggregators often lack traceability, hallucinate facts, or produce inconsistent structures. This system solves this by:
- Ethically ingesting real-time X data.
- Building chronological, verifiable timelines.
- Maintaining persistent, evolving memory.
- Verifying structured outputs with BAML to eliminate malformed or ungrounded responses.

This aligns with the hackathon's emphasis on multimodal retrieval, long-term memory, evidence-based outputs, and societal relevance.

### 1.2 Objectives
- **Primary Goal**: Deliver accurate, evidence-based event timelines from X data with 100% schema compliance and high traceability.
- **Key Metrics for Success**:
  - Accuracy: 90%+ fact-verification rate via cross-referenced sources.
  - Output Reliability: 100% schema compliance via BAML (no malformed timelines).
  - Latency: <5 seconds for timeline generation.
  - User Satisfaction: Fully traceable reasoning and verifiable structures.
  - Societal Impact: Focus on Mumbai/India-relevant topics with bias mitigation.
- **Hackathon Value**: Strong contender for digital trust/civic tech prizes; realistic prototype for deployment.

### 1.3 Target Users & Personas
- **Primary Users**: Journalists, researchers, students, and Mumbai residents tracking local events.
- **Personas**:
  - Ayush (Mumbai Resident): Queries local topics like "2026 Maharashtra assembly elections" for informed decisions.
  - Journalist: Needs quick, verifiable timelines for articles.
  - Student: Uses for educational research on historical/current events.
- **User Needs**: Fast, personalized (e.g., geo-filtered), ethical, and reliably structured timelines.

### 1.4 Features and Requirements
#### Core Features
1. **X Data Ingestion**:
   - Ethical fetching via X semantic/keyword search tools.
   - Multimodal support: Text, images, videos, links.
   - Filters: Credibility (min_faves, verified), time, location.

2. **Timeline Generation**:
   - Query-based chronological events with summaries, sources, media.
   - "What-if" predictions from patterns.

3. **Long-Term Memory**:
   - Qdrant storage with updates, decay, reinforcement.
   - Session personalization (e.g., Mumbai focus).

4. **Recommendations and Outputs**:
   - Context-aware suggestions.
   - BAML-verified structured outputs (e.g., Event arrays).
   - Grounded in retrieved data; traceable reasoning.

#### User Stories (TDD-Aligned)
- As a user, I want verified structured timelines → BAML ensures schema compliance.
- As a journalist, I want fact-verification → Cross-checks and BAML exceptions.
- As a returning user, I want memory persistence → Qdrant evolves knowledge.
- As a Mumbai resident, I want geo-filtered results → Location-based queries.
- As an ethical user, I want responsible handling → Diverse sources, explainability.

#### Non-Functional Requirements
- Performance: Scalable via Qdrant.
- Security/Privacy: Anonymized queries; no persistent user data.
- Usability: CLI/API interface.
- Reliability: BAML handles malformed LLM outputs; error fallbacks.
- Ethics: Bias detection, source diversity, full explainability.

### 1.5 Assumptions, Risks, and Dependencies
- Assumptions: X API access, BAML compatibility.
- Risks: Rate limits (mitigate with caching), source biases (mitigate with weighting).
- Dependencies: Qdrant Cloud, Hugging Face embeddings, BAML, LLM (e.g., OpenAI/Llama).

### 1.6 Roadmap (Hackathon Timeline)
- MVP (Day 1): Ingestion + basic search.
- Iteration 1 (Day 2): Memory + timeline generation.
- Final (Polish): BAML integration, docs, demos.

## 2. Technical Specification (SPEC)

### 2.1 System Overview
- **Architecture**:
  ```
  User Query --> LLM Agent (BAML-wrapped) --> X Tools (Semantic/Keyword Search)
                           |
                           v
  Fetched Data --> Embeddings (CLIP/Whisper/Sentence Transformers) --> Qdrant
                           |
                           v
  Hybrid Retrieval --> BAML Schema Verification --> Timeline Builder (LLM)
                           |
                           v
  Verified Output (JSON/Timeline) --> User (CLI/API)
  ```
- **Deployment**: Local Python app; Qdrant Cloud; no heavy infra.

### 2.2 Technical Stack
- **Languages/Frameworks**: Python 3.10+, qdrant-client, sentence-transformers, langchain/llama-index, **BAML** (pip install baml).
- **Embeddings**: Multimodal (text, images, audio/video).
- **Database**: Qdrant (collections for events, metadata: timestamp, source_id, credibility_score).
- **Integrations**: X tools, fact-check APIs, LLM.
- **Dev Tools**: pytest (TDD), Git.

### 2.3 Data Flow and Components
#### Ingestion
- Use X tools for real-time/batch fetches.
- Embed and upsert to Qdrant with metadata.

#### Retrieval and Memory
- Hybrid search (dense + sparse + filters).
- Memory: Evolving vectors (updates, decay <0.5 relevance, reinforcement via feedback).
- Collections: Knowledge (verified facts) vs. History (sessions).

#### Timeline Generation (BAML-Integrated)
- After retrieval, use BAML function:
  ```baml
  class Event {
    timestamp: string
    summary: string
    sources: string[]
    media: optional<string>
  }

  function BuildTimeline(input: string) -> Event[] {
    client "openai-gpt-4o"
    prompt #"
      Extract chronological timeline from: {{ input }}
      Output as array of events.
    "#
  }
  ```
- In code: `timeline = await b.BuildTimeline(retrieved_data)`
- Verification: Automatic parsing; exceptions on mismatches (retry or log).

#### Recommendations
- BAML schemas for suggestions (e.g., Recommendation { action: string, reason: string }).

### 2.4 APIs and Interfaces
- /query?topic=... → Verified timeline JSON.
- CLI: python app.py --query "topic".

### 2.5 Security, Privacy, and Ethics
- Anonymized queries; metadata filters.
- BAML validation reduces hallucinations; log mismatches.
- Bias: Source diversity weighting; explainability in outputs.

### 2.6 Testing and Validation (TDD Focus)
- Tests first: BAML parsing (edge cases), Qdrant CRUD, E2E flow.
- Edge Cases: Malformed LLM outputs, empty results, outdated data.

This final combined document provides everything needed for implementation, submission, and judging in Convolve 4.0. It emphasizes Qdrant's core role, BAML for reliability, and societal impact.
