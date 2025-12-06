# System Architecture: Deep Agent with VFS

## 1. High-Level Concept

The system is designed as a **Deep Agent**, meaning it breaks down complex tasks (like writing an entire article) into smaller, discrete steps that are executed over a longer period. It does not attempt to solve the problem in a single zero-shot prompt.

Key differentiating features:
- **Virtual Filesystem (VFS):** Decouples "Working Memory" (context window) from "Long-Term Storage" (research files). The agent can "read" and "write" files, allowing it to handle infinite research depth.
- **Hierarchical Planning:** A "Planner" agent breaks the goal into tasks, which are executed by "Worker" sub-agents (Researcher, Writer).
- **Subgraphs (LangGraph):** Each distinct capability (Research, Writing) is encapsulated as a reusable subgraph.

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

As requested, we leverage **GPT OSS** models via Groq:

- **Planner (openai/gpt-oss-120b):** High intelligence, used for understanding the user request and creating a strategic plan.
- **Researcher (openai/gpt-oss-20b):** Fast, used for summarizing search results and extracting keywords.
- **Writer (openai/gpt-oss-120b):** High quality, used for the final prose generation.

*Note: If cost is a major constraint, the Planner can be downgraded to 20B, but for "Senior Engineer" quality, 120B is preferred for planning.*

## 3. Workflow (The Graph)

### 3.1 Main Graph
1.  **Start** -> **Planner**
2.  **Planner** generates a list of tasks (e.g., ["Research Keyword X", "Research Competitors", "Outline", "Write Intro", ...])
3.  **Router** looks at the `current_task`.
    - If task type is "research" -> Send to **Research Subgraph**
    - If task type is "write" -> Send to **Writer Subgraph**
    - If task type is "review" -> Send to **Reviewer** (Bonus)
    - If no more tasks -> **End**

### 3.2 Research Subgraph
1.  **Input:** A research query (e.g., "remote work statistics 2024")
2.  **Search Node:** Queries DuckDuckGo (or Mock). Returns list of URLs.
3.  **Select Node:** LLM picks the top 3 most relevant URLs.
4.  **Scrape Node:** Fetches content (trafilatura).
5.  **Summarize Node:** LLM summarizes content into key facts.
6.  **Save Node:** Writes `summary_{query}.md` to VFS.
7.  **Output:** Success signal.

### 3.3 Writer Subgraph
1.  **Input:** A writing task (e.g., "Write the Introduction section")
2.  **Context Assembly:** Agent calls `vfs.list_files()` then `vfs.read_file()` to gather necessary context.
3.  **Drafting:** Agent generates text using the context.
4.  **Output:** Agent updates the "Draft" file in VFS (e.g., appends to `draft.md`).

## 4. Technology Stack

- **Orchestration:** LangGraph
- **LLM Serving:** Groq API
- **Models:** openai/gpt-oss-120b, openai/gpt-oss-20b
- **Web Search:** DuckDuckGo (via `duckduckgo-search` package)
- **Scraping:** Trafilatura
- **Backend:** FastAPI
- **Persistence:** PostgreSQL (via LangGraph Checkpointers)

