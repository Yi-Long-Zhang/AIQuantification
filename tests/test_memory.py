import tempfile
import pytest
from agent.memory import AgentMemory


@pytest.fixture
def memory():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    mem = AgentMemory(db_path=db_path)
    yield mem
    mem.close()


def test_create_session(memory):
    memory.create_session("test-session-1")
    history = memory.get_history("test-session-1")
    assert history == []


def test_save_and_get_history(memory):
    memory.create_session("test-session-2")
    memory.save_message("test-session-2", "user", "Hello")
    memory.save_message("test-session-2", "assistant", "Hi there")
    history = memory.get_history("test-session-2")
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hi there"


def test_save_message_with_metadata(memory):
    memory.create_session("test-session-3")
    metadata = {"tool": "get_klines", "args": {"symbol": "AAPL"}}
    memory.save_message("test-session-3", "assistant", "[Tool: get_klines]", metadata=metadata)
    history = memory.get_history("test-session-3")
    assert len(history) == 1
    assert history[0]["metadata"]["tool"] == "get_klines"


def test_save_trade(memory):
    memory.create_session("test-session-4")
    trade_id = memory.save_trade(
        session_id="test-session-4",
        symbol="AAPL",
        direction="long",
        confidence=0.8,
        entry_price=150.0,
        reason="SMA crossover",
    )
    assert trade_id is not None


def test_save_and_get_knowledge(memory):
    memory.save_knowledge("us_stock", "AAPL", "sector", "Technology")
    knowledge = memory.get_knowledge(market="us_stock")
    assert len(knowledge) == 1
    assert knowledge[0]["key"] == "sector"
    assert knowledge[0]["value"] == "Technology"


def test_get_knowledge_by_symbol(memory):
    memory.save_knowledge("us_stock", "AAPL", "sector", "Technology")
    memory.save_knowledge("us_stock", "MSFT", "sector", "Technology")
    knowledge = memory.get_knowledge(symbol="AAPL")
    assert len(knowledge) == 1


def test_session_updated_at(memory):
    memory.create_session("test-session-5")
    memory.save_message("test-session-5", "user", "test")
    history = memory.get_history("test-session-5")
    assert "created_at" in history[0]


def test_close_memory(memory):
    memory.close()
    assert memory._conn is not None
