"""
Shadow Account Tool — Import and analyze trade history.

Registers tools for importing CSV trades and analyzing trade performance.
"""

from __future__ import annotations

import logging

from ..tools.registry import tool
from .shadow import parse_trades_csv, analyze_trades, ImportedTrade

logger = logging.getLogger(__name__)


@tool(
    name="import_trades_csv",
    description="从 CSV 导入交易记录并分析",
    parameters={
        "csv_content": {"type": "string", "description": "CSV 内容（列: symbol, side, qty, price[, commission, realized_pl, timestamp]）"},
    },
)
async def import_trades_csv(csv_content: str) -> dict:
    """Import trades from CSV and return analysis results."""
    trades = parse_trades_csv(csv_content)
    if not trades:
        return {"error": "No valid trades found in CSV", "imported": 0}

    analysis = analyze_trades(trades)
    result = analysis.to_dict()
    result["imported"] = len(trades)
    result["sample_trades"] = [t.to_dict() for t in trades[:5]]
    logger.info(f"Imported {len(trades)} trades from CSV")
    return result


@tool(
    name="analyze_trade_performance",
    description="分析交易记录表现（胜率、盈亏、品种分布）",
    parameters={
        "trades_json": {"type": "string", "description": "交易记录 JSON 字符串数组，每项含 symbol/side/qty/price/realized_pl"},
    },
)
async def analyze_trade_performance(trades_json: str) -> dict:
    """Analyze trade performance from a JSON string of trades."""
    import json
    try:
        raw = json.loads(trades_json)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}"}

    trades = []
    for item in raw:
        trades.append(ImportedTrade(
            symbol=item.get("symbol", ""),
            side=item.get("side", "buy"),
            qty=float(item.get("qty", 0)),
            price=float(item.get("price", 0)),
            commission=float(item["commission"]) if item.get("commission") else None,
            realized_pl=float(item["realized_pl"]) if item.get("realized_pl") else None,
            timestamp=item.get("timestamp", ""),
            source="json",
        ))

    if not trades:
        return {"error": "No valid trades in JSON", "imported": 0}

    analysis = analyze_trades(trades)
    result = analysis.to_dict()
    result["imported"] = len(trades)
    return result
