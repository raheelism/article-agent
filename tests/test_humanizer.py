
import pytest
from app.graphs.humanizer import create_humanizer_graph, HumanizerState, should_continue
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_llm():
    with patch("app.graphs.humanizer.get_optimizer_model") as mock:
        yield mock

def test_should_continue_loop():
    """Test loop condition"""
    state = {
        "last_critique": {"ai_artifact_score": 5},
        "iteration_count": 0
    }
    next_node = should_continue(state)
    assert next_node == "humanization_critic"

def test_should_continue_exit_score():
    """Test exit on good score"""
    state = {
        "last_critique": {"ai_artifact_score": 2},
        "iteration_count": 0
    }
    next_node = should_continue(state)
    assert next_node == "__end__"

def test_should_continue_exit_iterations():
    """Test exit on max iterations"""
    state = {
        "last_critique": {"ai_artifact_score": 8},
        "iteration_count": 3
    }
    next_node = should_continue(state)
    assert next_node == "__end__"

def test_humanizer_graph_structure():
    """Test graph compilation"""
    graph = create_humanizer_graph()
    assert graph is not None
