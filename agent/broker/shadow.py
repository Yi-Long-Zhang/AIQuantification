"""
Shadow Account — Trade Import and Analysis

Import trade history from CSV files and perform P&L analysis.
Combined with broker connections for comprehensive account tracking.
"""

from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ImportedTrade:
    """A single imported trade record."""
    symbol: str
    side: str  # buy / sell
    qty: float
    price: float
    commission: float | None = None
    realized_pl: float | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "manual"

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "qty": self.qty,
            "price": self.price,
            "commission": self.commission,
            "realized_pl": self.realized_pl,
            "timestamp": self.timestamp,
            "source": self.source,
        }


TradeRow = tuple[str, str, float, float, float | None, float | None, str]


def parse_trades_csv(content: str, source: str = "csv") -> list[ImportedTrade]:
    """
    Parse trades from CSV content.

    Expected columns: symbol, side, qty, price[, commission, realized_pl, timestamp]
    Header row is required.
    """
    trades: list[ImportedTrade] = []
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return trades

    header = [h.strip().lower() for h in rows[0]]
    required = {"symbol", "side", "qty", "price"}
    if not required.issubset(header):
        logger.warning(f"CSV missing required columns {required}, got: {header}")
        return trades

    col_map = {col: idx for idx, col in enumerate(header)}

    for row in rows[1:]:
        if len(row) < len(header):
            continue
        try:
            trade = ImportedTrade(
                symbol=row[col_map["symbol"]].strip(),
                side=row[col_map["side"]].strip().lower(),
                qty=float(row[col_map["qty"]]),
                price=float(row[col_map["price"]]),
                commission=float(row[col_map["commission"]]) if "commission" in col_map and row[col_map["commission"]] else None,
                realized_pl=float(row[col_map["realized_pl"]]) if "realized_pl" in col_map and row[col_map["realized_pl"]] else None,
                timestamp=row[col_map["timestamp"]].strip() if "timestamp" in col_map and row[col_map["timestamp"]] else datetime.now().isoformat(),
                source=source,
            )
            trades.append(trade)
        except (ValueError, IndexError) as e:
            logger.warning(f"Skipping invalid row: {row} — {e}")
            continue

    return trades


# ── Analysis ─────────────────────────────────────────────────────────────────

@dataclass
class TradeAnalysis:
    """Aggregated trade analysis results."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pl: float = 0.0
    avg_pl: float = 0.0
    max_win: float = 0.0
    max_loss: float = 0.0
    avg_holding_period_days: float | None = None
    symbol_breakdown: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": self.win_rate,
            "total_pl": self.total_pl,
            "avg_pl": self.avg_pl,
            "max_win": self.max_win,
            "max_loss": self.max_loss,
            "avg_holding_period_days": self.avg_holding_period_days,
            "symbol_breakdown": self.symbol_breakdown,
        }


def analyze_trades(trades: list[ImportedTrade]) -> TradeAnalysis:
    """Analyze a list of trades and return aggregated statistics."""
    analysis = TradeAnalysis()
    if not trades:
        return analysis

    analysis.total_trades = len(trades)
    symbol_data: dict[str, list[float]] = {}
    pl_values: list[float] = []

    for t in trades:
        pl = t.realized_pl if t.realized_pl is not None else 0.0
        pl_values.append(pl)

        if pl > 0:
            analysis.winning_trades += 1
            analysis.max_win = max(analysis.max_win, pl)
        elif pl < 0:
            analysis.losing_trades += 1
            analysis.max_loss = min(analysis.max_loss, pl)

        if t.symbol not in symbol_data:
            symbol_data[t.symbol] = []
        symbol_data[t.symbol].append(pl)

    analysis.total_pl = sum(pl_values)
    analysis.avg_pl = analysis.total_pl / analysis.total_trades if analysis.total_trades else 0.0
    analysis.win_rate = round(analysis.winning_trades / analysis.total_trades, 4) if analysis.total_trades else 0.0

    # Symbol breakdown
    for symbol, pls in symbol_data.items():
        analysis.symbol_breakdown[symbol] = {
            "trades": len(pls),
            "total_pl": round(sum(pls), 2),
            "avg_pl": round(sum(pls) / len(pls), 2) if pls else 0.0,
            "win_rate": round(sum(1 for p in pls if p > 0) / len(pls), 4) if pls else 0.0,
        }

    return analysis
