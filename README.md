# Project Intelligence Graph

> Upload any codebase → auto-build a knowledge graph → explore relationships visually → ask natural language questions

A **GraphRAG-powered developer tool** that converts codebases and project files into navigable knowledge graphs with hybrid retrieval, interactive visualization, and full observability.

---

## 🎯 What It Does

| Feature | Description |
|---------|-------------|
|  **Project Import** | Upload ZIP or paste GitHub URL |
|  **Auto Entity Extraction** | Functions, classes, modules, endpoints, configs |
|  **Knowledge Graph** | Neo4j graph with entities and relationships |
|  **Natural Language Q&A** | Ask anything about your project |
|  **Graph Visualizer** | Interactive React Flow graph explorer |
|  **Observability** | Latency, retrieval types, traces, metrics |

---

## 🖥 Screenshots

### System Dashboard
```
🧠 Project Intelligence Graph
Upload your project → explore relationships → ask questions

System Status
┌─────────────┬──────────────┐
│ API ● Online│ PostgreSQL ● │
│ Neo4j ● Online│ Ollama ●  │
└─────────────┴──────────────┘

Knowledge Graph
┌──────┬───────┬──────────┬──────────┐
│ 1 Doc│ 45 Ch │ 87 Ent   │ 12 Rel   │
└──────┴───────┴──────────┴──────────┘
```

### Chat Interface
```
You: What functions does this project use?

Bot: Based on the source code:
- embedder.py: embed_text(), embed_batch(), cosine_similarity()
- chunker.py: chunk_text(), clean_text(), extract_text()
- query_engine.py: answer_question()
- retriever.py: vector_search(), graph_search(), hybrid_retrieve()

Sources: [VECTOR] embedder.py  [GRAPH] chunker.py
⏱ 3.2s  📦 5 chunks  🕸 2 hops  🔀 hybrid
```

### Observability Dashboard
```
┌──────────┬────────────┬───────────┬──────────────┐
│ 12 Queries│ 4.2s avg  │ 3.8 chunks│ 92% success  │
└──────────┴────────────┴───────────┴──────────────┘

[Latency Line Chart]     [Retrieval Pie Chart]
```

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────┐
│                PROJECT SOURCES                       │
│          ZIP Upload  │  GitHub URL                   │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────┐
│                FILE WALKER                            │
│   Supported: .py .js .ts .jsx .tsx .md .json .yaml   │
│   Skips: node_modules, .git, __pycache__, .env       │
└──────────────────────┬───────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────┐
│             CHUNKER + EMBEDDER                        │
│   chunk_size=300 words, overlap=30 words              │
│   Model: all-mpnet-base-v2 (768 dims)                │
└──────────────────────┬───────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────┐
│          ENTITY EXTRACTOR                             │
│   Code files (.py .js .ts) → Regex extraction         │
│     → functions, classes, modules, endpoints          │
│   Doc files (.md .txt)     → LLM extraction           │
│     → concepts, technologies                          │
└──────────────────────┬───────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────┐
│              NEO4J KNOWLEDGE GRAPH                    │
│   Project → File → Chunk → Entity                    │
│   Entity -[RELATED]-> Entity                         │
│   Chunk  -[MENTIONS]-> Entity                        │
└───────┬──────────────────────┬───────────────────────┘
        ↓                      ↓
┌───────────────┐    ┌─────────────────────┐
│ QUERY ENGINE  │    │  GRAPH VISUALIZER   │
│               │    │  React Flow         │
│ 5 retrieval   │    │  Color coded nodes  │
│ modes:        │    │  Click to explore   │
│ - overview    │    │  Filter by type     │
│ - file_exact  │    └─────────────────────┘
│ - vector      │
│ - graph       │
│ - hybrid      │
└───────┬───────┘
        ↓
┌──────────────────────────────────────────────────────┐
│            GEMMA 2B via OLLAMA                        │
│            Local LLM, zero API cost                   │
└───────┬──────────────────────────────────────────────┘
        ↓
