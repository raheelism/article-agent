"""
Linking Suggester Agent

Generates structured linking suggestions:
- Internal links: 3-5 anchor texts with suggested target pages
- External links: 2-4 authoritative sources with placement context
"""

from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from app.core.vfs import VFS
from app.core.llm import get_researcher_model
import json


class LinkingState(TypedDict):
    vfs_data: dict
    draft_file: str
    topic: str
    linking_report: Dict  # Structured linking suggestions


class InternalLink(TypedDict):
    anchor_text: str
    suggested_target: str
    context: str  # Where in the article to place it


class ExternalLink(TypedDict):
    source_name: str
    url: str
    anchor_text: str
    placement_context: str  # Why and where to cite


class LinkingReport(TypedDict):
    internal_links: List[InternalLink]
    external_links: List[ExternalLink]


def suggest_internal_links_node(state: LinkingState) -> dict:
    """
    Suggests internal linking opportunities based on article content.
    """
    vfs = VFS()
    vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()}
    
    draft = ""
    if vfs.exists(state["draft_file"]):
        draft = vfs.read_file(state["draft_file"])
    
    topic = state.get("topic", "")
    
    llm = get_researcher_model()
    
    prompt = f"""
    You are an SEO linking strategist. Analyze the article and suggest internal linking opportunities.
    
    TOPIC: {topic}
    
    ARTICLE:
    {draft[:5000]}
    
    Generate 3-5 INTERNAL LINK suggestions. For each:
    1. Identify a phrase in the article that could be linked
    2. Suggest what related page/article it should link to
    3. Explain where in the article this link fits
    
    Return ONLY valid JSON. No markdown.
    
    Format:
    {{
        "internal_links": [
            {{
                "anchor_text": "phrase to make clickable",
                "suggested_target": "Related Topic Page Title",
                "context": "Found in the section about X, links to deeper coverage of Y"
            }}
        ]
    }}
    """
    
    print("  [Linking] Generating internal link suggestions...")
    
    try:
        response = llm.invoke(prompt)
        content = response.content
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        data = json.loads(content.strip())
        internal_links = data.get("internal_links", [])
        
        # Validate structure
        validated = []
        for link in internal_links[:5]:
            if isinstance(link, dict) and "anchor_text" in link:
                validated.append({
                    "anchor_text": str(link.get("anchor_text", "")),
                    "suggested_target": str(link.get("suggested_target", "")),
                    "context": str(link.get("context", ""))
                })
        
        return {
            "linking_report": {
                "internal_links": validated,
                "external_links": []
            }
        }
        
    except Exception as e:
        print(f"  [Linking] Internal link generation failed: {e}")
        return {
            "linking_report": {
                "internal_links": [
                    {
                        "anchor_text": topic.split()[0] + " guide",
                        "suggested_target": f"Complete Guide to {topic}",
                        "context": "Link from introduction to comprehensive guide"
                    },
                    {
                        "anchor_text": "best practices",
                        "suggested_target": f"{topic} Best Practices",
                        "context": "Link from practical tips section"
                    },
                    {
                        "anchor_text": "getting started",
                        "suggested_target": f"{topic} for Beginners",
                        "context": "Link for newcomers to the topic"
                    }
                ],
                "external_links": []
            }
        }


