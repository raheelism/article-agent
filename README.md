# Article Agent

A "Deep Agent" system for generating high-quality, SEO-optimized articles using LangGraph, FastAPI, and Groq (Llama 3 / GPT OSS).

## Features

- **Deep Research:** autonomous agent that searches the web, selects relevant sources, scrapes content, and summarizes it.
- **Multi-Agent Evaluation:** A parallel critique system that uses specialized models to evaluate drafts on SEO, Engagement, and Logic before optimization.
- **Virtual Filesystem (VFS):** Decouples "Working Memory" from research data, allowing for infinite research depth without blowing up context windows.
- **Structured Planning:** A Planner agent breaks down topics into executable research and writing tasks.
- **Persistence:** Jobs are persisted to SQLite, allowing for resume capability (architecture ready).
- **Service Layer:** FastAPI backend for managing content generation jobs.

## Architecture

The system is built on **LangGraph** with a "Supervisor" pattern orchestrating four subgraphs:

1.  **Planner:** Generates the task list.
2.  **Researcher:** `Search -> Select -> Scrape -> Summarize -> Save to VFS`.
3.  **Writer:** `Read VFS -> Write Section -> Append to Draft`.
4.  **Evaluator:** `Parallel Critiques (Qwen/Kimi/Llama) -> Optimizer (GPT-OSS-120B)`.

Models used:
- **Planning/Writing/Optimization:** `openai/gpt-oss-120b` (via Groq)
- **Research:** `openai/gpt-oss-20b` (via Groq)
- **Critique (SEO/Structure):** `qwen/qwen3-32b`
- **Critique (Engagement/Tone):** `moonshotai/kimi-k2-instruct`
- **Critique (Logic/Accuracy):** `meta-llama/llama-4-maverick-17b-128e-instruct`

## Installation

1.  **Clone the repository**
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set Environment Variables:**
    Create a `.env` file or export:
    ```bash
    export GROQ_API_KEY=your_key_here
    ```

## Usage

### 1. Run via CLI (for testing)

```bash
PYTHONPATH=. python scripts/run_agent.py "Benefits of Remote Work" --word-count 1000
```

The final output will be saved to `final_article.md` (or printed to stdout).

### 2. Run as a Service (API)

Start the server:
```bash
PYTHONPATH=. uvicorn app.api.server:app --port 8000
```

**API Endpoints:**

-   `POST /jobs`: Submit a new article request.
    ```json
    {
      "topic": "Future of AI in Healthcare",
      "word_count": 1500
    }
    ```
-   `GET /jobs/{job_id}`: Check status and retrieve result.

### 3. Run Tests

```bash
PYTHONPATH=. pytest
```

## Directory Structure

-   `app/agents/`: Logic for individual agents (Planner).
-   `app/core/`: Core abstractions (VFS, State, LLM factory).
-   `app/graphs/`: Subgraph definitions (Researcher, Writer, Evaluator).
-   `app/tools/`: Tool implementations (Search, Scrape).
-   `app/api/`: FastAPI server.
-   `plan/`: Detailed implementation guides and architecture docs.
