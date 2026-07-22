"""
Broker base module tests.
"""

from __future__ import annotations

import pytest
from agent.broker.base import AccountInfo, Position, Order, Trade


class TestAccountInfo:
    def test_to_dict_contains_all_fields(self):
        info = AccountInfo(
            broker="alpaca",
            account_id="abc123",
            cash=50000.0,
            equity=55000.0,
            buying_power=100000.0,
        )
        d = info.to_dict()
        assert d["broker"] == "alpaca"
        assert d["account_id"] == "abc123"
        assert d["cash"] == 50000.0
        assert d["equity"] == 55000.0
        assert d["buying_power"] == 100000.0
        assert d["currency"] == "USD"
        assert d["status"] == "ACTIVE"

    def test_default_timestamp(self):
        info = AccountInfo(broker="test", account_id="x", cash=0, equity=0, buying_power=0)
        assert info.timestamp is not None


class TestPosition:
    def test_to_dict(self):
        pos = Position(
            symbol="AAPL", qty=10, avg_entry_price=150.0,
            current_price=160.0, market_value=1600.0,
            unrealized_pl=100.0, unrealized_pl_pct=6.67,
        )
        d = pos.to_dict()
        assert d["symbol"] == "AAPL"
        assert d["qty"] == 10
        assert d["unrealized_pl"] == 100.0

    def test_negative_pl(self):
        pos = Position(
            symbol="TSLA", qty=5, avg_entry_price=200.0,
            current_price=180.0, market_value=900.0,
            unrealized_pl=-100.0, unrealized_pl_pct=-10.0,
        )
        assert pos.to_dict()["unrealized_pl"] == -100.0


class TestOrder:
    def test_to_dict(self):
        order = Order(
            order_id="ord1", symbol="AAPL", side="buy",
            qty=100, filled_qty=100, price=150.0,
            avg_fill_price=150.0, status="filled",
            type="limit", created_at="2026-07-22T12:00:00Z",
        )
        d = order.to_dict()
        assert d["order_id"] == "ord1"
        assert d["status"] == "filled"

    def test_partial_fill(self):
        order = Order(
            order_id="ord2", symbol="MSFT", side="buy",
            qty=100, filled_qty=50, price=300.0,
            avg_fill_price=300.0, status="partially_filled",
            type="limit", created_at="2026-07-22T12:00:00Z",
        )
        assert order.to_dict()["filled_qty"] == 50


class TestTrade:
    def test_to_dict(self):
        trade = Trade(
            trade_id="t1", symbol="AAPL", side="buy",
            qty=10, price=150.0, realized_pl=50.0,
            commission=1.0, timestamp="2026-07-22T12:00:00Z",
        )
        d = trade.to_dict()
        assert d["trade_id"] == "t1"
        assert d["realized_pl"] == 50.0

    def test_no_pl(self):
        trade = Trade(
            trade_id="t2", symbol="MSFT", side="sell",
            qty=5, price=300.0, realized_pl=None,
            commission=None, timestamp="2026-07-22T12:00:00Z",
        )
        assert trade.to_dict()["realized_pl"] is None
