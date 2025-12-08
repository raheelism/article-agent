from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pydantic import BaseModel
from ddgs import DDGS
import time
import os
import ssl
import urllib3

# Disable SSL verification if configured (for corporate networks)
if os.getenv("DISABLE_SSL_VERIFY", "").lower() == "true":
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    ssl._create_default_https_context = ssl._create_unverified_context
    # Also set for requests library
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''

class SearchResult(BaseModel):
    url: str
    title: str
    snippet: str
    rank: int

class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        pass

class DuckDuckGoSearchProvider(SearchProvider):
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        results = []
        try:
            with DDGS(verify=os.getenv("DISABLE_SSL_VERIFY", "").lower() != "true") as ddgs:
                # DDGS.text() yields dictionaries
                search_gen = ddgs.text(query, max_results=max_results)
                for i, r in enumerate(search_gen):
                    results.append(SearchResult(
                        rank=i+1,
                        url=r.get("href", ""),
                        title=r.get("title", ""),
                        snippet=r.get("body", "")
                    ))
        except Exception as e:
            print(f"Error during DuckDuckGo search: {e}")
            # In production, we might want to raise or log
        return results

class MockSearchProvider(SearchProvider):
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        # Return a deterministic mock result
        return [
            SearchResult(
                rank=1,
                url="https://mock-example.com/best-tools",
                title=f"Best Tools for {query}",
                snippet=f"This is a mock snippet for {query}. It talks about productivity."
            ),
             SearchResult(
                rank=2,
                url="https://mock-competitor.com/top-10",
                title=f"Top 10 Things regarding {query}",
                snippet="Another valuable mock resource."
            )
        ]