def suggest_external_links_node(state: LinkingState) -> dict:
    """
    Suggests authoritative external sources to cite.
    """
    vfs = VFS()
    vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()}
    
    draft = ""
    if vfs.exists(state["draft_file"]):
        draft = vfs.read_file(state["draft_file"])
    
    topic = state.get("topic", "")
    report = state.get("linking_report", {"internal_links": [], "external_links": []})
    
    # Collect research sources
    research_sources = []
    for filename in vfs.list_files():
        if filename.startswith("research/"):
            file_obj = vfs.get_file(filename)
            if file_obj and file_obj.metadata:
                url = file_obj.metadata.get("url", "")
                if url and url != "unknown":
                    research_sources.append(url)
    
    llm = get_researcher_model()
    
    prompt = f"""
    You are an SEO linking strategist. Suggest authoritative external sources to cite in this article.
    
    TOPIC: {topic}
    
    RESEARCH SOURCES USED:
    {json.dumps(research_sources[:5], indent=2)}
    
    ARTICLE EXCERPT:
    {draft[:3000]}
    
    Generate 2-4 EXTERNAL LINK suggestions. For each:
    1. Name of the authoritative source (e.g., "Harvard Business Review", "Stanford Study")
    2. URL (use real research sources if available, or suggest plausible authority sites)
    3. Anchor text to use
    4. Where and why to place this citation
    
    Prefer: academic studies, industry reports, government data, established publications.
    
    Return ONLY valid JSON. No markdown.
    
    Format:
    {{
        "external_links": [
            {{
                "source_name": "Stanford University Research",
                "url": "https://example.com/study",
                "anchor_text": "according to Stanford researchers",
                "placement_context": "Cite when discussing health benefits to add credibility"
            }}
        ]
    }}
    """
    
    print("  [Linking] Generating external link suggestions...")
    
    try:
        response = llm.invoke(prompt)
        content = response.content
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        data = json.loads(content.strip())
        external_links = data.get("external_links", [])
        
        # Validate structure
        validated = []
        for link in external_links[:4]:
            if isinstance(link, dict) and "source_name" in link:
                validated.append({
                    "source_name": str(link.get("source_name", "")),
                    "url": str(link.get("url", "")),
                    "anchor_text": str(link.get("anchor_text", "")),
                    "placement_context": str(link.get("placement_context", ""))
                })
        
        # Also add any research sources we actually used
        for url in research_sources[:2]:
            if not any(v["url"] == url for v in validated):
                validated.append({
                    "source_name": "Research Source",
                    "url": url,
                    "anchor_text": "according to research",
                    "placement_context": "Primary research source used for this article"
                })
        
        report["external_links"] = validated[:4]
        
    except Exception as e:
        print(f"  [Linking] External link generation failed: {e}")
        # Use research sources as fallback
        for url in research_sources[:2]:
            report["external_links"].append({
                "source_name": "Research Source",
                "url": url,
                "anchor_text": "according to research",
                "placement_context": "Primary research source"
            })
    
    # Save report to VFS
    report_md = format_linking_report(report)
    vfs.write_file("linking_report.md", report_md)
    
    print(f"  [Linking] Generated {len(report['internal_links'])} internal + {len(report['external_links'])} external links")
    
    return {
        "linking_report": report,
        "vfs_data": vfs._files
    }


def format_linking_report(report: dict) -> str:
    """Formats linking report as markdown."""
    md = "## 🔗 Linking Strategy Report\n\n"
    
    md += "### Internal Links (3-5 Suggestions)\n\n"
    md += "| Anchor Text | Suggested Target Page | Context |\n"
    md += "|-------------|----------------------|----------|\n"
    for link in report.get("internal_links", []):
        md += f"| {link.get('anchor_text', '')} | {link.get('suggested_target', '')} | {link.get('context', '')} |\n"
    md += "\n"
    
    md += "### External Links (Authoritative Sources)\n\n"
    md += "| Source | URL | Anchor Text | Placement |\n"
    md += "|--------|-----|-------------|----------|\n"
    for link in report.get("external_links", []):
        url = link.get('url', '')
        short_url = url[:50] + "..." if len(url) > 50 else url
        md += f"| {link.get('source_name', '')} | {short_url} | {link.get('anchor_text', '')} | {link.get('placement_context', '')} |\n"
    
    return md


def create_linking_graph():
    """Creates the linking suggestion subgraph."""
    workflow = StateGraph(LinkingState)
    
    workflow.add_node("suggest_internal", suggest_internal_links_node)
    workflow.add_node("suggest_external", suggest_external_links_node)
    
    workflow.set_entry_point("suggest_internal")
    workflow.add_edge("suggest_internal", "suggest_external")
    workflow.add_edge("suggest_external", END)
    
    return workflow.compile()
