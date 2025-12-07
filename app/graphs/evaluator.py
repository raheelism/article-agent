from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, END
from app.core.vfs import VFS
from app.core.llm import (
    get_qwen_model,
    get_kimi_model,
    get_llama_model,
    get_optimizer_model
)

class EvaluatorState(TypedDict):
    draft_file: str
    vfs_data: dict
    critiques: Annotated[List[str], operator.add]

def get_draft(state: EvaluatorState) -> str:
    vfs = VFS()
    vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()}
    if vfs.exists(state["draft_file"]):
        return vfs.read_file(state["draft_file"])
    return ""

def critique_qwen_node(state: EvaluatorState):
    """Critic 1: Qwen - Structure & SEO"""
    draft = get_draft(state)
    if not draft: return {"critiques": ["Qwen: No draft to critique."]}
    
    llm = get_qwen_model()
    prompt = f"""
    You are an expert SEO and Content Structure Critic.
    Analyze the following blog post draft.
    
    Focus on:
    1. HTML Header Structure (H1, H2, H3)
    2. Keyword usage and placement
    3. Internal/External linking opportunities
    4. Formatting (bullet points, readability)
    
    Draft:
    {draft[:8000]}... (truncated if too long)
    
    Provide a structured critique and concrete suggestions for improvement.
    Label your response "CRITIC: QWEN (SEO/STRUCTURE)".
    """
    
    try:
        response = llm.invoke(prompt)
        return {"critiques": [response.content]}
    except Exception as e:
        return {"critiques": [f"Qwen Error: {str(e)}"]}

def critique_kimi_node(state: EvaluatorState):
    """Critic 2: Kimi - Engagement & Tone"""
    draft = get_draft(state)
    if not draft: return {"critiques": ["Kimi: No draft to critique."]}
    
    llm = get_kimi_model()
    prompt = f"""
    You are an expert Content Editor focusing on User Engagement.
    Analyze the following blog post draft.
    
    Focus on:
    1. Tone and Voice (is it human, engaging, appropriate?)
    2. Flow and transitions between sections
    3. Storytelling elements
    4. Hook and Conclusion strength
    
    Draft:
    {draft[:8000]}... (truncated if too long)
    
    Provide a structured critique and concrete suggestions for improvement.
    Label your response "CRITIC: KIMI (ENGAGEMENT)".
    """
    
    try:
        response = llm.invoke(prompt)
        return {"critiques": [response.content]}
    except Exception as e:
        return {"critiques": [f"Kimi Error: {str(e)}"]}

def critique_llama_node(state: EvaluatorState):
    """Critic 3: Llama 4 - Logic & Accuracy"""
    draft = get_draft(state)
    if not draft: return {"critiques": ["Llama: No draft to critique."]}
    
    llm = get_llama_model()
    prompt = f"""
    You are an expert Fact-Checker and Logician.
    Analyze the following blog post draft.
    
    Focus on:
    1. Logical consistency of arguments
    2. Clarity of explanations
    3. Potential factual inaccuracies (based on general knowledge)
    4. Depth of coverage
    
    Draft:
    {draft[:8000]}... (truncated if too long)
    
    Provide a structured critique and concrete suggestions for improvement.
    Label your response "CRITIC: LLAMA (LOGIC)".
    """
    
    try:
        response = llm.invoke(prompt)
        return {"critiques": [response.content]}
    except Exception as e:
        return {"critiques": [f"Llama Error: {str(e)}"]}

def optimize_node(state: EvaluatorState):
    """Optimizer: Rewrites the article based on critiques."""
    draft = get_draft(state)
    if not draft: return {}
    
    critiques_text = "\n\n".join(state["critiques"])
    llm = get_optimizer_model()
    
    prompt = f"""
    You are a Master Editor.
    Your task is to Rewrite and Optimize the following blog post based on the critiques provided by three expert reviewers.
    
    Original Draft:
    {draft}
    
    Critiques:
    {critiques_text}
    
    Instructions:
    1. Read the critiques carefully.
    2. Synthesize the feedback.
    3. REWRITE the article to address the issues raised.
    4. Maintain the Markdown format.
    5. Ensure the final output is a complete, polished article.
    6. Do not include the critiques in the final output, only the improved article content.
    """
    
    print("  [Optimizer] Optimizing draft based on critiques...")
    try:
        response = llm.invoke(prompt)
        new_content = response.content
        
        vfs = VFS()
        vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()}
        vfs.write_file(state["draft_file"], new_content)
        
        return {"vfs_data": vfs._files}
    except Exception as e:
        print(f"  [Optimizer] Failed: {e}")
        return {}

def create_evaluator_graph():
    workflow = StateGraph(EvaluatorState)
    
    workflow.add_node("critique_qwen", critique_qwen_node)
    workflow.add_node("critique_kimi", critique_kimi_node)
    workflow.add_node("critique_llama", critique_llama_node)
    workflow.add_node("optimize", optimize_node)
    
    # We use a dummy setup node to allow parallel branching from the start.
    workflow.add_node("setup", lambda x: {})
    workflow.set_entry_point("setup")
    
    # Fan out to parallel critics
    workflow.add_edge("setup", "critique_qwen")
    workflow.add_edge("setup", "critique_kimi")
    workflow.add_edge("setup", "critique_llama")
    
    # Fan in to optimizer
    workflow.add_edge("critique_qwen", "optimize")
    workflow.add_edge("critique_kimi", "optimize")
    workflow.add_edge("critique_llama", "optimize")
    
    workflow.add_edge("optimize", END)
    
    return workflow.compile()
