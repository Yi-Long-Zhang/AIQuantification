"""
Broker Base Module

Defines the abstract base class for all broker connections.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# ── Data types ───────────────────────────────────────────────────────────────

@dataclass
class AccountInfo:
    """Broker account summary."""
    broker: str
    account_id: str
    cash: float
    equity: float
    buying_power: float
    currency: str = "USD"
    status: str = "ACTIVE"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "broker": self.broker,
            "account_id": self.account_id,
            "cash": self.cash,
            "equity": self.equity,
            "buying_power": self.buying_power,
            "currency": self.currency,
            "status": self.status,
            "timestamp": self.timestamp,
        }


@dataclass
class Position:
    """A single open position."""
    symbol: str
    qty: float
    avg_entry_price: float
    current_price: float
    market_value: float
    unrealized_pl: float
    unrealized_pl_pct: float
    asset_class: str = "us_equity"

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "qty": self.qty,
            "avg_entry_price": self.avg_entry_price,
            "current_price": self.current_price,
            "market_value": self.market_value,
            "unrealized_pl": self.unrealized_pl,
            "unrealized_pl_pct": self.unrealized_pl_pct,
            "asset_class": self.asset_class,
        }


@dataclass
class Order:
    """A trade order."""
    order_id: str
    symbol: str
    side: str  # buy / sell
    qty: float
    filled_qty: float
    price: float | None
    avg_fill_price: float | None
    status: str  # new / filled / partially_filled / cancelled
    type: str  # market / limit / stop
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side,
            "qty": self.qty,
            "filled_qty": self.filled_qty,
            "price": self.price,
            "avg_fill_price": self.avg_fill_price,
            "status": self.status,
            "type": self.type,
            "created_at": self.created_at,
        }


@dataclass
class Trade:
    """A completed trade (fill)."""
    trade_id: str
    symbol: str
    side: str
    qty: float
    price: float
    realized_pl: float | None
    commission: float | None
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "side": self.side,
            "qty": self.qty,
            "price": self.price,
            "realized_pl": self.realized_pl,
            "commission": self.commission,
            "timestamp": self.timestamp,
        }


# ── Base class ───────────────────────────────────────────────────────────────

class BrokerBase(ABC):
    """
    Abstract base class for broker connections.

    Subclasses must implement all abstract methods.
    """

    def __init__(self, name: str):
        self.name = name
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the broker. Returns True on success."""
        ...

    async def disconnect(self) -> None:
        """Close the connection."""
        self._connected = False

    @abstractmethod
    async def get_account(self) -> AccountInfo:
        """Get account summary."""
        ...

    @abstractmethod
    async def get_positions(self) -> list[Position]:
        """Get all open positions."""
        ...

    @abstractmethod
    async def get_orders(self, status: str | None = None) -> list[Order]:
        """Get recent orders, optionally filtered by status."""
        ...

    async def get_trades(self, limit: int = 100) -> list[Trade]:
        """Get recent completed trades (fills)."""
        return []

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "connected": self._connected,
        }
