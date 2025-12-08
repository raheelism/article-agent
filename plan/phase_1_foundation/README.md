# Phase 1: Foundation (Hours 1-2) ✅ COMPLETE

## Goal
Establish the core infrastructure: The Virtual Filesystem, the basic State definition, and the Search/Scrape tools. By the end of this phase, we should be able to run a script that searches the web, scrapes a page, and saves it to an in-memory VFS.

## Implementation Steps

### 1. Project Setup
- [x] Initialize Python project (poetry or pip).
- [x] Install dependencies: `langgraph`, `langchain-groq`, `pydantic`, `fastapi`, `uvicorn`, `duckduckgo-search`, `trafilatura`.
- [x] Set up `pytest`.

### 2. Core Domain Models (`app/core/state.py`)
- [x] Define `File` Pydantic model.
- [x] Define `AgentState` TypedDict (or Pydantic model).
- [x] Implement `VFS` class methods:
    - `list()`
    - `read(filename)`
    - `write(filename, content)`
    - `exists(filename)`

### 3. Tool Implementations (`app/tools/`)
- [x] **Search Tool:**
    - Create `SearchProvider` abstract base class.
    - Implement `DuckDuckGoSearchProvider` (using `ddgs`).
    - Implement `MockSearchProvider` (crucial for repeatable testing).
    - *The output should be a list of `SearchResult` objects (url, title, snippet).*
- [x] **Scraper Tool:**
    - Implement `WebScraper` class using `trafilatura`.
    - Handle timeouts and basic errors.
    - SSL bypass support for corporate networks.
    - Implement `MockScraper` for offline testing.

### 4. LLM Setup (`app/core/llm.py`)
- [x] Configure `ChatGroq` client with SSL bypass support.
- [x] Create factory functions:
    - `get_planner_model()` -> gpt-oss-120b
    - `get_researcher_model()` -> gpt-oss-20b
    - `get_writer_model()` -> gpt-oss-120b
    - `get_critic_model()` -> Multiple models (Qwen, Kimi, Llama 4)

### 5. Initial Tests
- [x] Test VFS read/write operations.
- [x] Test MockSearchProvider returns expected data.
- [x] Test LLM connection (simple "hello world" prompt).

## Success Criteria for Phase 1 ✅
- `pytest` passes for VFS logic.
- A script `scripts/test_tools.py` can successfully:
    1.  Search for a term (mock or real).
    2.  "Scrape" a URL.
    3.  Save the content to the VFS.
    4.  Read it back.
