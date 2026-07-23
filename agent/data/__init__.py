"""
Data Source Abstraction Layer

Base class and registry for pluggable data sources.
"Inspired by OpenBB: connect once, consume everywhere."
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseDataSource(ABC):
    """Abstract base for data source plugins."""

    name: str = "base"
    priority: int = 0  # Higher = preferred

    @abstractmethod
    async def connect(self) -> bool:
        ...

    @abstractmethod
    async def get_klines(self, symbol: str, interval: str, period: str) -> list[dict]:
        ...

    @abstractmethod
    async def get_quote(self, symbol: str) -> dict:
        ...


_registry: dict[str, BaseDataSource] = {}


def register_source(source: BaseDataSource) -> None:
    _registry[source.name] = source


def get_source(name: str) -> BaseDataSource | None:
    return _registry.get(name)


def list_sources() -> list[str]:
    return sorted(_registry.keys(), key=lambda n: _registry[n].priority, reverse=True)
