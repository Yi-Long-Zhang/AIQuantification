"""
Broker Registry Module

Central registry for managing broker connections.
"""

from __future__ import annotations

import logging
from typing import Any

from .base import BrokerBase

logger = logging.getLogger(__name__)


class BrokerRegistry:
    """Central registry for broker connections."""

    def __init__(self) -> None:
        self._brokers: dict[str, BrokerBase] = {}

    def register(self, broker: BrokerBase) -> None:
        """Register a broker connection."""
        self._brokers[broker.name] = broker
        logger.info(f"Broker registered: {broker.name}")

    def get(self, name: str) -> BrokerBase | None:
        """Get a broker by name."""
        return self._brokers.get(name)

    def list_names(self) -> list[str]:
        """List all registered broker names."""
        return list(self._brokers.keys())

    def list_all(self) -> list[dict[str, Any]]:
        """List all brokers as dicts."""
        return [b.to_dict() for b in self._brokers.values()]

    async def connect_all(self) -> dict[str, bool]:
        """Connect all registered brokers. Returns name→success mapping."""
        results = {}
        for name, broker in self._brokers.items():
            try:
                results[name] = await broker.connect()
            except Exception as e:
                logger.error(f"Failed to connect {name}: {e}")
                results[name] = False
        return results

    async def disconnect_all(self) -> None:
        """Disconnect all brokers."""
        for broker in self._brokers.values():
            try:
                await broker.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting {broker.name}: {e}")


_registry = BrokerRegistry()


def get_broker_registry() -> BrokerRegistry:
    return _registry
