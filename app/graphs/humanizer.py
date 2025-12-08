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
    You are a Linguistic Forensics Expert. Analyze the draft for 'AI Artifacts' - patterns that reveal machine authorship.
    
    Draft:
    {draft[:10000]}... (truncated)
    
    DETECTION CATEGORIES:
    
    1. HEDGING LANGUAGE (Weak, non-committal phrasing)
       BAD: "It is important to note that exercise could potentially help with..."
       BAD: "This arguably suggests that there may be benefits..."
       BAD: "One might consider the possibility that..."
       GOOD: "Exercise helps." "This suggests benefits." "Consider this:"
    
    2. CONNECTOR OVERLOAD (Robotic transition words)
       BAD: "Moreover, the study shows... Furthermore, experts believe... Additionally, research indicates... In conclusion..."
       GOOD: Let ideas flow naturally. Use whitespace. Start sentences with subjects, not connectors.
    
    3. NOMINALIZATION (Verbs turned into clunky nouns)
       BAD: "The implementation of the system" → GOOD: "We implemented the system"
       BAD: "The utilization of resources" → GOOD: "We used resources"
       BAD: "Made a decision" → GOOD: "Decided"
       BAD: "Conducted an investigation" → GOOD: "Investigated"
       BAD: "Achieved optimization" → GOOD: "Optimized"
    
    4. SENSORY VACUUM (Abstract without physical grounding)
       BAD: "Productivity increases when employees feel valued."
       GOOD: "The office hums with keyboard clicks. Coffee cups empty faster. Deadlines whoosh past."
       BAD: "Stress affects mental health negatively."
       GOOD: "Your shoulders clench. The jaw tightens. Sleep fragments into 3 AM ceiling-staring."
    
    5. UNIFORM SENTENCE LENGTH (Robotic rhythm)
       BAD: "The study shows results. The results are positive. The positive results matter. This matters greatly."
       GOOD: "Results landed. Positive ones. The kind that make researchers high-five in sterile labs and email colleagues at midnight with all-caps subject lines."
    
    6. AI VOCABULARY (Overused LLM words)
       FLAGGED WORDS: "delve", "tapestry", "landscape", "unleash", "foster", "paramount", 
       "underscores", "game-changer", "multifaceted", "holistic", "leverage", "synergy",
       "robust", "streamline", "cutting-edge", "revolutionary", "transformative"
    
    Return ONLY valid JSON:
    {{
        "hedging_issues": ["exact quote from text", ...],
        "connector_issues": ["exact quote from text", ...],
        "nominalization_issues": ["exact quote from text", ...],
        "sensory_vacuum_issues": ["description of abstract section needing sensory detail", ...],
        "ai_vocabulary_found": ["flagged words found", ...],
        "burstiness_score": 5,
        "ai_artifact_score": 8,
        "worst_paragraph": "paste the most robotic paragraph here",
        "general_feedback": "specific actionable feedback"
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
    You are a Ruthless Human Voice Editor. Your ONLY job: make this text sound like a skilled human wrote it, not a machine.
    
    Input Draft:
    {draft}
    
    Detected AI Artifacts:
    {json.dumps(critique, indent=2)}
    
    TRANSFORMATION RULES WITH EXAMPLES:
    
    ═══════════════════════════════════════════════════════════════
    RULE 1: KILL HEDGING - Be direct and authoritative
    ═══════════════════════════════════════════════════════════════
    BEFORE: "It is important to note that meditation could potentially help reduce stress levels."
    AFTER:  "Meditation cuts stress. Studies confirm it."
    
    BEFORE: "One might argue that sleep plays a crucial role in cognitive function."
    AFTER:  "Sleep fuels the brain. Skip it, and your thinking turns to sludge."
    
    BEFORE: "This arguably demonstrates the significance of proper nutrition."
    AFTER:  "Eat garbage, feel like garbage. Simple math."
    
    ═══════════════════════════════════════════════════════════════
    RULE 2: MURDER CONNECTORS - Let ideas breathe
    ═══════════════════════════════════════════════════════════════
    BEFORE: "Moreover, research indicates that exercise improves mood. Furthermore, it enhances cognitive function. Additionally, it promotes better sleep. In conclusion, exercise is beneficial."
    AFTER:  "Exercise lifts mood. Sharpens thinking. Deepens sleep. Three wins from one habit."
    
    DELETE: Moreover, Furthermore, Additionally, However, Nevertheless, In conclusion, It is worth noting, Consequently
    
    ═══════════════════════════════════════════════════════════════
    RULE 3: INJECT SENSORY DETAILS - Make readers feel it
    ═══════════════════════════════════════════════════════════════
    BEFORE: "Stress negatively impacts productivity and well-being."
    AFTER:  "Stress tightens your shoulders into rocks. Your inbox blurs. Coffee tastes like battery acid. Deadlines pile up like unpaid bills."
    
    BEFORE: "Morning routines improve daily performance."
    AFTER:  "The alarm screams at 6 AM. Cold water hits your face. The coffee machine gurgles. By 7, you're two emails ahead of yesterday's you."
    
    ═══════════════════════════════════════════════════════════════
    RULE 4: VARY SENTENCE LENGTH - Create rhythm
    ═══════════════════════════════════════════════════════════════
    BEFORE: "The brain requires adequate rest. Sleep deprivation causes cognitive decline. Memory consolidation happens during sleep. Therefore sleep is essential."
    AFTER:  "Your brain needs rest. Not optional. During sleep, memories cement themselves into neural pathways—the day's chaos finally making sense. Skip this, and yesterday's lessons evaporate like morning fog."
    
    Pattern: Short. Short. Long with texture. Medium with punch.
    
    ═══════════════════════════════════════════════════════════════
    RULE 5: DENOMINALIZE - Verbs beat nouns
    ═══════════════════════════════════════════════════════════════
    BEFORE: "The implementation of the new system resulted in optimization of workflow."
    AFTER:  "We implemented the new system. Workflow sped up."
    
    BEFORE: "The utilization of meditation techniques leads to the reduction of anxiety."
    AFTER:  "Meditate. Anxiety drops."
    
    ═══════════════════════════════════════════════════════════════
    RULE 6: PURGE AI VOCABULARY - Replace with specific words
    ═══════════════════════════════════════════════════════════════
    "delve into" → "dig into" / "explore" / "examine"
    "tapestry" → (just remove it, use specific imagery instead)
    "landscape" → "field" / "space" / "world" / (be specific: "the startup scene")
    "unleash" → "release" / "trigger" / "spark"
    "foster" → "build" / "grow" / "encourage"
    "paramount" → "critical" / "essential" / "the priority"
    "game-changer" → (describe what actually changed)
    "leverage" → "use" / "apply"
    "robust" → "strong" / "solid" / "reliable"
    "holistic" → "complete" / "full" / "whole"
    
    ═══════════════════════════════════════════════════════════════
    
    OUTPUT: The completely rewritten article. No preamble. No "Here is the revised..."
    Just the article in Markdown format.
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
