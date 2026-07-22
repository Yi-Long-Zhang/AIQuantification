"""
IBKR (Interactive Brokers) Connection

Connects to TWS or IB Gateway via the ib_insync library.
Operates in read-only mode by default.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from agent.broker.base import BrokerBase, AccountInfo, Position, Order, Trade

logger = logging.getLogger(__name__)

# Lazy import for optional dependency
_ib_insync = None


def _get_ib():  # pragma: no cover
    global _ib_insync
    if _ib_insync is None:
        try:
            import ib_insync as _ib_insync
        except ImportError:
            raise ImportError(
                "ib_insync is required for IBKR connection. "
                "Install with: uv pip install ib_insync"
            )
    return _ib_insync


class IBRKBroker(BrokerBase):
    """
    Interactive Brokers connection via TWS/IB Gateway.

    Config:
        host: str = "127.0.0.1"
        port: int = 7497 (TWS paper) / 4001 (IB Gateway) / 7496 (TWS live)
        client_id: int = 1
        readonly: bool = True
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(name="ibkr")
        self._host = config.get("host", "127.0.0.1")
        self._port = int(config.get("port", 7497))
        self._client_id = int(config.get("client_id", 1))
        self._readonly = config.get("readonly", True)
        self._ib = None

    async def connect(self) -> bool:
        """Connect to TWS/IB Gateway via ib_insync."""
        ib = _get_ib()
        self._ib = ib.IB()
        try:
            await self._ib.connectAsync(
                host=self._host,
                port=self._port,
                clientId=self._client_id,
                readonly=self._readonly,
            )
            self._connected = True
            logger.info(f"IBKR connected to {self._host}:{self._port}")
            return True
        except Exception as e:
            logger.error(f"IBKR connection failed: {e}")
            self._ib = None
            return False

    async def disconnect(self) -> None:
        if self._ib:
            self._ib.disconnect()
            self._ib = None
        self._connected = False

    # ── Internal helpers ────────────────────────────────────────────────

    def _require_ib(self):
        if not self._ib or not self._connected:
            raise RuntimeError("IBKR not connected. Call connect() first.")
        return self._ib

    # ── Account ─────────────────────────────────────────────────────────

    async def get_account(self) -> AccountInfo:
        ib = self._require_ib()
        account_values = ib.accountSummary(account="ALL")
        cash = 0.0
        equity = 0.0
        buying_power = 0.0
        account_id = ""
        for av in account_values:
            if av.tag == "TotalCashValue":
                cash = float(av.value)
            elif av.tag == "NetLiquidation":
                equity = float(av.value)
            elif av.tag == "BuyingPower":
                buying_power = float(av.value)
            elif av.tag == "AccountType":
                account_id = av.value
        return AccountInfo(
            broker="ibkr",
            account_id=account_id,
            cash=cash,
            equity=equity,
            buying_power=buying_power,
            currency="USD",
            status="ACTIVE" if equity > 0 else "UNKNOWN",
        )

    async def get_positions(self) -> list[Position]:
        ib = self._require_ib()
        ib_positions = ib.positions()
        positions = []
        for pos in ib_positions:
            contract = pos.contract
            ticker = ib.reqMktData(contract, "", False, False)
            await ib.sleepAsync(0.1)  # Allow time for tick data
            current_price = ticker.marketPrice() or 0.0
            market_value = pos.position * current_price
            avg_cost = pos.avgCost or 0.0
            unrealized_pl = (current_price - avg_cost) * pos.position if avg_cost else 0.0
            unrealized_pl_pct = ((current_price / avg_cost) - 1) * 100 if avg_cost else 0.0
            positions.append(Position(
                symbol=contract.symbol,
                qty=float(pos.position),
                avg_entry_price=float(avg_cost),
                current_price=float(current_price),
                market_value=float(market_value),
                unrealized_pl=float(unrealized_pl),
                unrealized_pl_pct=float(unrealized_pl_pct),
                asset_class=contract.secType or "STK",
            ))
        return positions

    async def get_orders(self, status: str | None = None) -> list[Order]:
        ib = self._require_ib()
        ib_orders = ib.openOrders() if status == "open" else ib.reqAllOpenOrders()
        orders = []
        for o in ib_orders:
            order = o.order
            contract = o.contract
            orders.append(Order(
                order_id=str(order.orderId),
                symbol=contract.symbol,
                side="buy" if order.action == "BUY" else "sell",
                qty=float(order.totalQuantity),
                filled_qty=float(order.filledQuantity),
                price=float(order.lmtPrice) if order.lmtPrice else None,
                avg_fill_price=float(order.avgFillPrice) if order.avgFillPrice else None,
                status=order.status,
                type=order.orderType.lower(),
                created_at=datetime.now().isoformat(),
            ))
        return orders

    async def get_trades(self, limit: int = 100) -> list[Trade]:
        """Get filled trades from executions."""
        ib = self._require_ib()
        # Fetch last N days of executions
        from ib_insync import util
        end = datetime.now()
        start = end.replace(day=max(1, end.day - 7))
        fills = ib.executions(util.days_to_ib_time_period(7))
        trades = []
        for fill in fills[-limit:]:
            exec_data = fill.execution
            trade = Trade(
                trade_id=str(exec_data.execId),
                symbol=exec_data.symbol or fill.contract.symbol,
                side=exec_data.side.lower(),
                qty=float(exec_data.shares),
                price=float(exec_data.price),
                realized_pl=float(exec_data.realizedPnL) if hasattr(exec_data, 'realizedPnL') else None,
                commission=float(exec_data.commission) if hasattr(exec_data, 'commission') else None,
                timestamp=str(exec_data.time),
            )
            trades.append(trade)
        return trades
