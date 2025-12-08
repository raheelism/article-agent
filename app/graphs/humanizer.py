from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from app.core.vfs import VFS
from app.core.llm import get_optimizer_model, get_writer_model
import json

class HumanizerState(TypedDict):
    draft_file: str
    vfs_data: dict
    last_critique: Optional[dict]
    iteration_count: int

def get_draft(state: HumanizerState) -> str:
    vfs = VFS()
    vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()}
    if vfs.exists(state["draft_file"]):
        return vfs.read_file(state["draft_file"])
    return ""

def humanization_critic_node(state: HumanizerState):
    """
    Node A: The Linguistic Forensics Critic.
    Scans specifically for AI artifacts (Hedging, Connectors, Nominalization, Sensory Vacuum).
    """
    print("--- Humanization Critic ---")
    draft = get_draft(state)
    if not draft:
        return {"last_critique": {"ai_artifact_score": 0}, "iteration_count": state.get("iteration_count", 0)}

    llm = get_optimizer_model()
    
    prompt = f"""
    Analyze the input draft solely for 'AI Artifacts'. Do not check for factual accuracy.
    
    Draft:
    {draft[:10000]}... (truncated)
    
    Output a structured JSON critique identifying:
    1. Hedging: usage of 'potential,' 'arguably,' 'it is important to note'.
    2. Connective Tissue Syndrome: Overuse of 'Moreover,' 'Furthermore,' 'In conclusion'.
    3. Nominalization: Instances where actions are turned into nouns (e.g., 'made a decision' instead of 'decided').
    4. Sensory Vacuum: Sections that are purely abstract and lack physical/sensory descriptions.
    5. Burstiness Score: A qualitative assessment of sentence length variety (1-10, where 1 is robotic/uniform and 10 is jagged/human).
    6. AI Artifact Score: An overall score from 1-10 indicating how "AI-like" the text is (10 = very robotic, 1 = very human).
    
    Return ONLY valid JSON in the following format:
    {{
        "hedging_issues": ["example1", ...],
        "connector_issues": ["example1", ...],
        "nominalization_issues": ["example1", ...],
        "sensory_vacuum_issues": ["section description", ...],
        "burstiness_score": 5,
        "ai_artifact_score": 8,
        "general_feedback": "..."
    }}
    """
    
    try:
        response = llm.invoke(prompt)
        content = response.content
        # Basic JSON extraction if wrapped in code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        critique = json.loads(content.strip())
        print(f"  [Humanizer] AI Artifact Score: {critique.get('ai_artifact_score')}")
        return {
            "last_critique": critique, 
            "iteration_count": state.get("iteration_count", 0)
        }
    except Exception as e:
        print(f"  [Humanizer] Critic Error: {e}")
        # Return a dummy critique to avoid crashing, assuming score 0 to exit loop
        return {
            "last_critique": {"ai_artifact_score": 0, "general_feedback": "Error in critic"}, 
            "iteration_count": state.get("iteration_count", 0)
        }

def refiner_node(state: HumanizerState):
    """
    Node B: The Refiner Agent.
    Rewrites specific sections using Chain of Density (CoD) and sensory injection.
    """
    print("--- Refiner Agent ---")
    draft = get_draft(state)
    critique = state.get("last_critique", {})
    
    if not draft or not critique:
        return {}

    llm = get_optimizer_model() # Using high quality model for rewriting
    
    prompt = f"""
    Role: You are a Refiner Agent. Your goal is NOT to be polite or helpful. Your goal is to obliterate the "Machine Voice."
    
    Input Draft:
    {draft}
    
    Critique of AI Artifacts:
    {json.dumps(critique, indent=2)}
    
    Directives:
    1. Kill the Hedges: Change "This could potentially suggest..." to "This suggests..." Eliminate "It appears that." Be authoritative.
    2. Prune Connectors: Remove at least 80% of transition words like "Moreover," "Additionally," and "However." Rely on the semantic flow of ideas instead.
    3. Lexical Purge: If the draft contains "delve," "tapestry," or "game-changer," replace them with specific, low-frequency vocabulary.
    4. Inject Sensory Detail: The current text is abstract. Add specific visual or tactile details to the examples. Show, don't just tell.
    5. Variable Sentence Structure: Ensure the output has high "burstiness." Mix fragments with long compound sentences.
    6. Denominalization: Convert nominalizations (words ending in -tion, -ment) back into active verbs.
    
    Output:
    The completely rewritten article. Do not output anything else. Maintain Markdown formatting.
    """
    
    try:
        response = llm.invoke(prompt)
        new_content = response.content
        
        # Strip potential chat prefixes
        if new_content.strip().lower().startswith("here is"):
            new_content = new_content.split("\n", 1)[-1]
            
        vfs = VFS()
        vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()}
        vfs.write_file(state["draft_file"], new_content)
        
        return {
            "vfs_data": vfs._files, 
            "iteration_count": state["iteration_count"] + 1
        }
    except Exception as e:
        print(f"  [Humanizer] Refiner Error: {e}")
        return {"iteration_count": state["iteration_count"] + 1}

def should_continue(state: HumanizerState):
    """
    Determines if we should loop back to the critic or exit.
    """
    critique = state.get("last_critique", {})
    iteration_count = state.get("iteration_count", 0)
    threshold = 3 # If score > 3 (1 is human, 10 is robot), we continue
    
    score = critique.get("ai_artifact_score", 0)
    
    print(f"  [Humanizer] Check: Score={score}, Iteration={iteration_count}")
    
    if score > threshold and iteration_count < 3:
        return "humanization_critic"
    return END

def create_humanizer_graph():
    workflow = StateGraph(HumanizerState)
    
    workflow.add_node("humanization_critic", humanization_critic_node)
    workflow.add_node("refiner", refiner_node)
    
    workflow.set_entry_point("humanization_critic")
    
    workflow.add_edge("humanization_critic", "refiner")
    
    workflow.add_conditional_edges(
        "refiner",
        should_continue,
        {
            "humanization_critic": "humanization_critic",
            END: END
        }
    )
    
    return workflow.compile()
