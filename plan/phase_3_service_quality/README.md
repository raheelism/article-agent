# Phase 3: Service & Quality (Hour 6)

## Goal
Turn the script into a service, ensure persistence, and polish the output quality.

## Implementation Steps

### 1. FastAPI Wrapper (`app/api/server.py`)
- [ ] POST `/jobs`: Accepts `topic`, `word_count`. Returns `job_id`.
- [ ] GET `/jobs/{job_id}`: Returns status and current state (or final artifact).
- [ ] Background Task: Run the LangGraph execution in a background thread (or better, use LangGraph's async runner).

### 2. Persistence (PostgreSQL)
- [ ] Set up `AsyncPostgresSaver` from `langgraph.checkpoint.postgres`.
- [ ] Pass the `checkpointer` to the `graph.compile()`.
- [ ] Verify that if the server restarts, the job can be resumed (by reloading the state from DB).
    - *Note: For the scope of this 4-6h task, a simpler `SqliteSaver` or just in-memory persistence might be accepted if Postgres setup is too heavy, but the plan calls for Postgres durability.*

### 3. SEO & Quality Tuning
- [ ] **Prompt Engineering:** Refine the Writer prompt.
    - Ensure it outputs H1/H2/H3 correctly.
    - Force it to include the "Primary Keyword" in the first paragraph.
- [ ] **Metadata Generation:** Add a final step to generate Title Tag and Meta Description based on the `draft.md`.
- [ ] **Linking:** Add instructions to the Writer to insert `[Internal Link: ...]` placeholders.

### 4. Final Polish
- [ ] Add `README.md` instructions on how to run via Docker or locally.
- [ ] Add `example_output.md`.

## Success Criteria for Phase 3
- User can curl the API to start a job.
- User can poll the API to get the result.
- The result is a well-formatted Markdown article with SEO metadata.
