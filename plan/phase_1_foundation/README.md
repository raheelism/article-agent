# Phase 1: Foundation (Hours 1-2)

## Goal
Establish the core infrastructure: The Virtual Filesystem, the basic State definition, and the Search/Scrape tools. By the end of this phase, we should be able to run a script that searches the web, scrapes a page, and saves it to an in-memory VFS.

## Implementation Steps

### 1. Project Setup
- [ ] Initialize Python project (poetry or pip).
- [ ] Install dependencies: `langgraph`, `langchain-groq`, `pydantic`, `fastapi`, `uvicorn`, `duckduckgo-search`, `trafilatura`.
- [ ] Set up `pytest`.

### 2. Core Domain Models (`app/core/state.py`)
- [ ] Define `File` Pydantic model.
- [ ] Define `AgentState` TypedDict (or Pydantic model).
- [ ] Implement `VFS` class methods:
    - `list()`
    - `read(filename)`
    - `write(filename, content)`
    - `exists(filename)`

### 3. Tool Implementations (`app/tools/`)
- [ ] **Search Tool:**
    - Create `SearchProvider` abstract base class.
    - Implement `DuckDuckGoSearchProvider`.
    - Implement `MockSearchProvider` (crucial for repeatable testing).
    - *The output should be a list of `SearchResult` objects (url, title, snippet).*
- [ ] **Scraper Tool:**
    - Implement `WebScraper` class using `trafilatura`.
    - Handle timeouts and basic errors.
    - Implement `MockScraper` for offline testing.

### 4. LLM Setup (`app/core/llm.py`)
- [ ] Configure `ChatGroq` client.
- [ ] Create factory functions:
    - `get_planner_model()` -> gpt-oss-120b
    - `get_researcher_model()` -> gpt-oss-20b
    - `get_writer_model()` -> gpt-oss-120b

### 5. Initial Tests
- [ ] Test VFS read/write operations.
- [ ] Test MockSearchProvider returns expected data.
- [ ] Test LLM connection (simple "hello world" prompt).

## Success Criteria for Phase 1
- `pytest` passes for VFS logic.
- A script `scripts/test_tools.py` can successfully:
    1.  Search for a term (mock or real).
    2.  "Scrape" a URL.
    3.  Save the content to the VFS.
    4.  Read it back.
