"""
Paper Broker Risk Management Mixin.

Extracted from paper.py to keep files under 500 lines.
"""

from __future__ import annotations

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PaperRiskMixin:
    """Mixin providing risk management methods for PaperBroker."""

    def _check_risk(self, symbol: str, side: str, qty: float, order_type: str) -> str | None:
        """Check all risk limits before order execution.
        Returns error string if rejected, None if approved.
        """
        total_equity = self._cash + self._unrealized_pnl()
        current_price = self._prices.get(symbol, 0)

        # 1. Max daily loss circuit breaker
        daily_pnl = self._daily_pnl()
        if daily_pnl < -self._max_daily_loss_pct * self._initial_capital:
            return f"Daily loss limit reached ({daily_pnl:+.0f} < -{self._max_daily_loss_pct:.0%})"

        # 2. Max daily trade count
        today_trades = sum(1 for t in self._trades if t.timestamp.startswith(datetime.now().strftime("%Y-%m-%d")))
        if today_trades >= self._max_daily_trades:
            return f"Daily trade limit reached ({today_trades}/{self._max_daily_trades})"

        # 3. Max position size per symbol
        if side == "buy" and current_price > 0:
            position_value = qty * current_price
            max_position_value = total_equity * self._max_position_pct
            if position_value > max_position_value:
                return (
                    f"Position size {position_value:+.0f} exceeds {self._max_position_pct:.0%} "
                    f"limit ({max_position_value:+.0f})"
                )

        # 4. Max leverage check
        total_position_value = sum(
            pos.qty * self._prices.get(pos.symbol, pos.avg_entry_price)
            for pos in self._positions.values()
        )
        if side == "buy" and current_price > 0:
            new_total = total_position_value + qty * current_price
        else:
            new_total = total_position_value
        if new_total > total_equity * self._max_leverage:
            return f"Leverage limit exceeded ({new_total / total_equity:.1f}x > {self._max_leverage}x)"

        return None  # Approved

    def _check_daily_reset(self) -> None:
        """Reset daily counters at day boundary."""
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self._current_day:
            total_equity = self._cash + self._unrealized_pnl()
            self._daily_start_equity = total_equity
            self._daily_trade_count = 0
            self._current_day = today
            logger.info(f"Daily risk counters reset (new day: {today}, equity: {total_equity:,.0f})")

    def _daily_pnl(self) -> float:
        """Calculate today's realized P&L."""
        today = datetime.now().strftime("%Y-%m-%d")
        return sum(
            t.realized_pl or 0 for t in self._trades
            if t.timestamp.startswith(today)
        )
