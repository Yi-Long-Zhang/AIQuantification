"""
Broker registry tests.
"""

from __future__ import annotations

import pytest
from agent.broker.registry import BrokerRegistry, get_broker_registry
from agent.broker.base import BrokerBase


class _MockBroker(BrokerBase):
    """Minimal mock broker for testing the registry."""
    def __init__(self, name: str, connect_ok: bool = True):
        super().__init__(name)
        self._connect_ok = connect_ok

    async def connect(self) -> bool:
        self._connected = self._connect_ok
        return self._connect_ok

    async def get_account(self):
        raise NotImplementedError

    async def get_positions(self):
        return []

    async def get_orders(self, status=None):
        return []


@pytest.fixture
def registry():
    r = BrokerRegistry()
    r.register(_MockBroker("alpaca"))
    r.register(_MockBroker("ibkr"))
    return r


class TestBrokerRegistry:
    def test_register_and_list(self, registry):
        names = registry.list_names()
        assert "alpaca" in names
        assert "ibkr" in names

    def test_get_exists(self, registry):
        broker = registry.get("alpaca")
        assert broker is not None
        assert broker.name == "alpaca"

    def test_get_not_found(self, registry):
        assert registry.get("nonexistent") is None

    def test_list_all(self, registry):
        brokers = registry.list_all()
        assert len(brokers) == 2
        assert all("name" in b for b in brokers)
        assert all("connected" in b for b in brokers)

    def test_connect_all_success(self, registry):
        import asyncio
        results = asyncio.run(registry.connect_all())
        assert results["alpaca"] is True
        assert results["ibkr"] is True

    def test_connect_all_failure(self):
        r = BrokerRegistry()
        r.register(_MockBroker("failing", connect_ok=False))
        import asyncio
        results = asyncio.run(r.connect_all())
        assert results["failing"] is False

    def test_singleton(self):
        r1 = get_broker_registry()
        r2 = get_broker_registry()
        assert r1 is r2
