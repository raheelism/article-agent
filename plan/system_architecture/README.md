# System Architecture: Deep Agent with VFS

## 🎯 Key Achievement: 0% AI Detection

> Generated articles pass AI detection tools with **0% AI-detected content**, making them indistinguishable from human writing.

## 1. High-Level Concept

The system is designed as a **Deep Agent**, meaning it breaks down complex tasks (like writing an entire article) into smaller, discrete steps that are executed over a longer period. It does not attempt to solve the problem in a single zero-shot prompt.

Key differentiating features:
- **Virtual Filesystem (VFS):** Decouples "Working Memory" (context window) from "Long-Term Storage" (research files). The agent can "read" and "write" files, allowing it to handle infinite research depth.
- **Hierarchical Planning:** A "Planner" agent breaks the goal into tasks, which are executed by "Worker" sub-agents (Researcher, Writer).
- **Subgraphs (LangGraph):** Each distinct capability (Research, Writing, Evaluation, Humanization) is encapsulated as a reusable subgraph.
- **RAG-Powered Writing:** Uses SentenceTransformers + FAISS to retrieve only relevant research chunks per section.
- **Multi-Model Evaluation:** Three specialized critics (Qwen, Kimi, Llama 4) evaluate drafts in parallel.
- **Reflexion Humanization:** Iterative loop that detects and removes AI artifacts until 0% AI detection is achieved.

## 2. Core Components

### 2.1 The Virtual Filesystem (VFS)

The VFS is a Python dictionary-based abstraction that mimics a file system.

```python
class File(BaseModel):
    name: str          # e.g., "competitor_analysis.md"
    content: str       # The actual text content
    metadata: Dict     # e.g., {"source": "https://...", "timestamp": "..."}

class VFS:
    files: Dict[str, File]
    
    def list_files(self) -> List[str]: ...
    def read_file(self, filename: str) -> str: ...
    def write_file(self, filename: str, content: str, metadata: Dict = None): ...
```

**Why this matters:**
The 120B model has a context limit. If we scrape 10 websites, we cannot fit them all in context. The VFS allows the researcher to scrape 100 sites, summarize them into small files, and then the Writer only "reads" the summaries it needs.

### 2.2 The Global State

The state is passed between all nodes in the LangGraph.

```python
class AgentState(TypedDict):
    # User Request
    topic: str
    word_count: int
    language: str
    
    # Execution State
    plan: List[Task]           # The checklist of things to do
    current_task_index: int    # Where are we?
    vfs: VFS                   # The shared memory
    logs: List[str]            # Audit trail
```

### 2.3 The Models

We leverage multiple **Groq** models for different purposes:

| Purpose | Model | Temperature | Notes |
|---------|-------|-------------|-------|
| **Planner** | `openai/gpt-oss-120b` | 0.2 | Strategic planning |
| **Researcher** | `openai/gpt-oss-20b` | 0.0 | Fast summarization |
| **Writer** | `openai/gpt-oss-120b` | 0.4 | Human-like prose |
| **Critic (SEO)** | `qwen/qwen3-32b` | 0.1 | Structure analysis |
| **Critic (Engagement)** | `moonshotai/kimi-k2-instruct` | 0.2 | Tone evaluation |
| **Critic (Logic)** | `meta-llama/llama-4-maverick-17b-128e-instruct` | 0.1 | Accuracy check |
| **Optimizer** | `openai/gpt-oss-120b` | 0.2 | Critique synthesis |
| **Humanizer** | `openai/gpt-oss-120b` | 0.4 | AI artifact removal |

## 3. Workflow (The Graph)

### 3.1 Main Graph
1.  **Start** -> **Planner**
2.  **Planner** generates a list of tasks (e.g., ["Research Keyword X", "Research Competitors", "Outline", "Write Intro", ...])
3.  **Router** looks at the `current_task`.
    - If task type is "research" -> Send to **Research Subgraph**
    - If task type is "write" -> Send to **Writer Subgraph**
    - If all tasks completed -> Send to **Evaluator Subgraph**
4.  **Evaluator** runs 3 parallel critics + optimizer
5.  **Humanizer** runs reflexion loop (up to 3 iterations)
6.  **Finalizer** generates SEO metadata and saves to file

### 3.2 Research Subgraph
1.  **Input:** A research query (e.g., "remote work statistics 2024")
2.  **Search Node:** Queries DuckDuckGo. Returns list of URLs.
3.  **Select Node:** LLM picks the top 3 most relevant URLs.
4.  **Scrape Node:** Fetches content (trafilatura).
5.  **Summarize Node:** LLM summarizes content into key facts.
6.  **Save Node:** Writes `summary_{query}.md` to VFS.
7.  **Output:** Success signal.

### 3.3 Writer Subgraph (RAG-Powered)
1.  **Input:** A writing task (e.g., "Write the Introduction section")
2.  **RAG Retrieval:** Uses SentenceTransformers + FAISS to find relevant chunks.
3.  **Drafting:** Agent generates human-like text using anti-AI constraints.
4.  **Output:** Agent updates the "Draft" file in VFS.

### 3.4 Evaluator Subgraph
1.  **Input:** Draft article
2.  **Parallel Critics:** 3 models evaluate SEO, Engagement, Logic simultaneously.
3.  **Optimizer:** Synthesizes all critiques and rewrites.
4.  **Output:** Improved draft.

### 3.5 Humanizer Subgraph
1.  **Input:** Evaluated draft
2.  **Critic:** Detects AI artifacts (hedging, connectors, nominalization, etc.)
3.  **Refiner:** Rewrites with human voice using before/after examples.
4.  **Loop:** Repeats up to 3x until score is acceptable.
5.  **Output:** Human-like article (0% AI detection).

## 4. Technology Stack

- **Orchestration:** LangGraph
- **LLM Serving:** Groq API
- **Embedding:** SentenceTransformers (all-MiniLM-L6-v2)
- **Vector Store:** FAISS
- **Models:** openai/gpt-oss-120b, openai/gpt-oss-20b
- **Web Search:** DuckDuckGo (via `duckduckgo-search` package)
- **Scraping:** Trafilatura
- **Backend:** FastAPI
- **Persistence:** PostgreSQL (via LangGraph Checkpointers)

