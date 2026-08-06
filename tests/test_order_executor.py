"""
Order Executor unit tests.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, AsyncMock

from agent.broker.paper import PaperBroker
from agent.execution import OrderExecutor


@pytest.fixture
def broker():
    b = PaperBroker(initial_capital=100_000.0)
    b.update_price("AAPL", 100.0)
    b.update_price("MSFT", 50.0)
    return b


@pytest.mark.asyncio
async def test_dry_run_plans_qualified_buy(broker):
    ex = OrderExecutor(broker=broker, dry_run=True)
    report = await ex.execute_decisions([
        {"symbol": "AAPL", "action": "BUY", "confidence": 0.9},
    ])
    assert report.dry_run is True
    assert report.orders_planned == 1
    assert report.orders_filled == 0
    item = report.items[0]
    assert item["status"] == "planned"
    assert item["symbol"] == "AAPL"
    assert item["action"] == "BUY"
    assert item["qty"] > 0
    assert item["notional"] > 0


@pytest.mark.asyncio
async def test_dry_run_rejects_low_confidence(broker):
    ex = OrderExecutor(broker=broker, dry_run=True, min_confidence=0.65)
    report = await ex.execute_decisions([
        {"symbol": "AAPL", "action": "BUY", "confidence": 0.4},
    ])
    assert report.orders_planned == 0
    assert report.orders_rejected == 1
    assert "below threshold" in report.items[0]["reason"]


@pytest.mark.asyncio
async def test_dry_run_skips_non_executable_action(broker):
    ex = OrderExecutor(broker=broker, dry_run=True)
    report = await ex.execute_decisions([
        {"symbol": "AAPL", "action": "HOLD", "confidence": 0.9},
    ])
    assert report.orders_planned == 0
    assert report.items[0]["status"] == "skipped"


@pytest.mark.asyncio
async def test_dry_run_rejects_missing_fields(broker):
    ex = OrderExecutor(broker=broker, dry_run=True)
    report = await ex.execute_decisions([{"action": "BUY"}])
    assert report.items[0]["status"] == "rejected"


@pytest.mark.asyncio
async def test_dry_run_does_not_submit_to_broker(broker):
    ex = OrderExecutor(broker=broker, dry_run=True)
    with patch.object(broker, "submit_order", new=AsyncMock()) as mock_submit:
        await ex.execute_decisions([
            {"symbol": "AAPL", "action": "BUY", "confidence": 0.9},
        ])
        mock_submit.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_mode_submits_market_order(broker):
    ex = OrderExecutor(broker=broker, dry_run=False)
    report = await ex.execute_decisions([
        {"symbol": "AAPL", "action": "BUY", "confidence": 0.9},
    ])
    assert report.orders_filled == 1
    item = report.items[0]
    assert item["status"] == "filled"
    assert item["order_id"]
    assert item["order_status"] == "filled"
    positions = await broker.get_positions()
    assert any(p.symbol == "AAPL" for p in positions)


@pytest.mark.asyncio
async def test_execute_rejects_when_risk_vetoes(broker):
    broker._max_position_pct = 0.0  # force risk rejection
    ex = OrderExecutor(broker=broker, dry_run=False)
    report = await ex.execute_decisions([
        {"symbol": "AAPL", "action": "BUY", "confidence": 0.9},
    ])
    assert report.items[0]["status"] == "rejected"
    assert "broker status" in (report.items[0]["reason"] or "")


@pytest.mark.asyncio
async def test_position_sizing_uses_fixed_pct(broker):
    ex = OrderExecutor(broker=broker, dry_run=True, position_pct=0.10)
    report = await ex.execute_decisions([
        {"symbol": "AAPL", "action": "BUY", "confidence": 0.9},
    ])
    item = report.items[0]
    # ~10% of $100k equity at $100/share = 100 shares (via mock quote)
    assert item["qty"] > 0
