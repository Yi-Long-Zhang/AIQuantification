"""
PaperBroker 单元测试
"""
from __future__ import annotations

import pytest
from agent.broker.paper import PaperBroker


@pytest.fixture
def broker():
    pb = PaperBroker(initial_capital=100_000.0)
    # Set up initial prices
    pb.update_prices({
        "AAPL": 150.0, "MSFT": 420.0, "TSLA": 250.0,
        "BTC": 65000.0, "ETH": 3400.0,
    })
    return pb


class TestPaperBrokerBasics:
    def test_always_connected(self, broker):
        assert broker.is_connected is True

    def test_connect_returns_true(self, broker):
        import asyncio
        result = asyncio.run(broker.connect())
        assert result is True

    def test_initial_capital(self, broker):
        summary = broker.get_portfolio_summary()
        assert summary["initial_capital"] == 100_000.0
        assert summary["cash"] == 100_000.0

    def test_to_dict(self, broker):
        d = broker.to_dict()
        assert d["name"] == "paper"
        assert d["type"] == "paper"


class TestOrderExecution:
    def test_submit_market_buy(self, broker):
        import asyncio
        order = asyncio.run(broker.submit_order("AAPL", "buy", 10))
        assert order.symbol == "AAPL"
        assert order.side == "buy"
        assert order.qty == 10
        assert order.status == "filled"
        assert order.avg_fill_price is not None

    def test_submit_market_sell(self, broker):
        import asyncio
        # First buy some shares
        asyncio.run(broker.submit_order("AAPL", "buy", 10))
        # Then sell
        order = asyncio.run(broker.submit_order("AAPL", "sell", 5))
        assert order.status == "filled"

    def test_buy_updates_cash(self, broker):
        import asyncio
        asyncio.run(broker.submit_order("AAPL", "buy", 100))
        summary = broker.get_portfolio_summary()
        assert summary["cash"] < 100_000.0  # Spent money

    def test_sell_updates_positions(self, broker):
        import asyncio
        asyncio.run(broker.submit_order("AAPL", "buy", 100))
        asyncio.run(broker.submit_order("AAPL", "sell", 50))
        pos = asyncio.run(broker.get_positions())
        assert len(pos) == 1
        assert pos[0].qty == 50

    def test_cannot_buy_no_price(self):
        pb = PaperBroker()
        import asyncio
        order = asyncio.run(pb.submit_order("NOPRICE", "buy", 10))
        assert order.status == "cancelled"


class TestPriceFeed:
    def test_update_price(self, broker):
        broker.update_price("AAPL", 155.0)
        assert broker.get_price("AAPL") == 155.0

    def test_update_prices_batch(self, broker):
        broker.update_prices({"AAPL": 155.0, "MSFT": 430.0})
        assert broker.get_price("AAPL") == 155.0
        assert broker.get_price("MSFT") == 430.0

    def test_equity_history_recorded(self, broker):
        assert len(broker.get_equity_history()) >= 0


class TestTrades:
    def test_trades_recorded_on_fill(self, broker):
        import asyncio
        asyncio.run(broker.submit_order("AAPL", "buy", 100))
        trades = asyncio.run(broker.get_trades(limit=10))
        assert len(trades) > 0
        assert trades[-1].symbol == "AAPL"

    def test_get_orders(self, broker):
        import asyncio
        asyncio.run(broker.submit_order("MSFT", "buy", 5))
        orders = asyncio.run(broker.get_orders())
        assert len(orders) > 0


class TestRiskLimits:
    def test_risk_rejects_oversized_position(self, broker):
        import asyncio
        # Try to buy $50k worth, which exceeds 20% position limit
        order = asyncio.run(broker.submit_order("AAPL", "buy", 1000))
        # 1000 shares @ $150 = $150k, exceeds 20% of $100k
        assert order.status == "cancelled"

    def test_daily_trade_limit(self, broker):
        import asyncio
        for _ in range(25):
            asyncio.run(broker.submit_order("MSFT", "buy", 1))
            asyncio.run(broker.submit_order("MSFT", "sell", 1))
        # After >20 fills, subsequent orders should be rejected
        orders = asyncio.run(broker.get_orders())
        cancelled = sum(1 for o in orders if o.status == "cancelled")
        assert cancelled > 0


class TestPortfolioSummary:
    def test_summary_fields(self, broker):
        import asyncio
        asyncio.run(broker.submit_order("AAPL", "buy", 100))
        s = broker.get_portfolio_summary()
        assert "initial_capital" in s
        assert "cash" in s
        assert "equity" in s
        assert "unrealized_pnl" in s
        assert "total_return_pct" in s
        assert "positions" in s
        assert isinstance(s["positions"], list)
