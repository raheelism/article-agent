"""
Keyword Analysis Agent

Extracts and analyzes keywords from the article:
- Primary keyword (main topic)
- Secondary keywords (supporting terms)
- LSI keywords (semantically related)
- Keyword density analysis
"""

from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from app.core.vfs import VFS
from app.core.llm import get_researcher_model
import json
import re
from collections import Counter


class KeywordState(TypedDict):
    vfs_data: dict
    draft_file: str
    topic: str
    keyword_report: Dict  # Structured keyword analysis


class KeywordReport(TypedDict):
    primary_keyword: str
    secondary_keywords: List[str]
    lsi_keywords: List[str]
    keyword_density: Dict[str, float]
    recommendations: List[str]


def extract_keywords_node(state: KeywordState) -> dict:
    """
    Uses LLM to identify primary, secondary, and LSI keywords.
    """
    vfs = VFS()
    vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()}
    
    draft = ""
    if vfs.exists(state["draft_file"]):
        draft = vfs.read_file(state["draft_file"])
    
    topic = state.get("topic", "")
    
    llm = get_researcher_model()
    
    prompt = f"""
    You are an SEO keyword analyst. Analyze the article below and extract keywords.
    
    TOPIC: {topic}
    
    ARTICLE:
    {draft[:6000]}
    
    Extract:
    1. PRIMARY KEYWORD: The main keyword the article should rank for (2-4 words)
    2. SECONDARY KEYWORDS: 5-7 supporting keywords that reinforce the topic
    3. LSI KEYWORDS: 5-7 semantically related terms (Latent Semantic Indexing)
    
    Return ONLY valid JSON. No markdown, no explanation.
    
    Format:
    {{
        "primary_keyword": "main keyword phrase",
        "secondary_keywords": ["keyword 1", "keyword 2", "keyword 3"],
        "lsi_keywords": ["related term 1", "related term 2", "related term 3"]
    }}
    """
    
    print("  [Keywords] Extracting keywords...")
    
    try:
        response = llm.invoke(prompt)
        content = response.content
        
        # Clean markdown if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        keywords = json.loads(content.strip())
        
        return {
            "keyword_report": {
                "primary_keyword": keywords.get("primary_keyword", topic),
                "secondary_keywords": keywords.get("secondary_keywords", []),
                "lsi_keywords": keywords.get("lsi_keywords", []),
                "keyword_density": {},
                "recommendations": []
            }
        }
        
    except Exception as e:
        print(f"  [Keywords] Extraction failed: {e}")
        return {
            "keyword_report": {
                "primary_keyword": topic,
                "secondary_keywords": [],
                "lsi_keywords": [],
                "keyword_density": {},
                "recommendations": ["Unable to extract keywords automatically"]
            }
        }


def analyze_density_node(state: KeywordState) -> dict:
    """
    Calculates keyword density and provides SEO recommendations.
    """
    vfs = VFS()
    vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()}
    
    draft = ""
    if vfs.exists(state["draft_file"]):
        draft = vfs.read_file(state["draft_file"])
    
    report = state.get("keyword_report", {})
    primary = report.get("primary_keyword", "").lower()
    secondary = [kw.lower() for kw in report.get("secondary_keywords", [])]
    
    # Simple word count
    words = re.findall(r'\b\w+\b', draft.lower())
    total_words = len(words)
    
    if total_words == 0:
        return {"keyword_report": report}
    
    # Calculate densities
    density = {}
    recommendations = []
    
    # Primary keyword density
    if primary:
        # Count phrase occurrences
        primary_count = draft.lower().count(primary)
        primary_density = (primary_count * len(primary.split()) / total_words) * 100
        density[primary] = round(primary_density, 2)
        
        # SEO recommendations
        if primary_density < 0.5:
            recommendations.append(f"⚠️ Primary keyword '{primary}' density is low ({primary_density:.1f}%). Aim for 1-2%.")
        elif primary_density > 3:
            recommendations.append(f"⚠️ Primary keyword '{primary}' may be over-optimized ({primary_density:.1f}%). Reduce to 1-2%.")
        else:
            recommendations.append(f"✅ Primary keyword '{primary}' density is optimal ({primary_density:.1f}%).")
    
    # Secondary keywords density
    for kw in secondary[:5]:
        kw_count = draft.lower().count(kw)
        kw_density = (kw_count * len(kw.split()) / total_words) * 100
        density[kw] = round(kw_density, 2)
    
    # Check title/H1 for primary keyword
    if primary and primary not in draft[:500].lower():
        recommendations.append(f"⚠️ Primary keyword not found in introduction. Add it to the first paragraph.")
    
    # Check headings
    h2_pattern = r'^##\s+(.+)$'
    headings = re.findall(h2_pattern, draft, re.MULTILINE)
    heading_has_keyword = any(primary in h.lower() for h in headings) if primary else False
    
    if not heading_has_keyword and primary:
        recommendations.append(f"💡 Consider adding primary keyword to at least one H2 heading.")
    
    # Update report
    report["keyword_density"] = density
    report["recommendations"] = recommendations
    report["total_words"] = total_words
    
    # Save report to VFS
    report_md = format_keyword_report(report)
    vfs.write_file("keyword_report.md", report_md)
    
    print(f"  [Keywords] Analysis complete. Total words: {total_words}")
    
    return {
        "keyword_report": report,
        "vfs_data": vfs._files
    }


def format_keyword_report(report: dict) -> str:
    """Formats keyword report as markdown."""
    md = "## 📊 Keyword Analysis Report\n\n"
    
    md += f"**Total Word Count:** {report.get('total_words', 'N/A')}\n\n"
    
    md += f"### Primary Keyword\n`{report.get('primary_keyword', 'N/A')}`\n\n"
    
    md += "### Secondary Keywords\n"
    for kw in report.get("secondary_keywords", []):
        md += f"- {kw}\n"
    md += "\n"
    
    md += "### LSI Keywords (Semantically Related)\n"
    for kw in report.get("lsi_keywords", []):
        md += f"- {kw}\n"
    md += "\n"
    
    md += "### Keyword Density\n"
    md += "| Keyword | Density |\n|---------|--------|\n"
    for kw, density in report.get("keyword_density", {}).items():
        md += f"| {kw} | {density}% |\n"
    md += "\n"
    
    md += "### SEO Recommendations\n"
    for rec in report.get("recommendations", []):
        md += f"- {rec}\n"
    
    return md


def create_keyword_analyzer_graph():
    """Creates the keyword analysis subgraph."""
    workflow = StateGraph(KeywordState)
    
    workflow.add_node("extract_keywords", extract_keywords_node)
    workflow.add_node("analyze_density", analyze_density_node)
    
    workflow.set_entry_point("extract_keywords")
    workflow.add_edge("extract_keywords", "analyze_density")
    workflow.add_edge("analyze_density", END)
    
    return workflow.compile()
