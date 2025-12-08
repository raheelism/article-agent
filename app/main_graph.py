from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from app.core.state import AgentState
from app.core.vfs import VFS
from app.agents.planner import create_initial_plan
from app.graphs.researcher import create_researcher_graph
from app.graphs.writer import create_writer_graph
from app.graphs.evaluator import create_evaluator_graph
from app.graphs.humanizer import create_humanizer_graph
from app.graphs.faq import create_faq_graph
from app.graphs.keyword_analyzer import create_keyword_analyzer_graph
from app.graphs.linking import create_linking_graph
from app.core.llm import get_writer_model
import concurrent.futures

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

def call_evaluator(state: AgentState):
    """Bridge to Evaluator Subgraph"""
    print("--- Evaluating Article ---")
    evaluator_input = {
        "draft_file": "draft.md",
        "vfs_data": state.get("vfs_data", {}),
        "critiques": []
    }
    
    evaluator_graph = create_evaluator_graph()
    result = evaluator_graph.invoke(evaluator_input)
    
    return {
        "vfs_data": result.get("vfs_data", {})
    }

def call_humanizer(state: AgentState):
    """Bridge to Humanizer Subgraph"""
    print("--- Humanizing Article ---")
    humanizer_input = {
        "draft_file": "draft.md",
        "vfs_data": state.get("vfs_data", {}),
        "last_critique": None,
        "iteration_count": 0
    }
    
    humanizer_graph = create_humanizer_graph()
    result = humanizer_graph.invoke(humanizer_input)
    
    return {
        "vfs_data": result.get("vfs_data", {})
    }


def call_seo_analysis(state: AgentState):
    """
    Runs FAQ, Keyword Analysis, and Linking agents in PARALLEL.
    This is the SEO analysis phase before final article generation.
    """
    print("--- Running SEO Analysis (FAQ + Keywords + Linking) ---")
    
    vfs_data = state.get("vfs_data", {})
    topic = state.get("topic", "")
    
    # Prepare inputs for each agent
    faq_input = {
        "vfs_data": vfs_data,
        "draft_file": "draft.md",
        "faqs": []
    }
    
    keyword_input = {
        "vfs_data": vfs_data,
        "draft_file": "draft.md",
        "topic": topic,
        "keyword_report": {}
    }
    
    linking_input = {
        "vfs_data": vfs_data,
        "draft_file": "draft.md",
        "topic": topic,
        "linking_report": {}
    }
    
    # Run all three agents in parallel using ThreadPoolExecutor
    faq_result = {}
    keyword_result = {}
    linking_result = {}
    
    def run_faq():
        graph = create_faq_graph()
        return graph.invoke(faq_input)
    
    def run_keywords():
        graph = create_keyword_analyzer_graph()
        return graph.invoke(keyword_input)
    
    def run_linking():
        graph = create_linking_graph()
        return graph.invoke(linking_input)
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_faq = executor.submit(run_faq)
            future_keywords = executor.submit(run_keywords)
            future_linking = executor.submit(run_linking)
            
            # Collect results
            try:
                faq_result = future_faq.result(timeout=120)
            except Exception as e:
                print(f"  [SEO] FAQ generation failed: {e}")
                faq_result = {"faqs": []}
            
            try:
                keyword_result = future_keywords.result(timeout=120)
            except Exception as e:
                print(f"  [SEO] Keyword analysis failed: {e}")
                keyword_result = {"keyword_report": {}}
            
            try:
                linking_result = future_linking.result(timeout=120)
            except Exception as e:
                print(f"  [SEO] Linking suggestions failed: {e}")
                linking_result = {"linking_report": {}}
    
    except Exception as e:
        print(f"  [SEO] Parallel execution failed: {e}. Running sequentially...")
        # Fallback to sequential execution
        try:
            faq_result = run_faq()
        except:
            faq_result = {"faqs": []}
        try:
            keyword_result = run_keywords()
        except:
            keyword_result = {"keyword_report": {}}
        try:
            linking_result = run_linking()
        except:
            linking_result = {"linking_report": {}}
    
    # Merge VFS data from all results (linking has the most complete)
    merged_vfs = {**vfs_data}
    if faq_result.get("vfs_data"):
        merged_vfs.update(faq_result["vfs_data"])
    if keyword_result.get("vfs_data"):
        merged_vfs.update(keyword_result["vfs_data"])
    if linking_result.get("vfs_data"):
        merged_vfs.update(linking_result["vfs_data"])
    
    print(f"  [SEO] Analysis complete: {len(faq_result.get('faqs', []))} FAQs, keywords extracted, links suggested")
    
    return {
        "vfs_data": merged_vfs,
        "faqs": faq_result.get("faqs", []),
        "keyword_report": keyword_result.get("keyword_report", {}),
        "linking_report": linking_result.get("linking_report", {})
    }

