"""
Paper Broker — Local simulation account for paper trading.

Maintains a virtual portfolio, executes orders against current market prices,
tracks positions, P&L, and trade history. No real money involved.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .base import BrokerBase, AccountInfo, Position, Order, Trade

logger = logging.getLogger(__name__)


# ── Internal data types ──────────────────────────────────────────────────────

@dataclass
class _PositionState:
    """Internal position tracking."""
    symbol: str
    qty: float = 0.0
    avg_entry_price: float = 0.0
    realized_pnl: float = 0.0

    @property
    def market_value(self, current_price: float) -> float:
        return self.qty * current_price

    @property
    def unrealized_pnl(self, current_price: float) -> float:
        return self.qty * (current_price - self.avg_entry_price)


@dataclass
class _FillEvent:
    """Record of a filled order."""
    order_id: str
    symbol: str
    side: str
    qty: float
    price: float
    timestamp: str
    commission: float = 0.0


# ── PaperBroker ──────────────────────────────────────────────────────────────

class PaperBroker(BrokerBase):
    """
    Local paper trading broker with virtual portfolio.

    Features:
    - Virtual cash balance + positions
    - Market orders fill immediately at current price
    - Limit orders wait in order book until price is reached
    - Tracks realized/unrealized P&L
    - Full order and trade history
    - Configurable initial capital, commission, slippage
    """

    def __init__(
        self,
        name: str = "paper",
        initial_capital: float = 100_000.0,
        commission_pct: float = 0.001,  # 0.1% per trade
        slippage_pct: float = 0.001,   # 0.1% slippage on market orders
    ):
        super().__init__(name)
        self._initial_capital = initial_capital
        self._commission_pct = commission_pct
        self._slippage_pct = slippage_pct

        # Virtual portfolio state
        self._cash = initial_capital
        self._positions: dict[str, _PositionState] = {}
        self._orders: list[Order] = []
        self._trades: list[Trade] = []
        self._fills: list[_FillEvent] = []

        # Current market prices (set externally via update_price())
        self._prices: dict[str, float] = {}

        # For limit order book simulation
        self._open_orders: list[Order] = []
        self._connected = True  # Always connected

        logger.info(
            f"PaperBroker initialized: ${initial_capital:,.0f}, "
            f"commission={commission_pct:.1%}, slippage={slippage_pct:.1%}"
        )

    # ── Connection ────────────────────────────────────────────────────────

    async def connect(self) -> bool:
        """Paper broker is always 'connected'."""
        logger.info("PaperBroker: connected (virtual)")
        return True

    # ── Price feed ────────────────────────────────────────────────────────

    def update_price(self, symbol: str, price: float) -> None:
        """Update current market price for a symbol.

        This should be called by the data pipeline whenever new prices arrive.
        Triggers limit order checks automatically.
        """
        old_price = self._prices.get(symbol)
        self._prices[symbol] = price
        if old_price is not None and old_price != price:
            self._check_limit_orders(symbol)

    def update_prices(self, prices: dict[str, float]) -> None:
        """Batch update multiple prices. More efficient for bulk updates."""
        for symbol, price in prices.items():
            self._prices[symbol] = price
        for symbol in prices:
            self._check_limit_orders(symbol)

    def get_price(self, symbol: str) -> float | None:
        """Get current price for a symbol."""
        return self._prices.get(symbol)

    # ── Account ──────────────────────────────────────────────────────────

    async def get_account(self) -> AccountInfo:
        total_equity = self._cash + self._unrealized_pnl()
        return AccountInfo(
            broker=self.name,
            account_id="paper-001",
            cash=self._cash,
            equity=total_equity,
            buying_power=self._cash * 2,  # 2x leverage for margin simulation
            currency="USD",
            status="ACTIVE",
            timestamp=datetime.now().isoformat(),
        )

    async def get_positions(self) -> list[Position]:
        result = []
        for sym, pos in self._positions.items():
            price = self._prices.get(sym, pos.avg_entry_price)
            result.append(Position(
                symbol=sym,
                qty=pos.qty,
                avg_entry_price=pos.avg_entry_price,
                current_price=price,
                market_value=pos.market_value(price),
                unrealized_pl=pos.unrealized_pnl(price),
                unrealized_pl_pct=(pos.unrealized_pnl(price) / (pos.qty * pos.avg_entry_price))
                if pos.qty and pos.avg_entry_price else 0.0,
                asset_class="paper",
            ))
        return result

    async def get_orders(self, status: str | None = None) -> list[Order]:
        if status:
            return [o for o in self._orders if o.status == status]
        return self._orders[:]

    async def get_trades(self, limit: int = 100) -> list[Trade]:
        return self._trades[-limit:]

    # ── Order execution ───────────────────────────────────────────────────

    async def submit_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        order_type: str = "market",
        price: float | None = None,
    ) -> Order:
        order_id = f"paper-{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()

        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            qty=qty,
            filled_qty=0.0,
            price=price,
            avg_fill_price=None,
            status="new",
            type=order_type,
            created_at=now,
        )

        if order_type == "market":
            await self._execute_market_order(order)
        elif order_type == "limit":
            await self._place_limit_order(order)
        else:
            order.status = "cancelled"
            logger.warning(f"Unsupported order type '{order_type}' for {symbol}")

        self._orders.append(order)
        logger.info(
            f"Order {order_id}: {side} {qty} {symbol} @ "
            f"{'market' if order_type == 'market' else price} → {order.status}"
        )
        return order

    async def cancel_order(self, order_id: str) -> bool:
        for order in self._open_orders[:]:
            if order.order_id == order_id:
                order.status = "cancelled"
                self._open_orders.remove(order)
                logger.info(f"Order {order_id} cancelled")
                return True
        logger.warning(f"Order {order_id} not found or already filled")
        return False

    # ── Internal: order execution ────────────────────────────────────────

    async def _execute_market_order(self, order: Order) -> None:
        """Execute a market order immediately."""
        current_price = self._prices.get(order.symbol)
        if current_price is None:
            logger.warning(f"Cannot execute {order.symbol}: no price available")
            order.status = "cancelled"
            return

        # Apply slippage
        slippage = current_price * self._slippage_pct
        if order.side == "buy":
            fill_price = current_price + slippage
        else:
            fill_price = current_price - slippage

        fill_price = round(fill_price, 2)
        commission = round(order.qty * fill_price * self._commission_pct, 2)
        total_cost = order.qty * fill_price + commission

        # Check cash for buy orders
        if order.side == "buy" and total_cost > self._cash:
            logger.warning(
                f"Insufficient cash: need ${total_cost:,.2f}, have ${self._cash:,.2f}"
            )
            order.status = "cancelled"
            return

        # Execute fill
        order.filled_qty = order.qty
        order.avg_fill_price = fill_price
        order.status = "filled"
        now = datetime.now().isoformat()

        self._fills.append(_FillEvent(
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            price=fill_price,
            timestamp=now,
            commission=commission,
        ))

        # Update portfolio
        self._apply_fill(order.symbol, order.side, order.qty, fill_price, commission)

        # Record trade
        self._trades.append(Trade(
            trade_id=f"trade-{uuid.uuid4().hex[:10]}",
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            price=fill_price,
            realized_pl=None,  # Only set on close
            commission=commission,
            timestamp=now,
        ))

    async def _place_limit_order(self, order: Order) -> None:
        """Place a limit order in the order book."""
        current_price = self._prices.get(order.symbol)
        order.status = "open"

        # Check if limit price is immediately fillable
        if current_price and order.price:
            if (order.side == "buy" and order.price >= current_price) or \
               (order.side == "sell" and order.price <= current_price):
                # Immediately fillable
                order.order_type = "limit"
                await self._execute_market_order(order)
                return

        self._open_orders.append(order)

    def _check_limit_orders(self, symbol: str) -> None:
        """Check if any open limit orders can be filled at current price."""
        current_price = self._prices.get(symbol)
        if current_price is None:
            return

        for order in self._open_orders[:]:
            if order.symbol != symbol or order.price is None:
                continue

            fillable = False
            if order.side == "buy" and current_price <= order.price:
                fillable = True
            elif order.side == "sell" and current_price >= order.price:
                fillable = True

            if fillable:
                self._open_orders.remove(order)
                # Reuse execution logic
                import asyncio
                asyncio.ensure_future(self._execute_market_order(order))

    # ── Internal: portfolio management ───────────────────────────────────

    def _apply_fill(
        self,
        symbol: str,
        side: str,
        qty: float,
        price: float,
        commission: float,
    ) -> None:
        """Apply a fill to the virtual portfolio."""
        pos = self._positions.setdefault(symbol, _PositionState(symbol=symbol))

        if side == "buy":
            total_cost = qty * price + commission
            self._cash -= total_cost
            # Update average entry price
            new_total_qty = pos.qty + qty
            pos.avg_entry_price = (
                (pos.qty * pos.avg_entry_price) + (qty * price)
            ) / new_total_qty
            pos.qty = new_total_qty

        else:  # sell
            revenue = qty * price - commission
            self._cash += revenue
            # Calculate realized P&L for the sold shares
            realized = qty * (price - pos.avg_entry_price) - commission
            pos.realized_pnl += realized
            pos.qty -= qty

            if pos.qty <= 0:
                del self._positions[symbol]

            # Record closing trade with P&L
            self._trades.append(Trade(
                trade_id=f"trade-{uuid.uuid4().hex[:10]}",
                symbol=symbol,
                side=side,
                qty=qty,
                price=price,
                realized_pl=round(realized, 2),
                commission=commission,
                timestamp=datetime.now().isoformat(),
            ))

    def _unrealized_pnl(self) -> float:
        """Total unrealized P&L across all positions."""
        total = 0.0
        for sym, pos in self._positions.items():
            price = self._prices.get(sym, pos.avg_entry_price)
            total += pos.unrealized_pnl(price)
        return total

    # ── Portfolio summary ────────────────────────────────────────────────

    def get_portfolio_summary(self) -> dict[str, Any]:
        """Return full portfolio snapshot."""
        total_equity = self._cash + self._unrealized_pnl()
        pos_list = []
        for sym, pos in self._positions.items():
            price = self._prices.get(sym, pos.avg_entry_price)
            pos_list.append({
                "symbol": sym,
                "qty": pos.qty,
                "avg_entry": pos.avg_entry_price,
                "current_price": price,
                "market_value": pos.market_value(price),
                "unrealized_pnl": round(pos.unrealized_pnl(price), 2),
            })

        return {
            "initial_capital": self._initial_capital,
            "cash": round(self._cash, 2),
            "equity": round(total_equity, 2),
            "unrealized_pnl": round(self._unrealized_pnl(), 2),
            "total_realized_pnl": round(
                sum(pos.realized_pnl for pos in self._positions.values()), 2
            ),
            "total_return_pct": round(
                (total_equity - self._initial_capital) / self._initial_capital * 100, 2
            ),
            "positions": pos_list,
            "open_orders": len(self._open_orders),
            "total_trades": len(self._trades),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "connected": self._connected,
            "type": "paper",
            "balance": round(self._cash, 2),
        }
