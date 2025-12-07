from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from app.core.vfs import VFS
from app.core.llm import get_writer_model

# Use dict for vfs_data instead of VFS object
class WriterState(TypedDict):
    task_description: str
    vfs_data: dict
    draft_file: str # Filename of the draft

def gather_context_node(state: WriterState):
    """Reads relevant files from VFS."""
    vfs = VFS()
    vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()}
    files = vfs.list_files()
    
    context_text = ""
    for f in files:
        if f.startswith("research/"):
            content = vfs.read_file(f)
            meta = vfs.get_file(f).metadata
            context_text += f"\n--- Source: {meta.get('url', 'unknown')} ---\n{content}\n"
    
    if not context_text:
        context_text = "No research available."
            
    return {"context": context_text} 

class WriterStateInternal(WriterState):
    context: str

def write_node(state: WriterStateInternal):
    """Generates the text."""
    llm = get_writer_model()
    
    vfs = VFS()
    vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()}
    
    current_draft = ""
    if vfs.exists(state["draft_file"]):
        current_draft = vfs.read_file(state["draft_file"])
    
    draft_tail = current_draft[-2000:] if current_draft else "(Start of Article)"
    
    prompt = f"""
    You are an expert SEO Article Writer.
    
    Task: {state['task_description']}
    
    Here is the research context:
    {state['context']}
    
    Current Draft (End):
    {draft_tail}
    
    Instructions:
    - Write ONLY the actual article content for this section.
    - DO NOT chat ("Sure, here is the text..."). Just write the text.
    - Use Markdown formatting (H2, H3, bold, bullet points).
    - If this is the intro, include the primary keywords naturally.
    - Do not repeat what has already been written.
    - Add internal link placeholders like [Internal Link: Anchor Text -> Topic] where relevant.
    """
    
    print(f"  [Writer] Writing section: {state['task_description']}...")
    try:
        response = llm.invoke(prompt)
        new_content = response.content
        
        # Post-processing to remove chatty prefix if present (naive)
        if new_content.strip().lower().startswith("here is"):
            new_content = new_content.split("\n", 1)[-1]
        
        # Append to draft
        full_content = current_draft + "\n\n" + new_content
        vfs.write_file(state["draft_file"], full_content)
    except Exception as e:
        print(f"  [Writer] Failed: {e}")
    
    return {"vfs_data": vfs._files}

def create_writer_graph():
    workflow = StateGraph(WriterStateInternal)
    
    workflow.add_node("gather_context", gather_context_node)
    workflow.add_node("write", write_node)
    
    workflow.set_entry_point("gather_context")
    workflow.add_edge("gather_context", "write")
    workflow.add_edge("write", END)
    
    return workflow.compile()
