import trafilatura
from typing import Optional

class WebScraper:
    def scrape(self, url: str) -> Optional[str]:
        """
        Scrapes the main text content from a URL.
        Returns None if extraction fails.
        """
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                result = trafilatura.extract(downloaded)
                return result
        except Exception as e:
            print(f"Error scraping {url}: {e}")
        return None

class MockScraper:
    def scrape(self, url: str) -> str:
        return f"Scraped content from {url}. This is a mock article about the topic. It contains headers and paragraphs relevant to the search."
