"""
WebSocket Market Data Manager

Manages real-time market data streaming via WebSocket connections.
Fetches real prices from yfinance/ccxt/akshare and pushes to connected clients.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from agent.broker.registry import get_broker_registry

logger = logging.getLogger(__name__)

# Connected clients: {market: {ws_id: WebSocket}}
_clients: dict[str, dict[str, Any]] = {}
_poll_tasks: dict[str, asyncio.Task] = {}

# Default symbols to track per market
DEFAULT_SYMBOLS: dict[str, list[str]] = {
    "us_stock": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
    "cn_stock": ["000001", "600519", "300750"],
    "hk_stock": ["00700", "09988", "01810"],
    "crypto": ["BTC", "ETH", "BNB", "SOL", "XRP"],
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


def _feed_paper_broker(items: list[dict]) -> None:
    """Feed fetched prices to PaperBroker for limit orders and P&L."""
    try:
        registry = get_broker_registry()
        paper = registry.get("paper")
        if paper and hasattr(paper, "update_prices"):
            prices = {item["symbol"]: item["price"] for item in items if "price" in item}
            if prices:
                paper.update_prices(prices)
    except Exception as e:
        logger.debug(f"Failed to feed PaperBroker: {e}")


def _ensure_poll(market: str):
    if market in _poll_tasks and not _poll_tasks[market].done():
        return
    _poll_tasks[market] = asyncio.create_task(_poll_market(market))


def _stop_poll(market: str):
    if market in _poll_tasks:
        _poll_tasks[market].cancel()
        _poll_tasks.pop(market, None)


async def _fetch_prices(market: str, symbols: list[str]) -> list[dict]:
    """Fetch real prices for a market from the appropriate data source."""
    items: list[dict] = []
    now = datetime.now().isoformat()

    try:
        if market == "us_stock":
            import yfinance as yf
            for sym in symbols[:5]:  # Limit to 5 to avoid rate limiting
                try:
                    ticker = yf.Ticker(sym)
                    info = ticker.fast_info
                    price = getattr(info, "last_price", None) or getattr(info, "price", None)
                    prev_close = getattr(info, "previous_close", price)
                    if price:
                        change = ((price - prev_close) / prev_close * 100) if prev_close else 0
                        items.append({
                            "symbol": sym, "price": round(float(price), 2),
                            "change": round(float(change), 2),
                            "timestamp": now,
                        })
                except Exception as e:
                    logger.debug(f"WS fetch {sym} failed: {e}")
                    continue

        elif market == "crypto":
            import ccxt
            ex = ccxt.binance({"enableRateLimit": True})
            for sym in symbols[:5]:
                try:
                    pair = f"{sym}/USDT" if "/" not in sym else sym
                    ticker = ex.fetch_ticker(pair)
                    price = ticker.get("last")
                    change = ticker.get("percentage", 0)
                    if price:
                        items.append({
                            "symbol": sym, "price": round(float(price), 2),
                            "change": round(float(change), 2),
                            "timestamp": now,
                        })
                except Exception as e:
                    logger.debug(f"WS fetch crypto {sym} failed: {e}")
                    continue

        elif market == "cn_stock":
            import akshare as ak
            for sym in symbols[:3]:
                try:
                    df = ak.stock_zh_a_spot_em()
                    row = df[df["代码"] == sym]
                    if not row.empty:
                        price = float(row.iloc[0]["最新价"])
                        change = float(row.iloc[0]["涨跌幅"])
                        items.append({
                            "symbol": sym, "price": round(price, 2),
                            "change": round(change, 2),
                            "timestamp": now,
                        })
                except Exception as e:
                    logger.debug(f"WS fetch cn {sym} failed: {e}")
                    continue

        elif market == "hk_stock":
            import akshare as ak
            try:
                df = ak.stock_hk_spot_em()
                for sym in symbols[:4]:
                    row = df[df["代码"] == sym]
                    if not row.empty:
                        price = float(row.iloc[0]["最新价"])
                        change = float(row.iloc[0]["涨跌幅"])
                        items.append({
                            "symbol": sym, "price": round(price, 2),
                            "change": round(change, 2),
                            "timestamp": now,
                        })
            except Exception as e:
                logger.debug(f"WS fetch hk failed: {e}")

    except Exception as e:
        logger.warning(f"WS fetch error for {market}: {e}")

    return items


async def _poll_market(market: str):
    """Fetch real prices and broadcast to connected clients."""
    symbols = DEFAULT_SYMBOLS.get(market, [])
    if not symbols:
        return

    # Different markets have different update intervals
    intervals = {
        "crypto": 15,    # 15 seconds for crypto
        "us_stock": 30,  # 30 seconds for US stocks
        "hk_stock": 30,
        "cn_stock": 60,  # 60 seconds for A-shares (slower data source)
    }
    interval = intervals.get(market, 30)

    while market in _clients and _clients[market]:
        items = await _fetch_prices(market, symbols)
        if items:
            await broadcast(market, {
                "market": market,
                "data": items,
                "timestamp": datetime.now().isoformat(),
            })
            # Feed prices to PaperBroker for limit order checking and P&L
            _feed_paper_broker(items)
        else:
            logger.debug(f"No data fetched for {market}, waiting...")

        await asyncio.sleep(interval)
