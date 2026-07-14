from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import pytest

from agent.memory import AsyncAgentMemory, AgentMemory


@pytest.fixture
def tmp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield str(Path(tmpdir) / "test.db")


@pytest.mark.asyncio
async def test_create_session(tmp_db):
    memory = AsyncAgentMemory(db_path=tmp_db)
    await memory.create_session("test-session")
    history = await memory.get_history("test-session")
    assert history == []
    await memory.close()


@pytest.mark.asyncio
async def test_save_and_get_history(tmp_db):
    memory = AsyncAgentMemory(db_path=tmp_db)
    await memory.create_session("test-session")
    await memory.save_message("test-session", "user", "Hello")
    await memory.save_message("test-session", "assistant", "Hi there!")

    history = await memory.get_history("test-session")
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hi there!"
    await memory.close()


@pytest.mark.asyncio
async def test_save_message_with_metadata(tmp_db):
    memory = AsyncAgentMemory(db_path=tmp_db)
    await memory.create_session("test-session")
    await memory.save_message(
        "test-session", "assistant", "Tool result",
        metadata={"tool": "get_stock_quote", "args": {"symbol": "AAPL"}}
    )

    history = await memory.get_history("test-session")
    assert len(history) == 1
    assert history[0]["metadata"]["tool"] == "get_stock_quote"
    await memory.close()


@pytest.mark.asyncio
async def test_save_trade(tmp_db):
    memory = AsyncAgentMemory(db_path=tmp_db)
    await memory.create_session("test-session")
    trade_id = await memory.save_trade(
        "test-session", "AAPL", "long", 0.8, 150.0, "Technical breakout"
    )
    assert trade_id is not None
    await memory.close()


@pytest.mark.asyncio
async def test_save_and_get_knowledge(tmp_db):
    memory = AsyncAgentMemory(db_path=tmp_db)
    await memory.save_knowledge("us_stock", "AAPL", "sector", "Technology")
    await memory.save_knowledge("us_stock", "MSFT", "sector", "Technology")

    knowledge = await memory.get_knowledge(market="us_stock")
    assert len(knowledge) == 2

    knowledge = await memory.get_knowledge(symbol="AAPL")
    assert len(knowledge) == 1
    assert knowledge[0]["key"] == "sector"
    await memory.close()


@pytest.mark.asyncio
async def test_get_knowledge_by_symbol(tmp_db):
    memory = AsyncAgentMemory(db_path=tmp_db)
    await memory.save_knowledge("us_stock", "AAPL", "sector", "Technology")
    await memory.save_knowledge("crypto", "BTC", "type", "Cryptocurrency")

    knowledge = await memory.get_knowledge(symbol="AAPL")
    assert len(knowledge) == 1
    assert knowledge[0]["symbol"] == "AAPL"
    await memory.close()


@pytest.mark.asyncio
async def test_session_updated_at(tmp_db):
    memory = AsyncAgentMemory(db_path=tmp_db)
    await memory.create_session("test-session")
    await memory.save_message("test-session", "user", "First message")

    import asyncio
    await asyncio.sleep(0.01)

    await memory.save_message("test-session", "user", "Second message")
    await memory.close()


@pytest.mark.asyncio
async def test_close_memory(tmp_db):
    memory = AsyncAgentMemory(db_path=tmp_db)
    await memory.create_session("test-session")
    await memory.close()
    assert memory._conn is None
