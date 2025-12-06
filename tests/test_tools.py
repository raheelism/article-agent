import pytest
from app.tools.search import MockSearchProvider
from app.tools.scraper import MockScraper

def test_mock_search():
    provider = MockSearchProvider()
    results = provider.search("productivity")
    assert len(results) > 0
    assert results[0].rank == 1
    assert "productivity" in results[0].title.lower() or "productivity" in results[0].snippet.lower()

def test_mock_scraper():
    scraper = MockScraper()
    content = scraper.scrape("https://example.com")
    assert "Scraped content" in content
    assert "https://example.com" in content