┌──────────────────────────────────────────────────────┐
│          OBSERVABILITY DASHBOARD                      │
│   Latency chart │ Retrieval breakdown │ Traces table  │
│   Success rate  │ Slowest queries     │ Entity hits   │
└──────────────────────────────────────────────────────┘
```

---

## 🔧 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | FastAPI (Python) | REST API server |
| **Graph DB** | Neo4j 5.15 | Knowledge graph storage |
| **Relational DB** | PostgreSQL 15 | Projects, chunks, traces |
| **Embeddings** | all-mpnet-base-v2 | 768-dim semantic vectors |
| **LLM** | Gemma 2B via Ollama | Answer generation (local, free) |
| **Frontend** | React 18 | UI framework |
| **Graph UI** | React Flow | Interactive graph visualization |
| **Charts** | Recharts | Observability charts |
| **Infra** | Docker Compose | Neo4j + PostgreSQL containers |

---

## 🔍 Retrieval Modes

The system uses **5 retrieval strategies** depending on the question:

| Mode | Trigger | How It Works |
|------|---------|-------------|
| `overview` | Broad questions ("what does this project do?") | First chunk from every code file |
| `file_exact` | File mentioned ("what does App.js do?") | All chunks from that specific file |
| `hybrid` | Specific + entities found | Vector similarity + graph traversal |
| `vector_only` | Specific, no entities matched | Cosine similarity search only |
| `graph_only` | Entities found, no similar chunks | Neo4j graph traversal only |

---

## 📊 Observability

Every query is automatically logged with:

| Metric | Description |
|--------|-------------|
| Latency (ms) | Total query processing time |
| Chunks Retrieved | Number of context chunks used |
| Graph Hops | Depth of graph traversal |
| Entities Matched | Entities found in query |
| Retrieval Type | Which retrieval mode was used |
| Success/Failure | Whether LLM generated a valid answer |

Visualized as:
- **Line chart** → latency over time with average reference line
- **Pie chart** → retrieval type breakdown
- **Table** → recent query traces with color-coded badges
- **Cards** → total queries, avg latency, success rate

---

## 📁 Project Structure

```
project-intelligence-graph/
│
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app + startup
│   │   ├── config.py              # Environment settings
│   │   │
│   │   ├── database/
│   │   │   ├── postgres.py        # PostgreSQL operations
│   │   │   └── neo4j.py           # Neo4j client
│   │   │
│   │   ├── routers/
│   │   │   ├── health.py          # GET /health
│   │   │   ├── project.py         # POST /projects/upload-zip
│   │   │   │                      # POST /projects/import-github
│   │   │   │                      # GET  /projects
│   │   │   ├── graph.py           # POST /graph/build-project/{id}
│   │   │   │                      # GET  /graph/visualize/{id}
│   │   │   │                      # GET  /graph/stats
│   │   │   │                      # GET  /graph/entities
│   │   │   ├── query.py           # POST /query
│   │   │   │                      # GET  /traces/{id}
│   │   │   └── metrics.py         # GET  /metrics/{id}
│   │   │
│   │   └── services/
│   │       ├── embedder.py        # Sentence transformer embeddings
│   │       ├── chunker.py         # Text chunking with overlap
│   │       ├── file_walker.py     # ZIP/GitHub file extraction
│   │       ├── ollama.py          # LLM + entity extraction
│   │       ├── retriever.py       # 5-mode hybrid retrieval
│   │       ├── graph_builder.py   # Neo4j graph operations
│   │       └── query_engine.py    # Answer generation pipeline
│   │
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   └── src/
│       ├── App.jsx                # Main app with tabs
│       ├── index.css              # Dark theme styles
│       └── components/
│           ├── StatusCard.jsx     # Service health indicator
│           ├── GraphStats.jsx     # Graph node/edge counts
│           ├── ProjectImport.jsx  # ZIP upload + GitHub import
│           ├── ProjectList.jsx    # Projects table
│           ├── ProjectSelector.jsx # Project switcher
│           ├── GraphVisualizer.jsx # React Flow graph
│           ├── ChatPanel.jsx      # Q&A chat interface
│           ├── ObservabilityDashboard.jsx  # Metrics dashboard
│           ├── MetricCard.jsx     # Single metric display
│           ├── LatencyChart.jsx   # Latency line chart
│           ├── RetrievalChart.jsx # Retrieval type pie chart
│           └── TracesTable.jsx    # Recent queries table
│
├── docker-compose.yml             # Neo4j + PostgreSQL
├── .gitignore
└── README.md
```

---

## 🚀 Setup

### Prerequisites

| Tool | Version |
|------|---------|
| Docker | Latest |
| Python | 3.11+ |
| Node.js | 18+ |
| Ollama | Latest |

### 1. Clone

```bash
git clone https://github.com/vangogh1803/intelliGraph.git
cd project-intelligence-graph
```

### 2. Start Databases

```bash
docker compose up -d
```

Verify:
```bash
docker compose ps
# Both postgres and neo4j should show "running"
```

### 3. Start Ollama + Pull Model

```bash
# Terminal 1
ollama serve

