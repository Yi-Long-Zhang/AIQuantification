import tempfile
import pytest
from unittest.mock import patch, MagicMock
from agent.core import QuantAgent, SYSTEM_PROMPT


@pytest.fixture
def agent():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    with patch("agent.core.LLMClient") as mock_llm:
        mock_llm.return_value = MagicMock()
        agent = QuantAgent(db_path=db_path)
        yield agent


def test_system_prompt_defined():
    assert len(SYSTEM_PROMPT) > 0
    assert "quantitative trading" in SYSTEM_PROMPT.lower()


def test_agent_initialization(agent):
    assert agent.llm is not None
    assert agent.memory is not None
    assert agent.tools is not None
    assert len(agent.tools) > 0


def test_convert_history(agent):
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
        {"role": "system", "content": "test"},
    ]
    messages = agent._convert_history(history)
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == SYSTEM_PROMPT
    assert len(messages) == 4
    assert messages[1]["content"] == "Hello"
    assert messages[2]["content"] == "Hi"
    assert messages[3]["content"] == "test"


def test_convert_history_limit(agent):
    history = [{"role": "user", "content": f"msg-{i}"} for i in range(30)]
    messages = agent._convert_history(history)
    assert len(messages) <= 21


def test_convert_history_filters_invalid_roles(agent):
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "invalid_role", "content": "should be filtered"},
        {"role": "assistant", "content": "Hi"},
    ]
    messages = agent._convert_history(history)
    assert len(messages) == 3
    assert all(m["role"] in ("system", "user", "assistant") for m in messages)
