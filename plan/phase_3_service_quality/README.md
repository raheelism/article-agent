# Phase 3: Service & Quality (Hour 6) ✅ COMPLETE

## Goal
Turn the script into a service, ensure persistence, and polish the output quality.

## Implementation Steps

### 1. FastAPI Wrapper (`app/api/server.py`)
- [x] POST `/jobs`: Accepts `topic`, `word_count`. Returns `job_id`.
- [x] GET `/jobs/{job_id}`: Returns status and current state (or final artifact).
- [x] Background Task: Run the LangGraph execution in a background thread.

### 2. Persistence (SQLite)
- [x] Set up `SqliteSaver` from `langgraph.checkpoint.sqlite`.
- [x] Pass the `checkpointer` to the `graph.compile()`.
- [x] Verify that if the server restarts, the job can be resumed (by reloading the state from DB).

### 3. SEO & Quality Tuning
- [x] **Prompt Engineering:** Refine the Writer prompt.
    - Ensure it outputs H1/H2/H3 correctly.
    - Force it to include the "Primary Keyword" in the first paragraph.
- [x] **Metadata Generation:** Add a final step to generate Title Tag and Meta Description based on the `draft.md`.
- [x] **Linking:** Add instructions to the Writer to insert `[Internal Link: ...]` placeholders.

### 4. Final Polish
- [x] Add `README.md` instructions on how to run locally.
- [x] Output articles to `Generated articles/{Topic}_{Timestamp}.md`.

## Success Criteria for Phase 3 ✅
- User can curl the API to start a job.
- User can poll the API to get the result.
- The result is a well-formatted Markdown article with SEO metadata.