# Terminal 2
ollama pull gemma:2b
```

### 4. Backend Setup

```bash
# Terminal 3
cd backend
conda create -n graphrag python=3.11 -y
conda activate graphrag
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Verify: `http://localhost:8000/health` should return all green.

### 5. Frontend Setup

```bash
# Terminal 4
cd frontend
npm install
npm run dev
```

Open: `http://localhost:5173`

---

## 📖 How To Use

### 1. Import a Project

**ZIP Upload:**
- Click "Upload ZIP" tab
- Select your project ZIP file
- Click "Upload & Process"

**GitHub:**
- Click "GitHub URL" tab
- Paste a public repo URL
- Click "Import"

### 2. Build Knowledge Graph

- Find your project in the table
- Click "Build Graph"
- Wait for entity extraction to complete

### 3. Explore

**💬 Ask Tab:**
```
"What functions does this project use?"
"How does the upload process work?"
"What does App.js do?"
"Which embedding model is used?"
```

**🕸 Graph Tab:**
- Pan and zoom the graph
- Click any node to see details
- Filter by entity type (Function, Class, Module etc)

**📊 Observability Tab:**
- View latency trends
- See retrieval type distribution
- Browse recent query traces

---

## 🔌 API Endpoints

### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | System status check |

### Projects
| Method | Path | Description |
|--------|------|-------------|
| POST | `/projects/upload-zip` | Upload ZIP project |
| POST | `/projects/import-github` | Clone GitHub repo |
| GET | `/projects` | List all projects |
| GET | `/projects/{id}` | Get project details |

### Graph
| Method | Path | Description |
|--------|------|-------------|
| POST | `/graph/build-project/{id}` | Build knowledge graph |
| GET | `/graph/visualize/{id}` | Get graph for React Flow |
| GET | `/graph/stats` | Graph statistics |
| GET | `/graph/entities` | List all entities |

### Query
| Method | Path | Description |
|--------|------|-------------|
| POST | `/query` | Ask a question |
| GET | `/traces/{id}` | Get query traces |

### Metrics
| Method | Path | Description |
|--------|------|-------------|
| GET | `/metrics` | Global metrics |
| GET | `/metrics/{id}` | Project metrics |

---

## 🧠 How GraphRAG Works

### Traditional RAG
```
Question → Embed → Find similar chunks → Send to LLM → Answer
```

### This Project's GraphRAG
```
Question
    ↓
Detect question type (broad vs specific vs file-specific)
    ↓
┌─────────────────────────────────────────┐
│ Parallel retrieval:                      │
│  1. Vector similarity (cosine search)    │
│  2. Entity matching in Neo4j graph       │
│  3. Graph traversal (2-hop neighbors)    │
│  4. File name detection + exact lookup   │
│  5. Project overview (broad questions)   │
└─────────────────────────────────────────┘
    ↓
Merge + deduplicate + rank by priority
    ↓
Build context from best chunks
    ↓
Send to Gemma 2B (local LLM)
    ↓
Return answer + sources + trace metadata
```

### Why GraphRAG > Basic RAG

| Aspect | Basic RAG | This GraphRAG |
|--------|-----------|---------------|
| Retrieval | Vector only | Vector + Graph + File + Overview |
| Context | Random similar chunks | Connected, relationship-aware chunks |
| Broad questions | Poor | Project-wide overview mode |
| File questions | Poor | Exact file lookup |
| Traceability | None | Full source + trace logging |
| Debuggability | None | Observability dashboard |

---

## ⚙ Configuration

### Tunable Parameters

| Parameter | File | Default | Description |
|-----------|------|---------|-------------|
| `chunk_size` | chunker.py | 300 words | Words per chunk |
| `overlap` | chunker.py | 30 words | Overlap between chunks |
| `vector_top_k` | retriever.py | 5 | Top K vector results |
| `graph_hops` | retriever.py | 1 | Neo4j traversal depth |
| `num_ctx` | ollama.py | 4096 | LLM context window |
| `num_predict` | ollama.py | 500 | Max output tokens |
| `temperature` | ollama.py | 0.1 | LLM temperature |
| `context_budget` | query_engine.py | 1800 chars | Max context sent to LLM |

---

## 🛠 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8000 in use | `lsof -ti :8000 \| xargs kill -9` |
| Ollama not found | Run `ollama serve` in separate terminal |
| Neo4j connection failed | Run `docker compose up -d` |
| 0 entities after build | Check terminal for extraction logs |
| LLM timeout | Increase `timeout` in ollama.py |
| Answer cut off | Increase `num_predict` in ollama.py |
| Bad JSON from LLM | Regex fallback handles this automatically |
| numpy conflict | Use `pip install "numpy<2"` |


---

