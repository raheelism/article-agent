import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
import re
from datetime import datetime
from typing import Dict, Optional, Any
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from app.main_graph import create_main_graph
import aiosqlite
import json


def sanitize_filename(topic: str) -> str:
    """Convert topic to a safe filename."""
    filename = re.sub(r'[<>:"/\\|?*]', '', topic)
    filename = re.sub(r'\s+', '_', filename.strip())
    filename = filename[:50]
    return filename

app = FastAPI(title="Article Agent API")

# In-memory job tracker
jobs: Dict[str, Dict] = {}

class JobRequest(BaseModel):
    topic: str
    word_count: int = 1500
    language: str = "English"

class JobResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[str] = None

async def run_agent_background(job_id: str, request: JobRequest):
    jobs[job_id]["status"] = "running"
    
    # Setup Async Persistence
    try:
        async with aiosqlite.connect("agent_state.db") as conn:
            checkpointer = AsyncSqliteSaver(conn)
            
            config = {"configurable": {"thread_id": job_id}}
            graph = create_main_graph(checkpointer=checkpointer)
            
            initial_state = {
                "topic": request.topic,
                "word_count": request.word_count,
                "language": request.language,
                "plan": [],
                "current_task_index": 0,
                "vfs_data": {},
                "logs": []
            }
            
            # Run graph
            final_state = await graph.ainvoke(initial_state, config=config)
            
            # Extract result
            vfs_data = final_state.get("vfs_data", {})
            content = ""
            
            def get_content(f):
                if hasattr(f, 'content'): return f.content
                if isinstance(f, dict): return f.get('content', '')
                return str(f)
                
            if "final_article.md" in vfs_data:
                content = get_content(vfs_data["final_article.md"])
            elif "draft.md" in vfs_data:
                content = get_content(vfs_data["draft.md"])
            
            # Save to Generated articles folder
            if content:
                output_dir = "Generated articles"
                os.makedirs(output_dir, exist_ok=True)
                
                safe_name = sanitize_filename(request.topic)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{safe_name}_{timestamp}.md"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                
                jobs[job_id]["filepath"] = filepath
                
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["result"] = content
            
    except Exception as e:
        print(f"Job failed: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = str(e)

@app.post("/jobs", response_model=JobResponse)
async def create_job(request: JobRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "pending", "request": request.model_dump()}
    
    background_tasks.add_task(run_agent_background, job_id, request)
    
    return JobResponse(job_id=job_id, status="pending")

@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = jobs[job_id]
    return JobResponse(job_id=job_id, status=job["status"], result=job.get("result"))
