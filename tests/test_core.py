from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.core import QuantAgent, SYSTEM_PROMPT


@pytest.fixture
def tmp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield str(Path(tmpdir) / "test.db")


def test_system_prompt_defined():
    assert SYSTEM_PROMPT is not None
    assert len(SYSTEM_PROMPT) > 0
    assert "quantitative trading" in SYSTEM_PROMPT.lower()


@pytest.mark.asyncio
async def test_agent_initialization(tmp_db):
    with patch("agent.core.LLMClient") as mock_llm:
        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        mock_llm.return_value = mock_client
        agent = QuantAgent(db_path=tmp_db)
        assert agent.llm is not None
        assert agent.memory is not None
        await agent.close()


@pytest.mark.asyncio
async def test_convert_history(tmp_db):
    with patch("agent.core.LLMClient") as mock_llm:
        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        mock_llm.return_value = mock_client
        agent = QuantAgent(db_path=tmp_db)

        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ]

        messages = agent._convert_history(history)
        assert len(messages) == 4
        assert messages[0]["role"] == "system"
        assert messages[1]["content"] == "Hello"
        assert messages[2]["content"] == "Hi there!"
        await agent.close()


@pytest.mark.asyncio
async def test_convert_history_limit(tmp_db):
    with patch("agent.core.LLMClient") as mock_llm:
        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        mock_llm.return_value = mock_client
        agent = QuantAgent(db_path=tmp_db)

        history = [{"role": "user", "content": f"Message {i}"} for i in range(30)]
        messages = agent._convert_history(history)

        assert len(messages) == 21
        await agent.close()


@pytest.mark.asyncio
async def test_convert_history_filters_invalid_roles(tmp_db):
    with patch("agent.core.LLMClient") as mock_llm:
        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        mock_llm.return_value = mock_client
        agent = QuantAgent(db_path=tmp_db)

        history = [
            {"role": "user", "content": "Hello"},
            {"role": "invalid", "content": "This should be filtered"},
            {"role": "assistant", "content": "Hi!"},
            {"role": "system", "content": "System message"},
        ]

        messages = agent._convert_history(history)
        assert len(messages) == 4
        assert messages[1]["content"] == "Hello"
        assert messages[2]["content"] == "Hi!"
        assert messages[3]["content"] == "System message"
        await agent.close()
