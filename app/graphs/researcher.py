from typing import TypedDict, List, Annotated, Any
from langgraph.graph import StateGraph, END
from app.core.state import AgentState
from app.core.vfs import VFS
from app.core.llm import get_researcher_model
from app.tools.search import DuckDuckGoSearchProvider, MockSearchProvider
from app.tools.scraper import WebScraper, MockScraper
import json
import re

# Local state for the researcher subgraph
# IMPORTANT: VFS object itself is not serializable by msgpack/sqlite.
# We must pass "vfs_data" (dict) instead, or reconstruct VFS inside nodes.
class ResearchState(TypedDict):
    query: str
    vfs_data: dict 
    search_results: List[dict]
    selected_urls: List[str]
    summaries: List[str]

# --- NODES ---

def search_node(state: ResearchState):
    """Searches for the query."""
    query = state["query"]
    print(f"  [Researcher] Searching for: {query}")
    
    try:
        provider = DuckDuckGoSearchProvider()
        results = provider.search(query, max_results=5)
        if not results:
             raise Exception("No results found")
    except Exception:
        print("  [Researcher] DDG failed, using Mock.")
        provider = MockSearchProvider()
        results = provider.search(query)
        
    return {"search_results": [r.model_dump() for r in results]}

def select_node(state: ResearchState):
    """Selects the best URLs to scrape."""
    results = state["search_results"]
    llm = get_researcher_model()
    
    prompt = f"""
    Here are search results for "{state['query']}":
    {json.dumps(results[:5], indent=2)}
    
    Return ONLY a JSON list of the top 2 URLs that seem most information-rich and relevant.
    Example: ["http://site.com/a", "http://site.com/b"]
    """
    
    try:
        response = llm.invoke(prompt)
        urls = re.findall(r'https?://[^\s",]+', response.content)
        selected = [u.strip('",[]') for u in urls][:2]
        if not selected:
            selected = [r['url'] for r in results[:2]]
    except:
        selected = [r['url'] for r in results[:2]]
        
    print(f"  [Researcher] Selected: {selected}")
    return {"selected_urls": selected}

def scrape_and_summarize_node(state: ResearchState):
    """Scrapes and summarizes each selected URL."""
    urls = state["selected_urls"]
    llm = get_researcher_model()
    
    # Rehydrate VFS
    vfs = VFS()
    vfs._files = {k: v for k, v in state.get("vfs_data", {}).items()}
    
    for url in urls:
        # Determine scraper based on URL
        if "mock" in url or "example.com" in url:
            scraper = MockScraper()
        else:
            scraper = WebScraper()
            
        print(f"  [Researcher] Scraping {url}...")
        content = scraper.scrape(url)
        
        if not content:
            print(f"  [Researcher] Failed to scrape {url}")
            continue
            
        truncated_content = content[:10000] 
        
        prompt = f"""
        Summarize the following text related to "{state['query']}". 
        Extract key facts, statistics, and definitions.
        
        Text:
        {truncated_content}
        """
        
        try:
            response = llm.invoke(prompt)
            summary = response.content
            
            # Save to VFS
            filename = f"research/summary_{abs(hash(url))}.md"
            vfs.write_file(filename, summary, metadata={"url": url, "query": state['query']})
            print(f"  [Researcher] Saved {filename}")
        except Exception as e:
            print(f"  [Researcher] Summarization failed: {e}")
            
    # Return updated VFS data
    return {"vfs_data": vfs._files}

# --- GRAPH DEFINITION ---

def create_researcher_graph():
    workflow = StateGraph(ResearchState)
    
    workflow.add_node("search", search_node)
    workflow.add_node("select", select_node)
    workflow.add_node("scrape_summarize", scrape_and_summarize_node)
    
    workflow.set_entry_point("search")
    
    workflow.add_edge("search", "select")
    workflow.add_edge("select", "scrape_summarize")
    workflow.add_edge("scrape_summarize", END)
    
    return workflow.compile()
