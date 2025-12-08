"""
FAQ Generation Agent

Generates FAQ section from research data and article content.
Extracts common questions from search snippets and creates Q&A pairs.
"""

from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from app.core.vfs import VFS
from app.core.llm import get_writer_model
import json
import re


class FAQState(TypedDict):
    vfs_data: dict
    draft_file: str
    faqs: List[Dict[str, str]]  # List of {"question": "...", "answer": "..."}


class FAQItem(TypedDict):
    question: str
    answer: str


def extract_questions_node(state: FAQState) -> dict:
    """
    Extracts potential FAQ questions from:
    1. Research summaries (common themes)
    2. Search snippets (what people are asking)
    3. Article content (topics covered)
    """
    vfs = VFS()
    vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()}
    
    # Collect all research content
    research_content = []
    for filename in vfs.list_files():
        if filename.startswith("research/"):
            content = vfs.read_file(filename)
            research_content.append(content)
    
    # Get the draft
    draft = ""
    if vfs.exists(state["draft_file"]):
        draft = vfs.read_file(state["draft_file"])
    
    llm = get_writer_model()
    
    prompt = f"""
    You are an FAQ generator. Analyze the research and article below, then generate 5-7 frequently asked questions with concise answers.
    
    RESEARCH SUMMARIES:
    {chr(10).join(research_content[:3])[:4000]}
    
    ARTICLE DRAFT (excerpt):
    {draft[:3000]}
    
    RULES:
    1. Questions should be what real users would search for
    2. Answers should be 2-3 sentences, factual, and helpful
    3. Cover different aspects of the topic
    4. Include "how", "what", "why", "when" style questions
    5. Make answers conversational, not robotic
    
    Return ONLY valid JSON array. No markdown, no explanation.
    
    Format:
    [
        {{"question": "What is X?", "answer": "X is... It helps with..."}},
        {{"question": "How do I use X?", "answer": "You can use X by..."}}
    ]
    """
    
    print("  [FAQ] Generating FAQ section...")
    
    try:
        response = llm.invoke(prompt)
        content = response.content
        
        # Clean markdown if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        faqs = json.loads(content.strip())
        
        # Validate structure
        validated_faqs = []
        for faq in faqs:
            if isinstance(faq, dict) and "question" in faq and "answer" in faq:
                validated_faqs.append({
                    "question": str(faq["question"]),
                    "answer": str(faq["answer"])
                })
        
        print(f"  [FAQ] Generated {len(validated_faqs)} FAQ items")
        return {"faqs": validated_faqs}
        
    except Exception as e:
        print(f"  [FAQ] Generation failed: {e}")
        # Return fallback FAQs
        return {"faqs": [
            {"question": "What are the main benefits?", "answer": "The main benefits include improved efficiency, better outcomes, and time savings."},
            {"question": "How do I get started?", "answer": "Start by understanding the basics, then gradually implement the key concepts discussed in this article."},
            {"question": "Is this suitable for beginners?", "answer": "Yes, the concepts covered are accessible to beginners while also providing value for experienced practitioners."}
        ]}


def format_faq_node(state: FAQState) -> dict:
    """
    Formats FAQs as structured data and markdown for the article.
    """
    faqs = state.get("faqs", [])
    
    if not faqs:
        return {"faqs": []}
    
    # Create markdown section
    faq_markdown = "\n\n---\n\n## Frequently Asked Questions\n\n"
    
    for i, faq in enumerate(faqs, 1):
        question = faq.get("question", "")
        answer = faq.get("answer", "")
        faq_markdown += f"### {question}\n\n{answer}\n\n"
    
    # Save to VFS for inclusion in final article
    vfs = VFS()
    vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()}
    vfs.write_file("faq_section.md", faq_markdown)
    
    print(f"  [FAQ] Formatted {len(faqs)} FAQ items")
    
    return {
        "faqs": faqs,
        "vfs_data": vfs._files
    }


def create_faq_graph():
    """Creates the FAQ generation subgraph."""
    workflow = StateGraph(FAQState)
    
    workflow.add_node("extract_questions", extract_questions_node)
    workflow.add_node("format_faq", format_faq_node)
    
    workflow.set_entry_point("extract_questions")
    workflow.add_edge("extract_questions", "format_faq")
    workflow.add_edge("format_faq", END)
    
    return workflow.compile()
