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


@pytest.mark.asyncio
async def test_skill_definitions_included(tmp_db):
    with patch("agent.core.LLMClient") as mock_llm:
        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        mock_llm.return_value = mock_client
        agent = QuantAgent(db_path=tmp_db)

        skill_tools = [t for t in agent.tools if t["function"]["name"].startswith("skill_")]
        assert len(skill_tools) >= 3
        skill_names = [t["function"]["name"] for t in skill_tools]
        assert "skill_hk_fund_flow" in skill_names
        assert "skill_crypto_sentiment" in skill_names
        assert "skill_multi_market_compare" in skill_names
        await agent.close()


@pytest.mark.asyncio
async def test_system_prompt_has_alpha(tmp_db):
    assert "Alpha101" in SYSTEM_PROMPT
    assert "Alpha158" in SYSTEM_PROMPT


@pytest.mark.asyncio
async def test_execute_skill(tmp_db):
    with patch("agent.core.LLMClient") as mock_llm:
        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        mock_client.chat = AsyncMock(return_value={"choices": [{"message": {"content": "test result"}}]})
        mock_llm.return_value = mock_client
        agent = QuantAgent(db_path=tmp_db)

        with patch("agent.core.execute_tool", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"data": "test"}
            result = await agent._execute_skill("hk_fund_flow", {"query": "分析港股"}, "test_session")
            assert "test result" in result
            assert mock_exec.call_count >= 1
        await agent.close()
