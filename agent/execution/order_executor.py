"""
Order Executor — Turn final trading decisions into broker orders.

Filters decisions by action and confidence, fetches current prices into the
broker price feed, sizes positions with a fixed equity percentage, and either
previews orders (dry-run) or submits them to the broker.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from agent.broker.base import BrokerBase, Order

logger = logging.getLogger(__name__)

# ── Execution constants ─────────────────────────────────────────────────────

MIN_CONFIDENCE: float = 0.65     # Matches coordinator prompt execution threshold
POSITION_PCT: float = 0.10       # Fixed fraction of portfolio equity per signal
EXECUTABLE_ACTIONS: set[str] = {"BUY", "SELL"}
SUPPORTED_MARKETS: set[str] = {"us_stock", "cn_stock", "hk_stock", "crypto"}


@dataclass
class ExecutionReport:
    """Result of an execution pass over a set of decisions."""

    dry_run: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    decisions_seen: int = 0
    orders_planned: int = 0
    orders_filled: int = 0
    orders_rejected: int = 0
    items: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dry_run": self.dry_run,
            "timestamp": self.timestamp,
            "decisions_seen": self.decisions_seen,
            "orders_planned": self.orders_planned,
            "orders_filled": self.orders_filled,
            "orders_rejected": self.orders_rejected,
            "items": self.items,
        }


class OrderExecutor:
    """Converts decisions to orders against a broker instance."""

    def __init__(
        self,
        broker: BrokerBase,
        dry_run: bool = True,
        min_confidence: float = MIN_CONFIDENCE,
        position_pct: float = POSITION_PCT,
        market: str = "us_stock",
    ):
        self._broker = broker
        self._dry_run = dry_run
        self._min_confidence = min_confidence
        self._position_pct = position_pct
        self._market = market

    async def execute_decisions(self, decisions: list[dict]) -> ExecutionReport:
        """Process a list of decisions and produce an execution report."""
        report = ExecutionReport(dry_run=self._dry_run)
        report.decisions_seen = len(decisions)

        for decision in decisions:
            item = await self._process_decision(decision)
            report.items.append(item)
            if item["status"] == "planned":
                report.orders_planned += 1
            elif item["status"] == "filled":
                report.orders_filled += 1
            elif item["status"] == "rejected":
                report.orders_rejected += 1

        return report

    async def _process_decision(self, decision: dict) -> dict:
        """Validate, size, and execute a single decision."""
        symbol = decision.get("symbol")
        action = (decision.get("action") or "").upper()
        confidence = float(decision.get("confidence") or 0.0)

        if not symbol or not action:
            return {"status": "rejected", "reason": "missing symbol or action", "symbol": symbol}
        if action not in EXECUTABLE_ACTIONS:
            return {"status": "skipped", "reason": f"action {action} not executable", "symbol": symbol}
        if confidence < self._min_confidence:
            return {
                "status": "rejected",
                "reason": f"confidence {confidence:.2f} below threshold {self._min_confidence:.2f}",
                "symbol": symbol,
                "action": action,
                "confidence": confidence,
            }

        price = await self._ensure_price(symbol)
        if not price:
            return {"status": "rejected", "reason": "no price available", "symbol": symbol, "action": action}

        equity = await self._portfolio_equity()
        qty = self._compute_qty(price, equity)
        if qty <= 0:
            return {
                "status": "rejected", "reason": "position size is zero",
                "symbol": symbol, "action": action, "price": price,
            }

        if self._dry_run:
            return {
                "status": "planned",
                "symbol": symbol,
                "action": action,
                "confidence": confidence,
                "price": price,
                "qty": qty,
                "notional": round(qty * price, 2),
            }

        order = await self._submit(symbol, action, qty)
        return {
            "status": "filled" if order.status == "filled" else "rejected",
            "symbol": symbol,
            "action": action,
            "confidence": confidence,
            "price": price,
            "qty": qty,
            "order_id": order.order_id,
            "order_status": order.status,
            "reason": None if order.status == "filled" else f"broker status: {order.status}",
        }

    async def _ensure_price(self, symbol: str) -> float | None:
        """Fetch current price and push it into the broker price feed."""
        from agent.tools.market_data import get_stock_quote

        try:
            quote = await get_stock_quote(symbol, market=self._market)
        except Exception as e:
            logger.warning("Quote fetch failed for %s: %s", symbol, e)
            quote = {}
        price = quote.get("price") or quote.get("last")

        update_price = getattr(self._broker, "update_price", None)
        if price and callable(update_price):
            update_price(symbol, float(price))
        return float(price) if price else None

    async def _portfolio_equity(self) -> float:
        """Return current portfolio equity for position sizing."""
        summary = getattr(self._broker, "get_portfolio_summary", None)
        if callable(summary):
            data = summary()
            equity = data.get("equity")
            if equity:
                return float(equity)
        account = getattr(self._broker, "get_account", None)
        if callable(account):
            info = await account()
            if getattr(info, "equity", None):
                return float(info.equity)
        return 100_000.0

    def _compute_qty(self, price: float, equity: float) -> int:
        """Fixed-percentage position sizing."""
        return int(equity * self._position_pct / price)

    async def _submit(self, symbol: str, action: str, qty: int) -> Order:
        side = "buy" if action == "BUY" else "sell"
        return await self._broker.submit_order(symbol=symbol, side=side, qty=qty, order_type="market")
