"""
Unit tests for Agent Communication System (AgentMessage + MessageBroker)
"""

import pytest
import asyncio

from agent.multi_agent.communication import (
    AgentMessage, MessageBroker, MessageType, MessagePriority
)


# ─── AgentMessage ────────────────────────────────────────────────────────────

class TestAgentMessage:

    def test_create_message(self):
        msg = AgentMessage(
            from_agent="Coordinator",
            to_agent="MarketAnalyst",
            message_type=MessageType.REQUEST,
            content={"task": "analyze_market"}
        )
        assert msg.from_agent == "Coordinator"
        assert msg.to_agent == "MarketAnalyst"
        assert msg.message_type == MessageType.REQUEST
        assert msg.message_id is not None
        assert msg.timestamp is not None

    def test_default_priority(self):
        msg = AgentMessage(
            from_agent="A", to_agent="B",
            message_type=MessageType.NOTIFICATION, content={}
        )
        assert msg.priority == MessagePriority.NORMAL

    def test_to_dict(self):
        msg = AgentMessage(
            from_agent="A", to_agent="B",
            message_type=MessageType.REQUEST, content={"key": "value"}
        )
        d = msg.to_dict()
        assert d["from_agent"] == "A"
        assert d["message_type"] == "REQUEST"
        assert d["priority"] == 2  # NORMAL

    def test_from_dict(self):
        original = AgentMessage(
            from_agent="A", to_agent="B",
            message_type=MessageType.RESPONSE,
            content={"result": 42}
        )
        d = original.to_dict()
        restored = AgentMessage.from_dict(d)
        assert restored.from_agent == original.from_agent
        assert restored.message_type == original.message_type
        assert restored.content == original.content

    def test_create_response(self):
        req = AgentMessage(
            from_agent="Coordinator", to_agent="RiskAgent",
            message_type=MessageType.REQUEST, content={"signal": "BUY"}
        )
        resp = req.create_response({"approved": True})
        assert resp.from_agent == "RiskAgent"
        assert resp.to_agent == "Coordinator"
        assert resp.message_type == MessageType.RESPONSE
        assert resp.correlation_id == req.message_id

    def test_repr(self):
        msg = AgentMessage(
            from_agent="A", to_agent="B",
            message_type=MessageType.REQUEST, content={}
        )
        assert "A" in repr(msg)
        assert "B" in repr(msg)


# ─── MessageBroker ────────────────────────────────────────────────────────────

class TestMessageBroker:

    @pytest.fixture
    def broker(self):
        return MessageBroker()

    def test_register_agent(self, broker):
        broker.register_agent("Alpha")
        assert "Alpha" in broker.agents
        assert "Alpha" in broker.queues

    def test_register_duplicate_noop(self, broker):
        broker.register_agent("Alpha")
        broker.register_agent("Alpha")
        assert len([a for a in broker.agents if a == "Alpha"]) == 1

    def test_unregister_agent(self, broker):
        broker.register_agent("Alpha")
        broker.unregister_agent("Alpha")
        assert "Alpha" not in broker.agents
        assert "Alpha" not in broker.queues

    @pytest.mark.asyncio
    async def test_send_and_receive(self, broker):
        broker.register_agent("Sender")
        broker.register_agent("Receiver")

        msg = AgentMessage(
            from_agent="Sender", to_agent="Receiver",
            message_type=MessageType.NOTIFICATION,
            content={"hello": "world"}
        )
        await broker.send(msg)

        received = await broker.receive("Receiver", timeout=1.0)
        assert received is not None
        assert received.content == {"hello": "world"}

    @pytest.mark.asyncio
    async def test_priority_ordering(self, broker):
        broker.register_agent("Sender")
        broker.register_agent("Receiver")

        low_msg = AgentMessage(
            from_agent="Sender", to_agent="Receiver",
            message_type=MessageType.NOTIFICATION,
            content={"order": "low"},
            priority=MessagePriority.LOW
        )
        high_msg = AgentMessage(
            from_agent="Sender", to_agent="Receiver",
            message_type=MessageType.NOTIFICATION,
            content={"order": "high"},
            priority=MessagePriority.CRITICAL
        )

        await broker.send(low_msg)
        await broker.send(high_msg)

        first  = await broker.receive("Receiver", timeout=1.0)
        second = await broker.receive("Receiver", timeout=1.0)

        # Critical should arrive first
        assert first.content["order"] == "high"
        assert second.content["order"] == "low"

    @pytest.mark.asyncio
    async def test_broadcast(self, broker):
        for name in ["Coordinator", "AgentA", "AgentB", "AgentC"]:
            broker.register_agent(name)

        broadcast = AgentMessage(
            from_agent="Coordinator", to_agent="ALL",
            message_type=MessageType.BROADCAST,
            content={"announcement": "market_open"}
        )
        await broker.send(broadcast)

        # Every agent except Coordinator should have received a notification
        for name in ["AgentA", "AgentB", "AgentC"]:
            msg = await broker.receive(name, timeout=1.0)
            assert msg is not None
            assert msg.content["announcement"] == "market_open"

    @pytest.mark.asyncio
    async def test_receive_timeout(self, broker):
        broker.register_agent("Lonely")
        result = await broker.receive("Lonely", timeout=0.1)
        assert result is None

    @pytest.mark.asyncio
    async def test_auto_register_on_send(self, broker):
        # Sending to an unregistered agent should auto-register it
        msg = AgentMessage(
            from_agent="A", to_agent="NewAgent",
            message_type=MessageType.NOTIFICATION, content={}
        )
        await broker.send(msg)
        assert "NewAgent" in broker.agents

    def test_queue_size(self, broker):
        broker.register_agent("Agent")
        assert broker.get_queue_size("Agent") == 0

    @pytest.mark.asyncio
    async def test_stats_update(self, broker):
        broker.register_agent("A")
        broker.register_agent("B")

        await broker.send(AgentMessage(
            from_agent="A", to_agent="B",
            message_type=MessageType.REQUEST, content={}
        ))
        stats = broker.get_stats()
        assert stats["total_messages"] == 1
        assert "REQUEST" in stats["messages_by_type"]

    def test_message_history(self, broker):
        broker.message_history = []
        assert broker.get_message_history() == []

    @pytest.mark.asyncio
    async def test_message_history_filter(self, broker):
        broker.register_agent("Alpha")
        broker.register_agent("Beta")
        broker.register_agent("Gamma")

        await broker.send(AgentMessage(
            from_agent="Alpha", to_agent="Beta",
            message_type=MessageType.REQUEST, content={}
        ))
        await broker.send(AgentMessage(
            from_agent="Gamma", to_agent="Beta",
            message_type=MessageType.REQUEST, content={}
        ))

        alpha_msgs = broker.get_message_history(agent_name="Alpha")
        assert len(alpha_msgs) == 1
        assert alpha_msgs[0].from_agent == "Alpha"

    def test_reset_stats(self, broker):
        broker.stats['total_messages'] = 99
        broker.reset_stats()
        assert broker.stats['total_messages'] == 0
