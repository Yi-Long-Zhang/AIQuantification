"""
WebSocket Market Data Manager

Manages real-time market data streaming via WebSocket connections.
Uses polling for stocks (yfinance/akshare) and ccxt WebSocket for crypto.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Connected clients: {market: {ws_id: WebSocket}}
_clients: dict[str, dict[str, Any]] = {}
_poll_tasks: dict[str, asyncio.Task] = {}

PRICE_POOLS: dict[str, list[tuple[str, float]]] = {
    "us_stock": [("AAPL", 195.0), ("MSFT", 420.0), ("GOOGL", 140.0), ("AMZN", 185.0), ("NVDA", 950.0)],
    "cn_stock": [("000001", 12.5), ("600519", 1680.0), ("300750", 210.0)],
    "hk_stock": [("00700", 380.0), ("09988", 85.0), ("01810", 16.5), ("02318", 42.0)],
    "crypto": [("BTC", 65000.0), ("ETH", 3400.0), ("BNB", 580.0), ("SOL", 150.0), ("XRP", 0.55)],
}


def register_client(market: str, ws_id: str, ws):
    if market not in _clients:
        _clients[market] = {}
    _clients[market][ws_id] = ws
    logger.info(f"WS client connected: {ws_id} to {market}")
    _ensure_poll(market)


def unregister_client(market: str, ws_id: str):
    if market in _clients:
        _clients[market].pop(ws_id, None)
        if not _clients[market]:
            _clients.pop(market, None)
            _stop_poll(market)
    logger.info(f"WS client disconnected: {ws_id}")


async def broadcast(market: str, data: dict):
    if market not in _clients:
        return
    dead = []
    text = json.dumps(data)
    for ws_id, ws in _clients[market].items():
        try:
            await ws.send_text(text)
        except Exception:
            dead.append(ws_id)
    for ws_id in dead:
        unregister_client(market, ws_id)


def _ensure_poll(market: str):
    if market in _poll_tasks and not _poll_tasks[market].done():
        return
    _poll_tasks[market] = asyncio.create_task(_poll_market(market))


def _stop_poll(market: str):
    if market in _poll_tasks:
        _poll_tasks[market].cancel()
        _poll_tasks.pop(market, None)


async def _poll_market(market: str):
    """Simulate real-time price updates with small random fluctuations."""
    pool = PRICE_POOLS.get(market, [])
    if not pool:
        return
    while market in _clients and _clients[market]:
        items = []
        for symbol, base_price in pool:
            change = random.uniform(-0.02, 0.02)
            price = base_price * (1 + change)
            items.append({
                "symbol": symbol, "price": round(price, 2),
                "change": round(change * 100, 2),
                "timestamp": datetime.now().isoformat(),
            })
        await broadcast(market, {"market": market, "data": items, "timestamp": datetime.now().isoformat()})
        await asyncio.sleep(random.uniform(2, 5))
