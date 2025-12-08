# Phase 2: Agent Graph (Hours 3-5) ✅ COMPLETE

## Goal
Build the "Brain" of the operation. This involves creating the LangGraph nodes, defining the subgraphs, and connecting them.

## Implementation Steps

### 1. The Planner Node (`app/agents/planner.py`)
- [x] Design the prompt: "You are a content strategist. Given a topic, break it down into research and writing steps."
- [x] Define Structured Output: `Plan` object containing a list of `Task` items.
    - `Task`: `id`, `type` (research/write), `description`, `status`.
- [x] Implement the node function `plan_step(state)`.

### 2. The Research Subgraph (`app/graphs/researcher.py`)
- [x] **Node: Search:** Uses the `SearchTool` to find URLs based on the task description.
- [x] **Node: Select:** Uses LLM (20b) to pick the best 2-3 URLs from the search results.
- [x] **Node: Scrape:** Loops through selected URLs and fetches content.
- [x] **Node: Summarize:** Uses LLM (20b) to condense the scraped content into a markdown summary.
- [x] **Node: Save:** Writes the summary to VFS (e.g., `research/topic_name.md`).
- [x] **Wiring:** Connect these nodes into a compiled `StateGraph`.

### 3. The Writer Subgraph (`app/graphs/writer.py`)
- [x] **Node: Gather Context:** 
    - RAG-based retrieval using SentenceTransformers + FAISS.
    - Retrieves only relevant research chunks (~600-1000 tokens) per section.
- [x] **Node: Draft:**
    - Prompt with anti-AI writing constraints and example transformations.
    - Bans 20+ robotic words and enforces sentence burstiness.
    - Output: Human-like Markdown text.
- [x] **Node: Save Draft:** Appends the new section to `draft.md` in VFS.

### 4. The Main Orchestrator (`app/main_graph.py`)
- [x] Create the Supervisor/Router loop.
- [x] Logic:
    1.  Check `state.plan`.
    2.  Find first `pending` task.
    3.  If Research -> Call Research Subgraph.
    4.  If Write -> Call Writer Subgraph.
    5.  Mark task `completed`.
    6.  Loop.
    7.  If all completed -> Proceed to Evaluation.

### 5. Testing the Graph
- [x] Create integration tests using `MockSearchProvider`.
- [x] Run the full graph on a simple topic.
- [x] Verify `draft.md` exists in VFS at the end.

## Success Criteria for Phase 2 ✅
- A script `scripts/run_agent.py "topic"` produces a full article in `Generated articles/` folder.
- The process is observable (logs show planning -> research -> writing).