def finalize_article(state: AgentState):
    """
    Generates SEO metadata and finalizes the article.
    Includes: FAQ section, keyword report, and linking suggestions.
    """
    print("--- Finalizing Article ---")
    vfs = VFS()
    vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()}
    
    if not vfs.exists("draft.md"):
        return {}
        
    draft = vfs.read_file("draft.md")
    llm = get_writer_model()
    
    # Get SEO analysis results
    faqs = state.get("faqs", [])
    keyword_report = state.get("keyword_report", {})
    linking_report = state.get("linking_report", {})
    
    # Generate SEO metadata
    prompt = f"""
    Analyze the following article draft and generate SEO metadata.
    
    Draft:
    {draft[:5000]}... (truncated)
    
    Primary Keyword: {keyword_report.get('primary_keyword', 'N/A')}
    
    Requirements:
    1. Title Tag (max 60 chars, include primary keyword)
    2. Meta Description (max 160 chars, compelling and includes primary keyword)
    3. Primary Keyword confirmation
    
    Format output as Markdown frontmatter:
    ---
    title: "Your Title Here"
    meta_description: "Your description here"
    primary_keyword: "keyword"
    ---
    """
    
    try:
        response = llm.invoke(prompt)
        metadata = response.content
    except Exception as e:
        print(f"Metadata generation failed: {e}")
        metadata = f"""---
title: "{state.get('topic', 'Article')}"
meta_description: "Learn about {state.get('topic', 'this topic')} in this comprehensive guide."
primary_keyword: "{keyword_report.get('primary_keyword', state.get('topic', ''))}"
---"""
    
    # Build final article with all sections
    final_parts = [metadata, "\n\n", draft]
    
    # Add FAQ section
    if faqs:
        faq_section = "\n\n---\n\n## ❓ Frequently Asked Questions\n\n"
        for faq in faqs:
            question = faq.get("question", "")
            answer = faq.get("answer", "")
            faq_section += f"### {question}\n\n{answer}\n\n"
        final_parts.append(faq_section)
    
    # Add structured data appendix (for programmatic access)
    appendix = "\n\n---\n\n## 📊 SEO Analysis Report\n\n"
    
    # Keyword Report
    if keyword_report:
        appendix += "### Keywords\n\n"
        appendix += f"**Primary Keyword:** `{keyword_report.get('primary_keyword', 'N/A')}`\n\n"
        
        if keyword_report.get('secondary_keywords'):
            appendix += "**Secondary Keywords:**\n"
            for kw in keyword_report.get('secondary_keywords', []):
                appendix += f"- {kw}\n"
            appendix += "\n"
        
        if keyword_report.get('lsi_keywords'):
            appendix += "**LSI Keywords:**\n"
            for kw in keyword_report.get('lsi_keywords', []):
                appendix += f"- {kw}\n"
            appendix += "\n"
        
        if keyword_report.get('keyword_density'):
            appendix += "**Keyword Density:**\n\n"
            appendix += "| Keyword | Density |\n|---------|--------|\n"
            for kw, density in keyword_report.get('keyword_density', {}).items():
                appendix += f"| {kw} | {density}% |\n"
            appendix += "\n"
        
        if keyword_report.get('recommendations'):
            appendix += "**SEO Recommendations:**\n"
            for rec in keyword_report.get('recommendations', []):
                appendix += f"- {rec}\n"
            appendix += "\n"
    
    # Linking Report
    if linking_report:
        appendix += "### 🔗 Linking Strategy\n\n"
        
        internal_links = linking_report.get('internal_links', [])
        if internal_links:
            appendix += "**Internal Links (3-5):**\n\n"
            appendix += "| Anchor Text | Target Page | Context |\n|-------------|-------------|----------|\n"
            for link in internal_links:
                appendix += f"| {link.get('anchor_text', '')} | {link.get('suggested_target', '')} | {link.get('context', '')} |\n"
            appendix += "\n"
        
        external_links = linking_report.get('external_links', [])
        if external_links:
            appendix += "**External Links (Authoritative Sources):**\n\n"
            appendix += "| Source | Anchor Text | Placement |\n|--------|-------------|----------|\n"
            for link in external_links:
                appendix += f"| {link.get('source_name', '')} | {link.get('anchor_text', '')} | {link.get('placement_context', '')} |\n"
            appendix += "\n"
    
    final_parts.append(appendix)
    
    # Combine all parts
    final_content = "".join(final_parts)
    vfs.write_file("final_article.md", final_content)
    
    print(f"  [Finalize] Article complete with FAQ ({len(faqs)} items), keywords, and linking strategy")
    
    return {"vfs_data": vfs._files}


def planner_node(state: AgentState):
    return create_initial_plan(state)

def router(state: AgentState):
    """Decides next step"""
    if not state.get("plan"):
        return "planner"
        
    if state["current_task_index"] >= len(state["plan"]):
        return "evaluator"
        
    current_task = state["plan"][state["current_task_index"]]
    if current_task["type"] == "research":
        return "researcher"
    elif current_task["type"] == "write":
        return "writer"
    
    return "evaluator"

# --- MAIN GRAPH ---

def create_main_graph(checkpointer: Optional[BaseCheckpointSaver] = None):
    workflow = StateGraph(AgentState)
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", call_researcher)
    workflow.add_node("writer", call_writer)
    workflow.add_node("evaluator", call_evaluator)
    workflow.add_node("humanizer", call_humanizer)
    workflow.add_node("seo_analysis", call_seo_analysis)  # NEW: Parallel FAQ + Keywords + Linking
    workflow.add_node("finalize", finalize_article)
    
    workflow.set_entry_point("planner")
    
    workflow.add_conditional_edges(
        "planner",
        router,
        {
            "researcher": "researcher",
            "writer": "writer",
            "evaluator": "evaluator"
        }
    )
    
    workflow.add_conditional_edges(
        "researcher",
        router,
        {
            "researcher": "researcher",
            "writer": "writer",
            "evaluator": "evaluator"
        }
    )
    
    workflow.add_conditional_edges(
        "writer",
        router,
        {
            "researcher": "researcher",
            "writer": "writer",
            "evaluator": "evaluator"
        }
    )

    workflow.add_edge("evaluator", "humanizer")
    workflow.add_edge("humanizer", "seo_analysis")  # After humanization -> run SEO analysis
    workflow.add_edge("seo_analysis", "finalize")   # Then finalize with all data
    
    workflow.add_edge("finalize", END)
    
    return workflow.compile(checkpointer=checkpointer)
