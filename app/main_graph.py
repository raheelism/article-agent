from typing import TypedDict
from langgraph.graph import StateGraph, END
from app.core.state import AgentState
from app.core.vfs import VFS
from app.agents.planner import create_initial_plan
from app.graphs.researcher import create_researcher_graph
from app.graphs.writer import create_writer_graph

# --- SUBGRAPH WRAPPERS ---

def call_researcher(state: AgentState):
    """Bridge to Researcher Subgraph"""
    task = state["plan"][state["current_task_index"]]
    
    # Reconstruct VFS from state
    # (In a persistent setup, we'd need better handling, but for now assuming shared memory)
    # vfs = VFS() 
    # vfs._files = state["vfs_data"] -- actually, let's just use the VFS object if we pass it around in memory?
    # LangGraph state is usually JSON-serializable. 
    # We need to serialize/deserialize VFS.
    
    vfs = VFS()
    vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()} # simplified hydration
    
    research_input = {
        "query": task["description"], # Use task description as query? Or params?
        "vfs": vfs,
        "search_results": [],
        "selected_urls": [],
        "summaries": []
    }
    
    # Invoke subgraph
    research_graph = create_researcher_graph()
    research_graph.invoke(research_input)
    
    # Update VFS state back to global
    # (Since VFS writes to its internal dict, we need to extract it back)
    # Note: This is where "Pass by Reference" vs "Pass by Value" gets tricky in LangGraph distributed.
    # For a single process, objects might persist, but let's be explicit.
    
    return {
        "vfs_data": vfs._files, # Save changes
        # Mark task complete
        "plan": [
            t if i != state["current_task_index"] else {**t, "status": "completed"}
            for i, t in enumerate(state["plan"])
        ],
        "current_task_index": state["current_task_index"] + 1
    }

def call_writer(state: AgentState):
    """Bridge to Writer Subgraph"""
    task = state["plan"][state["current_task_index"]]
    
    vfs = VFS()
    vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()}
    
    writer_input = {
        "task_description": task["description"],
        "vfs": vfs,
        "draft_file": "draft.md",
        "context": "" # will be filled
    }
    
    writer_graph = create_writer_graph()
    writer_graph.invoke(writer_input)
    
    return {
        "vfs_data": vfs._files,
        "plan": [
            t if i != state["current_task_index"] else {**t, "status": "completed"}
            for i, t in enumerate(state["plan"])
        ],
        "current_task_index": state["current_task_index"] + 1
    }

def planner_node(state: AgentState):
    return create_initial_plan(state)

def router(state: AgentState):
    """Decides next step"""
    if not state.get("plan"):
        return "planner"
        
    if state["current_task_index"] >= len(state["plan"]):
        return END
        
    current_task = state["plan"][state["current_task_index"]]
    if current_task["type"] == "research":
        return "researcher"
    elif current_task["type"] == "write":
        return "writer"
    
    return END

# --- MAIN GRAPH ---

def create_main_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", call_researcher)
    workflow.add_node("writer", call_writer)
    
    workflow.set_entry_point("planner")
    
    workflow.add_conditional_edges(
        "planner",
        router,
        {
            "researcher": "researcher",
            "writer": "writer",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "researcher",
        router,
        {
            "researcher": "researcher",
            "writer": "writer",
            END: END
        }
    )
    
    workflow.add_conditional_edges(
        "writer",
        router,
        {
            "researcher": "researcher",
            "writer": "writer",
            END: END
        }
    )
    
    return workflow.compile()
