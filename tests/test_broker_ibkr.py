"""
IBKR broker connection tests (mocked ib_insync).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.broker.ibkr import IBRKBroker


def broker(config: dict | None = None) -> IBRKBroker:
    cfg = config or {
        "host": "127.0.0.1",
        "port": 7497,
        "client_id": 1,
        "readonly": True,
    }
    return IBRKBroker(cfg)


class MockIBKR:
    """Simulates ib_insync.IB() for testing."""

    def __init__(self):
        self.connected = False

    async def connectAsync(self, host="", port=0, clientId=0, readonly=False):
        self.connected = True
        return self

    def disconnect(self):
        self.connected = False

    # Account summary mock
    def accountSummary(self, account: str = "ALL"):
        from collections import namedtuple
        AV = namedtuple("AccountValue", ["tag", "value"])
        return [
            AV("TotalCashValue", "100000.0"),
            AV("NetLiquidation", "110000.0"),
            AV("BuyingPower", "200000.0"),
            AV("AccountType", "DU1234567"),
        ]

    # Positions mock
    def positions(self):
        from collections import namedtuple
        Contract = namedtuple("Contract", ["symbol", "secType"])
        Position = namedtuple("Position", ["contract", "position", "avgCost"])
        return [
            Position(Contract("AAPL", "STK"), 10, 150.0),
            Position(Contract("MSFT", "STK"), 5, 300.0),
        ]

    # Market data mock
    def reqMktData(self, contract, generic=None, snap=False, regulatory=False):
        ticker = MagicMock()
        ticker.marketPrice.return_value = 160.0
        return ticker

    async def sleepAsync(self, seconds):
        pass

    # Orders mock
    def openOrders(self):
        return []

    def reqAllOpenOrders(self):
        from collections import namedtuple
        Contract = namedtuple("Contract", ["symbol", "secType"])
        OrderData = namedtuple("OrderData", ["orderId", "action", "totalQuantity",
                                              "filledQuantity", "lmtPrice", "avgFillPrice",
                                              "status", "orderType"])
        Order = namedtuple("Order", ["contract", "order"])
        od = OrderData(1, "BUY", 100, 0, 150.0, None, "Submitted", "LMT")
        return [Order(Contract("AAPL", "STK"), od)]

    # Executions mock
    def executions(self, time_period):
        from collections import namedtuple
        ExecData = namedtuple("ExecData", ["execId", "symbol", "side", "shares",
                                            "price", "time"])
        Fill = namedtuple("Fill", ["execution", "contract"])
        ed = ExecData("e1", "AAPL", "BUY", 10, 150.0, "2026-07-22T12:00:00Z")
        contract = namedtuple("Contract", ["symbol"])(symbol="AAPL")
        return [Fill(ed, contract)]


@pytest.fixture
def mock_ib():
    """Patch the _get_ib function and ib_insync module so it returns mock ib_insync module."""
    mock_module = MagicMock()
    mock_module.IB = MagicMock(return_value=MockIBKR())
    mock_module.util = MagicMock()
    mock_module.util.days_to_ib_time_period = MagicMock(return_value="7 D")

    with patch("agent.broker.ibkr._get_ib", return_value=mock_module):
        with patch.dict("sys.modules", {"ib_insync": mock_module, "ib_insync.util": mock_module.util}):
            yield


class TestIBRKConnect:
    @pytest.mark.asyncio
    async def test_connect_success(self, mock_ib):
        b = broker()
        result = await b.connect()
        assert result is True
        assert b.is_connected is True
        await b.disconnect()

    @pytest.mark.asyncio
    async def test_connect_failure(self, mock_ib):
        b = broker()
        # Replace the ib_insync module's IB with a failing one
        failing_module = MagicMock()
        failing_ib = MagicMock()
        failing_ib.connectAsync = AsyncMock(side_effect=Exception("Connection refused"))
        failing_module.IB = MagicMock(return_value=failing_ib)
        with patch("agent.broker.ibkr._get_ib", return_value=failing_module):
            b2 = broker()
            result = await b2.connect()
            assert result is False
            assert b2.is_connected is False

    @pytest.mark.asyncio
    async def test_not_connected_raises(self, mock_ib):
        b = broker()
        with pytest.raises(RuntimeError, match="not connected"):
            await b.get_account()


class TestIBRKAccount:
    @pytest.mark.asyncio
    async def test_get_account(self, mock_ib):
        b = broker()
        await b.connect()
        account = await b.get_account()
        assert account.broker == "ibkr"
        assert account.cash == 100000.0
        assert account.equity == 110000.0
        assert account.buying_power == 200000.0
        await b.disconnect()


class TestIBRKPositions:
    @pytest.mark.asyncio
    async def test_get_positions(self, mock_ib):
        b = broker()
        await b.connect()
        positions = await b.get_positions()
        assert len(positions) == 2
        assert positions[0].symbol == "AAPL"
        assert positions[0].qty == 10.0
        assert positions[1].symbol == "MSFT"
        await b.disconnect()


class TestIBRKOrders:
    @pytest.mark.asyncio
    async def test_get_orders_all(self, mock_ib):
        b = broker()
        await b.connect()
        orders = await b.get_orders()
        assert len(orders) == 1
        assert orders[0].symbol == "AAPL"
        await b.disconnect()

    @pytest.mark.asyncio
    async def test_get_orders_open(self, mock_ib):
        b = broker()
        await b.connect()
        orders = await b.get_orders(status="open")
        assert orders == []
        await b.disconnect()


class TestIBRKTrades:
    @pytest.mark.asyncio
    async def test_get_trades(self, mock_ib):
        b = broker()
        await b.connect()
        trades = await b.get_trades()
        assert len(trades) >= 1
        assert trades[0].symbol == "AAPL"
        await b.disconnect()
