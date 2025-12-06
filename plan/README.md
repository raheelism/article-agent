# Implementation Plan: Article Agent SEO Content Platform

## 1. Executive Summary
This project implements an autonomous **Deep Agent** designed to generate high-quality, SEO-optimized articles. Unlike shallow agents relying on a single context window, this system uses a **Virtual Filesystem (VFS)** to decouple *Working Memory* (active context) from *Long-term Storage* (research data).

The system is orchestrated via **LangGraph**, using:

- **GPT OSS 120B** → Planning + Research  
- **GPT OSS 120B** → High-fidelity writing  

Additional features include a self-healing scraping layer and PostgreSQL-backed checkpointing for crash-safe execution.

---

## 2. System Architecture

### 2.1 Core Components

- **Orchestrator:** LangGraph (state machine + cyclical flows)  
- **Intelligence:**  
  - **Planner/Researcher:** Groq — GPT OSS 120B  
  - **Writer:** Groq — GPT OSS 120B  
- **Memory:** Virtual Filesystem (VFS)  
- **Perception:** DuckDuckGo Search + Trafilatura Scraping  
- **Persistence:** PostgreSQL checkpoints + FastAPI service layer  

---

### 2.2 Global State Schema

```python
from typing import List, Dict, Annotated
from pydantic import BaseModel, Field
import operator

class File(BaseModel):
    name: str
    content: str
    metadata: Dict[str, str] = {}  # e.g., source_url, author

class AgentState(BaseModel):
    # User Inputs
    topic: str
    word_count: int = 1500
    language: str = "English"
    
    # Internal State
    vfs: Dict[str, File] = {}  # The Virtual Filesystem
    plan: List[Dict] = []      # The Execution Plan
    current_step: int = 0
    search_results: List[Dict] = []
    
    # Audit Trail
    logs: Annotated[List[str], operator.add]
```

---

## 3. The "Deep Agent" Implementation

### 3.1 Phase 1: The Virtual Filesystem (VFS)

The VFS stores all research independently from the model’s context window.

**Tools:**

- **ls:** List files  
- **read_file:** Return file contents (truncates >10k chars)  
- **write_file:** Save research summaries  

---

### 3.2 Phase 2: Planner Agent (Llama 3.1 8B)

The planner generates a structured task plan.

**Example Input:**  
`"Best productivity tools"`

**Planner Output:**

```json
{
  "steps": [
    {"id": 1, "action": "research_serp", "params": {"query": "best productivity tools remote teams"}},
    {"id": 2, "action": "research_competitor", "params": {"url": "https://competitor.com/top-10-tools"}},
    {"id": 3, "action": "generate_outline", "params": {}},
    {"id": 4, "action": "write_section", "params": {"section": "Introduction"}}
  ]
}
```

---

### 3.3 Phase 3: Researcher Subgraph (GPT OSS 120B)

Handles searching, filtering, scraping, summarization, and VFS storage.

**Workflow:**

1. Search via DuckDuckGo  
2. Filter → Select best Top 3  
3. Scrape using trafilatura  
4. Retry on failures  
5. Summarize using GPT OSS 120B  
6. Save to `vfs/research/source_{i}.md`

---

### 3.4 Phase 4: Writer Agent (GPT OSS 120B)

The only agent allowed to generate final prose.

**Strategy:**

1. List files (ls)  
2. Read relevant research  
3. Write the section using SEO-optimized structure  

**SEO Enhancements:**

- Inserts placeholders for internal links:  
  `[Internal Link: <anchor> -> <topic>]`
- External authority citations: Uses metadata in VFS  

---

## 4. Technical Specifications

### 4.1 SERP Analysis & Data Mocking

```python
class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str) -> List[SearchResult]:
        pass

class DuckDuckGoProvider(SearchProvider):
    def search(self, query: str):
        # exponential backoff
        pass

class MockSearchProvider(SearchProvider):
    def search(self, query: str):
        return [
            {"rank": 1, "url": "https://mock.com/1", "title": "Mock Result 1", "snippet": "..."}
        ]
```

---

### 4.2 Durability & Resume (PostgreSQL)

- **Checkpoint every step**  
- **Recoverable** via `thread_id`  
- Uses LangGraph persistence to restore full state  

---

### 4.3 Output Validation

```python
class FinalArticle(BaseModel):
    title: str
    meta_description: str
    keywords_used: List[str]
    content_markdown: str
    internal_links: List[LinkSuggestion]
    external_references: List[Reference]
```

---

## 5. Development Roadmap

### **Phase 1 (Hours 1–2): Foundation**

- Setup FastAPI, LangGraph, Pydantic  
- Implement VFS  
- DuckDuckGo wrapper  
- MockSearchProvider  

### **Phase 2 (Hours 3–5): Agent Graph**

- Planner node  
- Researcher loop (search → filter → scrape → summarization)  
- Writer with context-pulling  
- Connect nodes with LangGraph  

### **Phase 3 (Hour 6): Service & Quality**

- FastAPI endpoint `/generate`  
- PostgreSQL saver  
- SEO prompt tuning  
- Unit tests  

---

## 6. Directory Structure (GitHub)

```
seo-agent/
├── app/
│   ├── agents/
│   │   ├── planner.py
│   │   ├── researcher.py
│   │   └── writer.py
│   ├── core/
│   │   ├── vfs.py
│   │   ├── state.py
│   │   └── config.py
│   ├── tools/
│   │   ├── search.py
│   │   └── scraper.py
│   └── main.py
├── tests/
│   ├── test_vfs.py
│   └── test_agents.py
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 7. Quality & SEO Principles Checklist

- [ ] **Primary Keyword:** Present in H1 and first 100 words  
- [ ] **Heading Hierarchy:** Proper H2/H3 nesting  
- [ ] **External Authority:** Minimum 2 citations from research phase  
- [ ] **Internal Linking:** 3–5 internal link suggestions  
- [ ] **Readability:** Varied sentence length & structure  
