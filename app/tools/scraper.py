import trafilatura
import os
import ssl
import urllib3
from typing import Optional

# Disable SSL verification if configured (for corporate networks)
if os.getenv("DISABLE_SSL_VERIFY", "").lower() == "true":
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    ssl._create_default_https_context = ssl._create_unverified_context
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''

class WebScraper:
    def scrape(self, url: str) -> Optional[str]:
        """
        Scrapes the main text content from a URL.
        Returns None if extraction fails.
        """
        try:
            # Configure proxy if available
            proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
            if proxy:
                os.environ['https_proxy'] = proxy
                os.environ['http_proxy'] = proxy
            
            # Disable SSL verification if configured
            no_ssl = os.getenv("DISABLE_SSL_VERIFY", "").lower() == "true"
            
            downloaded = trafilatura.fetch_url(url, no_ssl=no_ssl)
            if downloaded:
                result = trafilatura.extract(downloaded)
                return result
        except Exception as e:
            print(f"Error scraping {url}: {e}")
        return None

class MockScraper:
    def scrape(self, url: str) -> str:
        return f"Scraped content from {url}. This is a mock article about the topic. It contains headers and paragraphs relevant to the search."
