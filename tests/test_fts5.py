from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield str(Path(tmpdir) / "test_fts.db")


@pytest.mark.asyncio
async def test_search_history(tmp_db):
    from agent.memory import AsyncAgentMemory
    memory = AsyncAgentMemory(db_path=tmp_db)
    await memory.create_session("s1")
    await memory.save_message("s1", "user", "Analyze AAPL stock trend")
    await memory.save_message("s1", "assistant", "AAPL shows upward momentum")
    await memory.save_message("s1", "user", "What about MSFT?")

    results = await memory.search_history("AAPL")
    assert len(results) >= 1
    assert any("AAPL" in r["content"] for r in results)
    await memory.close()


@pytest.mark.asyncio
async def test_search_knowledge(tmp_db):
    from agent.memory import AsyncAgentMemory
    memory = AsyncAgentMemory(db_path=tmp_db)
    await memory.save_knowledge("us_stock", "AAPL", "sector", "Technology")
    await memory.save_knowledge("us_stock", "MSFT", "sector", "Technology")
    await memory.save_knowledge("crypto", "BTC", "type", "Cryptocurrency")

    results = await memory.search_knowledge("Technology")
    assert len(results) >= 2
    await memory.close()


@pytest.mark.asyncio
async def test_search_knowledge_by_market(tmp_db):
    from agent.memory import AsyncAgentMemory
    memory = AsyncAgentMemory(db_path=tmp_db)
    await memory.save_knowledge("us_stock", "AAPL", "sector", "Technology")
    await memory.save_knowledge("crypto", "BTC", "type", "Cryptocurrency")

    results = await memory.search_knowledge("Technology", market="us_stock")
    assert len(results) >= 1
    await memory.close()


def test_sync_search_history(tmp_db):
    from agent.memory import AgentMemory
    memory = AgentMemory(db_path=tmp_db)
    memory.create_session("s1")
    memory.save_message("s1", "user", "Analyze AAPL stock trend")
    memory.save_message("s1", "assistant", "AAPL shows upward momentum")

    results = memory.search_history("AAPL")
    assert len(results) >= 1
    assert any("AAPL" in r["content"] for r in results)
    memory.close()


def test_sync_search_knowledge(tmp_db):
    from agent.memory import AgentMemory
    memory = AgentMemory(db_path=tmp_db)
    memory.save_knowledge("us_stock", "AAPL", "sector", "Technology")

    results = memory.search_knowledge("Technology")
    assert len(results) >= 1
    memory.close()
