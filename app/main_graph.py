from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from app.core.state import AgentState
from app.core.vfs import VFS
from app.agents.planner import create_initial_plan
from app.graphs.researcher import create_researcher_graph
from app.graphs.writer import create_writer_graph
from app.core.llm import get_writer_model

# --- SUBGRAPH WRAPPERS ---

def call_researcher(state: AgentState):
    """Bridge to Researcher Subgraph"""
    task = state["plan"][state["current_task_index"]]
    
    # Pass dict instead of VFS object
    research_input = {
        "query": task["description"],
        "vfs_data": state.get("vfs_data", {}),
        "search_results": [],
        "selected_urls": [],
        "summaries": []
    }
    
    research_graph = create_researcher_graph()
    result = research_graph.invoke(research_input)
    
    return {
        "vfs_data": result.get("vfs_data", {}),
        "plan": [
            t if i != state["current_task_index"] else {**t, "status": "completed"}
            for i, t in enumerate(state["plan"])
        ],
        "current_task_index": state["current_task_index"] + 1
    }

def call_writer(state: AgentState):
    """Bridge to Writer Subgraph"""
    task = state["plan"][state["current_task_index"]]
    
    writer_input = {
        "task_description": task["description"],
        "vfs_data": state.get("vfs_data", {}),
        "draft_file": "draft.md",
        "context": ""
    }
    
    writer_graph = create_writer_graph()
    result = writer_graph.invoke(writer_input)
    
    return {
        "vfs_data": result.get("vfs_data", {}),
        "plan": [
            t if i != state["current_task_index"] else {**t, "status": "completed"}
            for i, t in enumerate(state["plan"])
        ],
        "current_task_index": state["current_task_index"] + 1
    }

def finalize_article(state: AgentState):
    """Generates SEO metadata and finalizes the article."""
    print("--- Finalizing Article ---")
    vfs = VFS()
    vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()}
    
    if not vfs.exists("draft.md"):
        return {}
        
    draft = vfs.read_file("draft.md")
    llm = get_writer_model()
    
    prompt = f"""
    Analyze the following article draft and generate SEO metadata.
    
    Draft:
    {draft[:5000]}... (truncated)
    
    Requirements:
    1. Title Tag (max 60 chars)
    2. Meta Description (max 160 chars)
    3. Primary Keyword used
    
    Format output as Markdown frontmatter or a simple block.
    """
    
    try:
        response = llm.invoke(prompt)
        metadata = response.content
        
        # Prepend to draft
        final_content = f"{metadata}\n\n{draft}"
        vfs.write_file("final_article.md", final_content)
    except Exception as e:
        print(f"Finalization failed: {e}")
    
    return {"vfs_data": vfs._files}


def planner_node(state: AgentState):
    return create_initial_plan(state)

def router(state: AgentState):
    """Decides next step"""
    if not state.get("plan"):
        return "planner"
        
    if state["current_task_index"] >= len(state["plan"]):
        return "finalize"
        
    current_task = state["plan"][state["current_task_index"]]
    if current_task["type"] == "research":
        return "researcher"
    elif current_task["type"] == "write":
        return "writer"
    
    return "finalize"

# --- MAIN GRAPH ---

def create_main_graph(checkpointer: Optional[BaseCheckpointSaver] = None):
    workflow = StateGraph(AgentState)
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", call_researcher)
    workflow.add_node("writer", call_writer)
    workflow.add_node("finalize", finalize_article)
    
    workflow.set_entry_point("planner")
    
    workflow.add_conditional_edges(
        "planner",
        router,
        {
            "researcher": "researcher",
            "writer": "writer",
            "finalize": "finalize"
        }
    )
    
    workflow.add_conditional_edges(
        "researcher",
        router,
        {
            "researcher": "researcher",
            "writer": "writer",
            "finalize": "finalize"
        }
    )
    
    workflow.add_conditional_edges(
        "writer",
        router,
        {
            "researcher": "researcher",
            "writer": "writer",
            "finalize": "finalize"
        }
    )
    
    workflow.add_edge("finalize", END)
    
    return workflow.compile(checkpointer=checkpointer)
