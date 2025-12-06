# Phase 2: Agent Graph (Hours 3-5)

## Goal
Build the "Brain" of the operation. This involves creating the LangGraph nodes, defining the subgraphs, and connecting them.

## Implementation Steps

### 1. The Planner Node (`app/agents/planner.py`)
- [ ] Design the prompt: "You are a content strategist. Given a topic, break it down into research and writing steps."
- [ ] Define Structured Output: `Plan` object containing a list of `Task` items.
    - `Task`: `id`, `type` (research/write), `description`, `status`.
- [ ] Implement the node function `plan_step(state)`.

### 2. The Research Subgraph (`app/graphs/researcher.py`)
- [ ] **Node: Search:** Uses the `SearchTool` to find URLs based on the task description.
- [ ] **Node: Select:** Uses LLM (20b) to pick the best 2-3 URLs from the search results.
- [ ] **Node: Scrape:** Loops through selected URLs and fetches content.
- [ ] **Node: Summarize:** Uses LLM (20b) to condense the scraped content into a markdown summary.
- [ ] **Node: Save:** Writes the summary to VFS (e.g., `research/topic_name.md`).
- [ ] **Wiring:** Connect these nodes into a compiled `StateGraph`.

### 3. The Writer Subgraph (`app/graphs/writer.py`)
- [ ] **Node: Gather Context:** 
    - LLM decides which files to read from VFS based on the task.
    - Or, simpler v1: Read *all* files in `research/` directory (if total tokens < limit).
- [ ] **Node: Draft:**
    - Prompt: "You are an SEO writer. Write the section described in the task using the provided context."
    - Output: Markdown text.
- [ ] **Node: Save Draft:** Appends the new section to `draft.md` in VFS.

### 4. The Main Orchestrator (`app/main_graph.py`)
- [ ] Create the Supervisor/Router loop.
- [ ] Logic:
    1.  Check `state.plan`.
    2.  Find first `pending` task.
    3.  If Research -> Call Research Subgraph.
    4.  If Write -> Call Writer Subgraph.
    5.  Mark task `completed`.
    6.  Loop.
    7.  If all completed -> End.

### 5. Testing the Graph
- [ ] Create integration tests using `MockSearchProvider`.
- [ ] Run the full graph on a simple topic ("Apples").
- [ ] Verify `draft.md` exists in VFS at the end.

## Success Criteria for Phase 2
- A script `scripts/run_agent.py "topic"` produces a full article in `draft.md`.
- The process is observable (logs show planning -> research -> writing).
