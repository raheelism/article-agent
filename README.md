# Article Agent

<p align="center">
  <strong>🤖 AI-Powered Article Generation System</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/AI%20Detection-0%25-brightgreen?style=for-the-badge" alt="0% AI Detection" />
  <img src="https://img.shields.io/badge/Human--Like%20Output-100%25-blue?style=for-the-badge" alt="100% Human-Like" />
</p>

A sophisticated "Deep Agent" system for generating high-quality, SEO-optimized articles using **LangGraph**, **FastAPI**, and **Groq** (Llama 4 / GPT OSS / Qwen / Kimi). The system employs a multi-agent architecture with autonomous research, structured writing, and parallel evaluation capabilities.

> **🎯 Key Achievement:** Generated articles pass AI detection tools with **0% AI-detected content**, thanks to the advanced Humanization Loop with reflexion-based rewriting and anti-AI writing constraints.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [How It Works](#-how-it-works)
- [State Management](#-state-management)
- [Testing](#-testing)
- [Development Plan](#-development-plan)
- [Contributing](#-contributing)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Deep Research** | Autonomous agent that searches the web via DuckDuckGo, intelligently selects relevant sources, scrapes content using Trafilatura, and summarizes findings |
| 🧠 **RAG-Powered Writing** | Uses SentenceTransformers + FAISS to retrieve only relevant research chunks (~600-1000 tokens) per section, avoiding rate limits and improving context quality |
| 🎯 **Multi-Agent Evaluation** | Parallel critique system using 3 specialized AI models to evaluate drafts on SEO, Engagement, and Logic before final optimization |
| 🤖➡️👤 **Humanization Loop** | Reflexion-based loop achieving **0% AI detection** - detects "AI artifacts" (hedging, nominalizations, sensory vacuum) and rewrites until text is indistinguishable from human writing |
| ❓ **FAQ Generation** | Automatically generates 5-7 FAQ items from research data and article content, formatted for rich snippets |
| 📊 **Keyword Analysis** | Extracts primary, secondary, and LSI keywords with density analysis and SEO recommendations |
| 🔗 **Structured Linking** | Generates 3-5 internal link suggestions and 2-4 authoritative external source citations with placement context |
| 📁 **Virtual Filesystem (VFS)** | In-memory file system that decouples working memory from research data, enabling infinite research depth without context window overflow |
| 📝 **Structured Planning** | AI Planner agent that breaks down topics into executable research and writing tasks with logical flow |
| ✍️ **Anti-AI Writing Constraints** | Writer uses detailed before/after examples to enforce human voice - bans 20+ robotic words and enforces sentence burstiness |
| 💾 **Persistence** | Jobs persisted to SQLite with async checkpointing, enabling resume capability for long-running tasks |
| 🌐 **Service Layer** | Production-ready FastAPI backend for managing content generation jobs via REST API |
| 🔄 **Conditional Routing** | LangGraph-powered state machine with intelligent task routing between research, writing, evaluation, and humanization phases |

---

## 🏗 Architecture

The system is built on **LangGraph** with a "Supervisor" pattern orchestrating five subgraphs:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MAIN GRAPH                                     │
│                     (Supervisor / Orchestrator)                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌──────────────┐                                                           │
│  │   PLANNER    │ ──► Creates structured task list (research + write tasks) │
│  │  (GPT-120B)  │                                                           │
│  └──────────────┘                                                           │
│          │                                                                  │
│          ▼                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     CONDITIONAL ROUTER                               │   │
│  │         (Routes to Researcher/Writer based on task type)             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│          │                                     │                            │
│          ▼                                     ▼                            │
│  ┌──────────────┐                      ┌──────────────┐                     │
│  │  RESEARCHER  │                      │    WRITER    │                     │
│  │  (GPT-20B)   │                      │  (GPT-120B)  │                     │
│  │              │                      │              │                     │
│  │ ┌──────────┐ │                      │ ┌──────────┐ │                     │
│  │ │  Search  │ │                      │ │ Gather   │ │                     │
│  │ │  (DDG)   │ │                      │ │ Context  │ │                     │
│  │ └────┬─────┘ │                      │ └────┬─────┘ │                     │
│  │      ▼       │                      │      ▼       │                     │
│  │ ┌──────────┐ │                      │ ┌──────────┐ │                     │
│  │ │  Select  │ │                      │ │  Write   │ │                     │
│  │ │  URLs    │ │                      │ │ Section  │ │                     │
│  │ └────┬─────┘ │                      │ └────┬─────┘ │                     │
│  │      ▼       │                      │      ▼       │                     │
│  │ ┌──────────┐ │                      │ ┌──────────┐ │                     │
│  │ │  Scrape  │ │                      │ │  Append  │ │                     │
│  │ │ Content  │ │                      │ │ to Draft │ │                     │
│  │ └────┬─────┘ │                      │ └──────────┘ │                     │
│  │      ▼       │                      │              │                     │
│  │ ┌──────────┐ │                      │              │                     │
│  │ │Summarize │ │                      │              │                     │
│  │ │& Save VFS│ │                      │              │                     │
│  │ └──────────┘ │                      │              │                     │
│  └──────────────┘                      └──────────────┘                     │
│          │                                     │                            │
│          └──────────────┬──────────────────────┘                            │
│                         ▼                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         EVALUATOR SUBGRAPH                           │   │
│  │                    (Parallel Multi-Model Critique)                   │   │
│  │                                                                      │   │
│  │    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐               │   │
│  │    │    QWEN     │   │    KIMI     │   │   LLAMA 4   │               │   │
│  │    │  (32B)      │   │(k2-instruct)│   │ (Maverick)  │               │   │
│  │    │             │   │             │   │             │               │   │
│  │    │ SEO &       │   │ Engagement  │   │ Logic &     │               │   │
│  │    │ Structure   │   │ & Tone      │   │ Accuracy    │               │   │
│  │    └──────┬──────┘   └──────┬──────┘   └──────┬──────┘               │   │
│  │           │                 │                 │                      │   │
│  │           └─────────────────┼─────────────────┘                      │   │
│  │                             ▼                                        │   │
│  │                    ┌─────────────────┐                               │   │
│  │                    │    OPTIMIZER    │                               │   │
│  │                    │   (GPT-120B)    │                               │   │
│  │                    │                 │                               │   │
│  │                    │ Synthesizes all │                               │   │
│  │                    │ critiques and   │                               │   │
│  │                    │ rewrites draft  │                               │   │
│  │                    └─────────────────┘                               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                │                                            │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      HUMANIZER SUBGRAPH                              │   │
│  │                  (Reflexion Loop - up to 3 iterations)               │   │
│  │                                                                      │   │
│  │    ┌─────────────────┐         ┌─────────────────┐                   │   │
│  │    │  HUMANIZATION   │ ──────► │    REFINER      │                   │   │
│  │    │     CRITIC      │         │                 │                   │   │
│  │    │                 │         │ Chain of Density│                   │   │
│  │    │ Detects:        │         │ Sensory Inject  │                   │   │
│  │    │ - Hedging       │ ◄────── │ Kill Hedges     │                   │   │
│  │    │ - Connectors    │  Loop   │ Prune Connectors│                   │   │
│  │    │ - Nominalization│  if     │                 │                   │   │
│  │    │ - Sensory Vacuum│ score>3 │                 │                   │   │
│  │    └─────────────────┘         └─────────────────┘                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                │                                            │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    SEO ANALYSIS (PARALLEL)                           │   │
│  │                                                                      │   │
│  │    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐               │   │
│  │    │     FAQ     │   │  KEYWORDS   │   │   LINKING   │               │   │
│  │    │  GENERATOR  │   │  ANALYZER   │   │  SUGGESTER  │               │   │
│  │    │             │   │             │   │             │               │   │
│  │    │ 5-7 Q&A     │   │ Primary +   │   │ 3-5 Internal│               │   │
│  │    │ from        │   │ Secondary + │   │ 2-4 External│               │   │
│  │    │ research    │   │ LSI + Density│  │ with context│               │   │
│  │    └─────────────┘   └─────────────┘   └─────────────┘               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                │                                            │
│                                ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         FINALIZER                                    │   │
│  │     (SEO metadata + FAQ section + Keyword Report + Link Strategy)    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                │                                            │
│                                ▼                                            │
│                        [final_article.md]                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Models Used

| Purpose | Model | Provider | Temperature |
|---------|-------|----------|-------------|
| **Planning** | `openai/gpt-oss-120b` | Groq | 0.2 |
| **Research** | `openai/gpt-oss-20b` | Groq | 0.0 |
| **Writing** | `openai/gpt-oss-120b` | Groq | 0.4 |
| **Critique (SEO/Structure)** | `qwen/qwen3-32b` | Groq | 0.1 |
| **Critique (Engagement)** | `moonshotai/kimi-k2-instruct` | Groq | 0.2 |
| **Critique (Logic)** | `meta-llama/llama-4-maverick-17b-128e-instruct` | Groq | 0.1 |
| **Optimization** | `openai/gpt-oss-120b` | Groq | 0.2 |

---

## 🛠 Tech Stack

| Category | Technologies |
|----------|--------------|
| **Framework** | LangGraph (State Machine Orchestration) |
| **LLM Provider** | Groq (Fast Inference) |
| **RAG / Embeddings** | SentenceTransformers + FAISS |
| **API** | FastAPI + Uvicorn |
| **Web Search** | DDGS (DuckDuckGo Search) |
| **Web Scraping** | Trafilatura |
| **Persistence** | SQLite (Async) |
| **Validation** | Pydantic |
| **Testing** | Pytest |
| **Environment** | Python-dotenv |

---

## 📦 Installation

### Prerequisites

- Python 3.10+
- Groq API Key ([Get one here](https://console.groq.com))

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/raheelism/article-agent.git
   cd article-agent
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file
   echo "GROQ_API_KEY=your_groq_api_key_here" > .env
   ```

---

## ⚙ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ Yes | Your Groq API key for LLM access |

### Model Configuration

Models are configured in `app/core/llm.py`. Each model factory function can be customized:

```python
# Example: Modify temperature for writer
def get_writer_model():
    return get_model("openai/gpt-oss-120b", temperature=0.4)
```

---

## 🚀 Usage

### 1. CLI Mode (Development/Testing)

Run the agent directly from command line:

```bash
# Windows (PowerShell) or Linux/macOS
python scripts/run_agent.py "Benefits of Remote Work" --word-count 1000
```

**CLI Arguments:**

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `topic` | string | required | The article topic to write about |
| `--word-count` | int | 1500 | Target word count for the article |

**Output:** Final article saved to `Generated articles/{Topic}_{Timestamp}.md`

**Example Output Path:** `Generated articles/Benefits_of_Remote_Work_20251208_143052.md`

### Output Structure

The generated article includes:

```markdown
---
title: "SEO-Optimized Title (max 60 chars)"
meta_description: "Compelling description (max 160 chars)"
primary_keyword: "main keyword"
---

# Article Title

[Article content with proper H1/H2/H3 hierarchy...]

---

## ❓ Frequently Asked Questions

### What is [topic]?
[Answer based on research...]

### How do I [action]?
[Practical answer...]

[5-7 FAQ items total]

---

## 📊 SEO Analysis Report

### Keywords

**Primary Keyword:** `main keyword phrase`

**Secondary Keywords:**
- keyword 1
- keyword 2

**LSI Keywords:**
- related term 1
- related term 2

**Keyword Density:**
| Keyword | Density |
|---------|---------|
| main keyword | 1.5% |

**SEO Recommendations:**
- ✅ Primary keyword density is optimal (1.5%)
- 💡 Consider adding primary keyword to H2 headings

### 🔗 Linking Strategy

**Internal Links (3-5):**
| Anchor Text | Target Page | Context |
|-------------|-------------|---------|
| productivity tools | Best Tools Guide | In tools section |

**External Links (Authoritative Sources):**
| Source | Anchor Text | Placement |
|--------|-------------|-----------|
| Harvard Business Review | according to HBR | Support statistics |
```

### 2. API Mode (Production)

Start the FastAPI server:

```bash
# Windows (PowerShell) or Linux/macOS
uvicorn app.api.server:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

---

## 📡 API Reference

### Base URL
```
http://localhost:8000
```

### Endpoints

#### Create Job
```http
POST /jobs
Content-Type: application/json

{
  "topic": "Future of AI in Healthcare",
  "word_count": 1500,
  "language": "English"
}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "result": null
}
```

#### Get Job Status
```http
GET /jobs/{job_id}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": "# Article Title\n\nArticle content..."
}
```

**Job Status Values:**
- `pending` - Job queued
- `running` - Job in progress
- `completed` - Job finished successfully
- `failed` - Job encountered an error

---

## 📁 Project Structure

```
article-agent/
├── app/
│   ├── agents/
│   │   └── planner.py          # Planner agent - creates task list
│   ├── api/
│   │   └── server.py           # FastAPI server with job management
│   ├── core/
│   │   ├── llm.py              # LLM factory functions (Groq integration)
│   │   ├── state.py            # AgentState TypedDict definition
│   │   └── vfs.py              # Virtual File System implementation
│   ├── graphs/
│   │   ├── evaluator.py        # Evaluator subgraph (parallel critiques)
│   │   ├── faq.py              # FAQ generator (from research data)
│   │   ├── humanizer.py        # Humanizer subgraph (reflexion loop)
│   │   ├── keyword_analyzer.py # Keyword extraction and density analysis
│   │   ├── linking.py          # Internal/external link suggestions
│   │   ├── researcher.py       # Researcher subgraph (search/scrape/summarize)
│   │   └── writer.py           # Writer subgraph (RAG + draft generation)
│   ├── tools/
│   │   ├── scraper.py          # Web scraping with Trafilatura
│   │   └── search.py           # DDGS search provider
│   └── main_graph.py           # Main orchestration graph
├── plan/
│   ├── phase_1_foundation/     # Phase 1 implementation docs
│   ├── phase_2_agent_graph/    # Phase 2 implementation docs
│   ├── phase_3_service_quality/# Phase 3 implementation docs
│   ├── phase_4_humanization/   # Phase 4 implementation docs
│   ├── system_architecture/    # System architecture docs
│   └── README.md               # Development plan overview
├── scripts/
│   └── run_agent.py            # CLI entry point
├── tests/
│   ├── test_evaluator.py       # Evaluator tests
│   ├── test_humanizer.py       # Humanizer tests
│   ├── test_tools.py           # Tools tests
│   └── test_vfs.py             # VFS tests
├── Generated articles/         # Output folder for generated articles
│   └── {Topic}_{Timestamp}.md  # Articles named by topic and timestamp
├── requirements.txt            # Python dependencies
├── requirements.md             # Project requirements spec
└── README.md                   # This file
```

---

## 🔄 How It Works

### 1. Planning Phase
The Planner agent receives the topic and generates a structured task list:

```json
[
  {"id": 1, "type": "research", "description": "Research main topic keywords..."},
  {"id": 2, "type": "research", "description": "Find competitor articles..."},
  {"id": 3, "type": "write", "description": "Write introduction..."},
  {"id": 4, "type": "write", "description": "Write main body sections..."},
  {"id": 5, "type": "write", "description": "Write conclusion..."}
]
```

### 2. Research Phase
For each `research` task:
1. **Search** - Query DuckDuckGo for relevant results
2. **Select** - LLM picks top 2 most relevant URLs
3. **Scrape** - Extract content using Trafilatura
4. **Summarize** - LLM extracts key facts and saves to VFS

### 3. Writing Phase (RAG-Powered)
For each `write` task:
1. **Chunk Research** - Split research summaries into paragraphs
2. **Embed & Index** - Use SentenceTransformers to embed chunks, build FAISS index
3. **Retrieve Context** - Find top 4 most relevant chunks (~600-1000 tokens) for the current section
4. **Generate Content** - LLM writes section with "Absolute Mode" constraints (no robotic words, enforced burstiness)
5. **Append** - Add new content to `draft.md` in VFS

### 4. Evaluation Phase
Three parallel critics analyze the draft:

| Critic | Focus Areas |
|--------|-------------|
| **Qwen** | Header structure, keyword usage, internal linking, formatting |
| **Kimi** | Tone, flow, storytelling, hooks, conclusions |
| **Llama 4** | Logical consistency, clarity, factual accuracy, depth |

### 5. Optimization Phase
The Optimizer (GPT-120B):
- Synthesizes all three critiques
- Rewrites the article addressing all issues
- Maintains Markdown formatting

### 6. Humanization Phase (Reflexion Loop)
Up to 3 iterations of:
1. **Humanization Critic** - Analyzes for AI artifacts with detailed pattern matching:
   - Hedging ("It is important to note that..." → direct statements)
   - Connector overuse ("Moreover, Furthermore, Additionally" → natural flow)
   - Nominalization ("made a decision" → "decided")
   - Sensory vacuum (abstract → physical details)
   - AI vocabulary detection (delve, tapestry, leverage, robust, etc.)
   - Burstiness score (sentence length variety)
2. **Refiner Agent** - Rewrites using example-driven transformations:
   - Before/after patterns for hedge elimination
   - Sensory injection templates
   - Connector pruning with rhythm patterns
   - AI vocabulary replacement guide (20+ words)
3. **Loop Check** - If AI Artifact Score > 3, repeat; otherwise exit

**Banned Words List:**
```
delve, tapestry, landscape, unleash, foster, paramount, underscores,
game-changer, multifaceted, holistic, leverage, synergy, robust,
streamline, cutting-edge, revolutionary, transformative, comprehensive,
facilitate, utilize
```

### 7. SEO Analysis (Parallel)
After humanization, three agents run in parallel:

1. **FAQ Generator** - Creates 5-7 Q&A pairs from research data
2. **Keyword Analyzer** - Extracts primary/secondary/LSI keywords with density analysis
3. **Linking Suggester** - Generates 3-5 internal + 2-4 external link suggestions

### 8. Finalization
- Generates SEO metadata (title tag, meta description)
- Appends FAQ section to article
- Appends keyword analysis report
- Appends linking strategy tables
- Saves final article to `Generated articles/{Topic}_{Timestamp}.md`

---

## 📊 State Management

### AgentState Schema

```python
class AgentState(TypedDict):
    # User Inputs
    topic: str              # Article topic
    word_count: int         # Target word count
    language: str           # Output language (default: English)
    
    # Execution State
    plan: List[Task]        # List of tasks to execute
    current_task_index: int # Current task pointer
    
    # Virtual File System (serializable)
    vfs_data: Dict[str, Dict]  # Filename -> File content/metadata
    
    # SEO Analysis Results
    faqs: List[FAQItem]           # Generated FAQ section
    keyword_report: KeywordReport # Keyword analysis
    linking_report: LinkingReport # Link suggestions
    
    # Logging
    logs: List[str]         # Execution logs (append-only)
```

### SEO Report Schemas

```python
class FAQItem(TypedDict):
    question: str
    answer: str

class KeywordReport(TypedDict):
    primary_keyword: str
    secondary_keywords: List[str]
    lsi_keywords: List[str]
    keyword_density: Dict[str, float]
    recommendations: List[str]
    total_words: int

class LinkingReport(TypedDict):
    internal_links: List[InternalLink]  # anchor, target, context
    external_links: List[ExternalLink]  # source, url, anchor, placement
```

### Task Schema

```python
class Task(TypedDict):
    id: int                 # Task ID
    description: str        # Task description
    type: str              # 'research' | 'write' | 'review'
    status: str            # 'pending' | 'completed' | 'failed'
    params: Dict           # Additional parameters
```

### Virtual File System

The VFS provides an abstraction layer for storing intermediate artifacts:

```python
vfs = VFS()
vfs.write_file("research/topic1.md", "Summary content...", metadata={"url": "https://..."})
vfs.write_file("draft.md", "Article content...")
content = vfs.read_file("draft.md")
files = vfs.list_files()  # ["research/topic1.md", "draft.md"]
```

---

## 🧪 Testing

Run the test suite:

```bash
# Windows (PowerShell) or Linux/macOS
pytest

# With verbose output
pytest -v

# Run specific test file
pytest tests/test_vfs.py
pytest tests/test_humanizer.py
```

---

## 📈 Development Plan

The project follows a phased development approach:

| Phase | Focus | Status |
|-------|-------|--------|
| **Phase 1** | Foundation (Core infrastructure, VFS, LLM) | ✅ Complete |
| **Phase 2** | Agent Graph (Subgraphs, routing, orchestration) | ✅ Complete |
| **Phase 3** | Service & Quality (API, persistence, evaluation) | ✅ Complete |
| **Phase 4** | Humanization (RAG writing, reflexion loop, anti-AI prompts) | ✅ Complete |
| **Phase 5** | SEO Analysis (FAQ generator, keyword analyzer, linking suggester) | ✅ Complete |

See [`plan/`](plan/) directory for detailed implementation guides.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/raheelism">raheelism</a>
</p>
