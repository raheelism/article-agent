from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from app.core.vfs import VFS
from app.core.llm import get_writer_model
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Singleton for embedding model to avoid reloading
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        # Use a small, fast model
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

class WriterState(TypedDict):
    task_description: str
    vfs_data: dict
    draft_file: str # Filename of the draft

class WriterStateInternal(WriterState):
    context: str

def retrieve_context_node(state: WriterState):
    """
    RAG Implementation:
    1. Reads research files.
    2. Chunks them.
    3. Embeds them.
    4. Retrieves top K relevant chunks for the current task.
    """
    vfs = VFS()
    vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()}
    files = vfs.list_files()
    
    # 1. Collect all research text
    chunks = []
    
    for f in files:
        if f.startswith("research/"):
            content = vfs.read_file(f)
            meta = vfs.get_file(f).metadata
            source_url = meta.get('url', 'unknown')
            
            # Simple chunking by paragraphs or max char length
            # A more robust approach would use a text splitter, but this suffices for now.
            raw_paragraphs = content.split("\n\n")
            for p in raw_paragraphs:
                p = p.strip()
                if len(p) > 50: # Ignore tiny fragments
                    chunks.append(f"Source: {source_url}\nContent: {p}")
    
    if not chunks:
        return {"context": "No research available."}
        
    # 2. Embed chunks & Task
    try:
        model = get_embedding_model()
        chunk_embeddings = model.encode(chunks)
        task_embedding = model.encode([state['task_description']])
        
        # 3. Build FAISS index
        dimension = chunk_embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array(chunk_embeddings).astype('float32'))
        
        # 4. Search
        k = 4 # Retrieve top 4 chunks (approx 600-1000 tokens)
        D, I = index.search(np.array(task_embedding).astype('float32'), k)
        
        retrieved_indices = I[0]
        relevant_chunks = [chunks[i] for i in retrieved_indices if i >= 0 and i < len(chunks)]
        
        context_text = "\n\n".join(relevant_chunks)
        print(f"  [Writer] Retrieved {len(relevant_chunks)} chunks for context.")
        
    except Exception as e:
        print(f"  [Writer] RAG failed ({e}), falling back to simple truncation.")
        # Fallback: Just take the first 3000 chars of all research
        full_text = "\n".join(chunks)
        context_text = full_text[:3000]

    return {"context": context_text} 


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
    You are a human writer with 10 years of experience. Write like a person, not a machine.
    
    Task: {state['task_description']}
    
    Research Context:
    {state['context']}
    
    Current Draft (End):
    {draft_tail}
    
    ═══════════════════════════════════════════════════════════════
    WRITING RULES - FOLLOW EXACTLY
    ═══════════════════════════════════════════════════════════════
    
    1. OUTPUT ONLY THE ARTICLE CONTENT. No "Sure!" No "Here is..." Just write.
    
    2. USE MARKDOWN: H2 (##), H3 (###), **bold**, bullet points, > blockquotes
    
    3. NEVER USE THESE WORDS (they scream "AI wrote this"):
       ❌ delve, tapestry, landscape, unleash, foster, paramount
       ❌ underscores, game-changer, multifaceted, holistic, leverage
       ❌ synergy, robust, streamline, cutting-edge, revolutionary
       ❌ transformative, comprehensive, facilitate, utilize
       
       USE INSTEAD: dig into, explore, field, release, build, critical, shows, changes everything, complete, use
    
    4. VARY SENTENCE LENGTH (Critical for human voice):
       
       ❌ BAD (robotic): "Sleep is important. It helps recovery. Recovery improves performance. Performance matters for success."
       
       ✅ GOOD (human): "Sleep matters. Not just for rest—for everything. Your brain consolidates memories while you dream, filing the day's chaos into retrievable folders. Skip it, and yesterday's lessons vanish."
       
       Pattern: Short punch. Short punch. Long flowing sentence with texture. Medium closer.
    
    5. ADD SENSORY DETAILS (Show, don't tell):
       
       ❌ BAD: "Stress affects your health negatively."
       ✅ GOOD: "Stress knots your shoulders. Grinds your teeth at 3 AM. Turns coffee into a survival mechanism."
       
       ❌ BAD: "Morning routines increase productivity."
       ✅ GOOD: "The alarm buzzes. Cold water shocks your face awake. By the time the coffee machine gurgles its last drop, you've already cleared three emails."
    
    6. KILL HEDGE WORDS:
       ❌ "It is important to note that..." → Just state it
       ❌ "could potentially" → "can" or "does"
       ❌ "One might argue" → Make the argument directly
       ❌ "It appears that" → State what IS
    
    7. AVOID CONNECTOR SPAM:
       ❌ "Moreover... Furthermore... Additionally... In conclusion..."
       ✅ Just start sentences with subjects. Let ideas flow naturally.
    
    8. USE ACTIVE VOICE:
       ❌ "The study was conducted by researchers"
       ✅ "Researchers conducted the study"
       
       ❌ "Improvements were seen in patients"
       ✅ "Patients improved"
    
    ═══════════════════════════════════════════════════════════════
    EXAMPLE OF EXCELLENT HUMAN WRITING:
    ═══════════════════════════════════════════════════════════════
    
    ## Why Deep Breathing Actually Works
    
    Your nervous system has two modes. Fight-or-flight. Rest-and-digest.
    
    Most of us live in fight-or-flight. Emails ping. Deadlines loom. The amygdala—that ancient alarm system in your brain—stays perpetually triggered, pumping cortisol like a broken faucet.
    
    Deep breathing flips the switch.
    
    When you exhale slowly, the vagus nerve sends a signal: "We're safe." Heart rate drops. Blood pressure eases. The cortisol faucet finally shuts off.
    
    > A 2023 Stanford study found that just 5 minutes of cyclic sighing—inhale, inhale again, long exhale—beat traditional meditation for reducing anxiety.
    
    The technique is stupidly simple:
    
    - **Inhale** through your nose for 4 seconds
    - **Inhale again** to fully expand your lungs
    - **Exhale slowly** through your mouth for 6-8 seconds
    
    That's it. Your shoulders drop. Your jaw unclenches. The world looks slightly less like a dumpster fire.
    
    ═══════════════════════════════════════════════════════════════
    
    Now write your section. No preamble. Just the content.
    """
    
    print(f"  [Writer] Writing section: {state['task_description'][:50]}...")
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
    
    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("write", write_node)
    
    workflow.set_entry_point("retrieve_context")
    workflow.add_edge("retrieve_context", "write")
    workflow.add_edge("write", END)
    
    return workflow.compile()
