"""
Alpaca broker connection tests (mock HTTP).
"""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from agent.broker.alpaca import AlpacaBroker

BASE = "https://paper-api.alpaca.markets"


def broker(config: dict | None = None) -> AlpacaBroker:
    cfg = config or {
        "api_key": "test-key",
        "secret_key": "test-secret",
        "paper": True,
        "base_url": BASE,
    }
    return AlpacaBroker(cfg)


class TestAlpacaConnect:
    @pytest.mark.asyncio
    @respx.mock
    async def test_connect_success(self):
        respx.get(f"{BASE}/v2/account").return_value = Response(200, json={
            "id": "acct123", "cash": "50000", "equity": "55000",
            "buying_power": "100000", "currency": "USD", "status": "ACTIVE",
        })
        b = broker()
        result = await b.connect()
        assert result is True
        assert b.is_connected is True
        await b.disconnect()

    @pytest.mark.asyncio
    @respx.mock
    async def test_connect_auth_failure(self):
        respx.get(f"{BASE}/v2/account").return_value = Response(401)
        b = broker()
        result = await b.connect()
        assert result is False
        assert b.is_connected is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_connect_network_error(self):
        respx.get(f"{BASE}/v2/account").return_value = Response(503)
        b = broker()
        result = await b.connect()
        assert result is False
        assert b.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_no_credentials(self):
        b = broker({"api_key": "", "secret_key": "", "paper": True, "base_url": BASE})
        result = await b.connect()
        assert result is False


class TestAlpacaAccount:
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_account(self):
        respx.get(f"{BASE}/v2/account").return_value = Response(200, json={
            "id": "acct1", "cash": "100000", "equity": "110000",
            "buying_power": "200000", "currency": "USD", "status": "ACTIVE",
        })
        b = broker()
        await b.connect()
        account = await b.get_account()
        assert account.account_id == "acct1"
        assert account.cash == 100000.0
        assert account.equity == 110000.0
        assert account.buying_power == 200000.0
        assert account.broker == "alpaca"
        await b.disconnect()

    @pytest.mark.asyncio
    async def test_get_account_not_connected(self):
        b = broker()
        with pytest.raises(RuntimeError, match="not connected"):
            await b.get_account()


class TestAlpacaPositions:
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_positions(self):
        respx.get(f"{BASE}/v2/account").return_value = Response(200, json={})
        respx.get(f"{BASE}/v2/positions").return_value = Response(200, json=[
            {"symbol": "AAPL", "qty": "10", "avg_entry_price": "150.0",
             "current_price": "160.0", "market_value": "1600.0",
             "unrealized_pl": "100.0", "unrealized_plpc": "6.67", "asset_class": "us_equity"},
            {"symbol": "MSFT", "qty": "5", "avg_entry_price": "300.0",
             "current_price": "310.0", "market_value": "1550.0",
             "unrealized_pl": "50.0", "unrealized_plpc": "3.33", "asset_class": "us_equity"},
        ])
        b = broker()
        await b.connect()
        positions = await b.get_positions()
        assert len(positions) == 2
        assert positions[0].symbol == "AAPL"
        assert positions[0].qty == 10.0
        assert positions[1].symbol == "MSFT"
        await b.disconnect()

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_positions_empty(self):
        respx.get(f"{BASE}/v2/account").return_value = Response(200, json={})
        respx.get(f"{BASE}/v2/positions").return_value = Response(200, json=[])
        b = broker()
        await b.connect()
        positions = await b.get_positions()
        assert positions == []
        await b.disconnect()


class TestAlpacaOrders:
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_orders(self):
        respx.get(f"{BASE}/v2/account").return_value = Response(200, json={})
        respx.get(f"{BASE}/v2/orders").return_value = Response(200, json=[
            {"id": "ord1", "symbol": "AAPL", "side": "buy", "qty": "100",
             "filled_qty": "100", "limit_price": "150.0", "filled_avg_price": "150.0",
             "status": "filled", "type": "limit", "created_at": "2026-07-22T12:00:00Z"},
        ])
        b = broker()
        await b.connect()
        orders = await b.get_orders()
        assert len(orders) == 1
        assert orders[0].order_id == "ord1"
        await b.disconnect()

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_orders_filter_by_status(self):
        respx.get(f"{BASE}/v2/account").return_value = Response(200, json={})
        respx.get(f"{BASE}/v2/orders").return_value = Response(200, json=[])
        b = broker()
        await b.connect()
        orders = await b.get_orders(status="open")
        assert orders == []
        await b.disconnect()


class TestAlpacaTrades:
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_trades(self):
        respx.get(f"{BASE}/v2/account").return_value = Response(200, json={})
        respx.get(f"{BASE}/v2/account/activities").return_value = Response(200, json=[
            {"id": "t1", "symbol": "AAPL", "side": "sell", "qty": "10",
             "price": "160.0", "realized_pl": "100.0", "commission": "1.0",
             "transaction_time": "2026-07-22T12:00:00Z"},
        ])
        b = broker()
        await b.connect()
        trades = await b.get_trades()
        assert len(trades) == 1
        assert trades[0].trade_id == "t1"
        assert trades[0].realized_pl == 100.0
        await b.disconnect()
