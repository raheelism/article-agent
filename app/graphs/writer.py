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
    You are an expert SEO Article Writer.
    
    Task: {state['task_description']}
    
    Here is the RELEVANT research context (retrieved for this specific section):
    {state['context']}
    
    Current Draft (End):
    {draft_tail}
    
    Instructions:
    - Write ONLY the actual article content for this section.
    - DO NOT chat ("Sure, here is the text..."). Just write the text.
    - Use Markdown formatting (H2, H3, bold, bullet points).
    - If this is the intro, include the primary keywords naturally.
    - Do not repeat what has already been written.
    - Integrate facts from the research context naturally.
    - Add internal link placeholders like [Internal Link: Anchor Text -> Topic] where relevant.
    
    ABSOLUTE MODE CONSTRAINTS (MANDATORY):
    1. PROHIBITED WORDS: You are strictly prohibited from using the following words: "delve", "tapestry", "landscape", "unleash", "foster", "paramount", "underscores", "game-changer". If you need these concepts, find concrete synonyms.
    2. BURSTINESS: Do not write sentences of uniform length. You must alternate between short, punchy sentences (under 10 words) and complex, flowing sentences. Create a jagged rhythm.
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
