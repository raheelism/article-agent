"""
Tests for SEO Analysis Agents: FAQ, Keywords, and Linking
"""

import pytest
from app.core.vfs import VFS


class TestFAQAgent:
    """Tests for the FAQ generation agent."""
    
    def test_faq_state_structure(self):
        """Test that FAQ state has required fields."""
        from app.graphs.faq import FAQState
        
        state: FAQState = {
            "vfs_data": {},
            "draft_file": "draft.md",
            "faqs": []
        }
        
        assert "vfs_data" in state
        assert "draft_file" in state
        assert "faqs" in state
    
    def test_faq_item_structure(self):
        """Test FAQ item has question and answer."""
        faq_item = {
            "question": "What is the benefit?",
            "answer": "The main benefit is improved efficiency."
        }
        
        assert "question" in faq_item
        assert "answer" in faq_item
        assert len(faq_item["question"]) > 0
        assert len(faq_item["answer"]) > 0
    
    def test_faq_graph_creation(self):
        """Test that FAQ graph can be created."""
        from app.graphs.faq import create_faq_graph
        
        graph = create_faq_graph()
        assert graph is not None


class TestKeywordAnalyzer:
    """Tests for the keyword analysis agent."""
    
    def test_keyword_state_structure(self):
        """Test that keyword state has required fields."""
        from app.graphs.keyword_analyzer import KeywordState
        
        state: KeywordState = {
            "vfs_data": {},
            "draft_file": "draft.md",
            "topic": "test topic",
            "keyword_report": {}
        }
        
        assert "vfs_data" in state
        assert "topic" in state
        assert "keyword_report" in state
    
    def test_keyword_report_structure(self):
        """Test keyword report has all required fields."""
        report = {
            "primary_keyword": "test keyword",
            "secondary_keywords": ["keyword1", "keyword2"],
            "lsi_keywords": ["related1", "related2"],
            "keyword_density": {"test keyword": 1.5},
            "recommendations": ["Add more keywords"],
            "total_words": 1000
        }
        
        assert "primary_keyword" in report
        assert "secondary_keywords" in report
        assert "lsi_keywords" in report
        assert "keyword_density" in report
        assert "recommendations" in report
    
    def test_keyword_graph_creation(self):
        """Test that keyword analyzer graph can be created."""
        from app.graphs.keyword_analyzer import create_keyword_analyzer_graph
        
        graph = create_keyword_analyzer_graph()
        assert graph is not None
    
    def test_format_keyword_report(self):
        """Test keyword report formatting."""
        from app.graphs.keyword_analyzer import format_keyword_report
        
        report = {
            "primary_keyword": "remote work",
            "secondary_keywords": ["work from home", "productivity"],
            "lsi_keywords": ["telecommuting"],
            "keyword_density": {"remote work": 1.2},
            "recommendations": ["Good density"],
            "total_words": 1500
        }
        
        md = format_keyword_report(report)
        
        assert "remote work" in md
        assert "Secondary Keywords" in md
        assert "LSI Keywords" in md
        assert "Keyword Density" in md


class TestLinkingSuggester:
    """Tests for the linking suggestion agent."""
    
    def test_linking_state_structure(self):
        """Test that linking state has required fields."""
        from app.graphs.linking import LinkingState
        
        state: LinkingState = {
            "vfs_data": {},
            "draft_file": "draft.md",
            "topic": "test topic",
            "linking_report": {}
        }
        
        assert "vfs_data" in state
        assert "topic" in state
        assert "linking_report" in state
    
    def test_internal_link_structure(self):
        """Test internal link suggestion structure."""
        link = {
            "anchor_text": "productivity tools",
            "suggested_target": "Best Productivity Tools Guide",
            "context": "Link from tools section"
        }
        
        assert "anchor_text" in link
        assert "suggested_target" in link
        assert "context" in link
    
    def test_external_link_structure(self):
        """Test external link suggestion structure."""
        link = {
            "source_name": "Harvard Business Review",
            "url": "https://hbr.org/article",
            "anchor_text": "according to HBR research",
            "placement_context": "Cite in productivity section"
        }
        
        assert "source_name" in link
        assert "url" in link
        assert "anchor_text" in link
        assert "placement_context" in link
    
    def test_linking_graph_creation(self):
        """Test that linking graph can be created."""
        from app.graphs.linking import create_linking_graph
        
        graph = create_linking_graph()
        assert graph is not None
    
    def test_format_linking_report(self):
        """Test linking report formatting."""
        from app.graphs.linking import format_linking_report
        
        report = {
            "internal_links": [
                {
                    "anchor_text": "best practices",
                    "suggested_target": "Best Practices Guide",
                    "context": "In tips section"
                }
            ],
            "external_links": [
                {
                    "source_name": "Research Paper",
                    "url": "https://example.com/paper",
                    "anchor_text": "study shows",
                    "placement_context": "Support statistics"
                }
            ]
        }
        
        md = format_linking_report(report)
        
        assert "Internal Links" in md
        assert "External Links" in md
        assert "best practices" in md
        assert "Research Paper" in md


class TestAgentStateWithSEO:
    """Tests for the updated AgentState with SEO fields."""
    
    def test_agent_state_has_seo_fields(self):
        """Test that AgentState includes new SEO fields."""
        from app.core.state import AgentState
        
        # Check that the TypedDict accepts these fields
        state: AgentState = {
            "topic": "test",
            "word_count": 1500,
            "language": "English",
            "plan": [],
            "current_task_index": 0,
            "vfs_data": {},
            "faqs": [],
            "keyword_report": {},
            "linking_report": {},
            "logs": []
        }
        
        assert "faqs" in state
        assert "keyword_report" in state
        assert "linking_report" in state
