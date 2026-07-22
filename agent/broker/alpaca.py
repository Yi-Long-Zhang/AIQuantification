"""
Alpaca Broker Connection

Connects to Alpaca Markets REST API for account info, positions, orders,
and trade history. Supports both paper and live trading environments.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from agent.broker.base import BrokerBase, AccountInfo, Position, Order, Trade

logger = logging.getLogger(__name__)

BASE_URLS = {
    "paper": "https://paper-api.alpaca.markets",
    "live": "https://api.alpaca.markets",
}

DATA_URL = "https://data.alpaca.markets"


class AlpacaBroker(BrokerBase):
    """
    Alpaca Markets broker connection.

    Requires api_key and secret_key in config. Uses paper trading by default.
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(name="alpaca")
        self._api_key = config.get("api_key", "")
        self._secret_key = config.get("secret_key", "")
        paper = config.get("paper", True)
        self._base_url = config.get("base_url") or BASE_URLS["paper" if paper else "live"]
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> bool:
        """Initialize HTTP client and verify credentials."""
        if not self._api_key or not self._secret_key:
            logger.error("Alpaca requires api_key and secret_key")
            return False

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "APCA-API-KEY-ID": self._api_key,
                "APCA-API-SECRET-KEY": self._secret_key,
            },
            timeout=10,
        )

        # Verify credentials by fetching account
        try:
            resp = await self._client.get("/v2/account")
            if resp.status_code == 401:
                logger.error("Alpaca authentication failed: invalid API keys")
                await self._client.aclose()
                self._client = None
                return False
            resp.raise_for_status()
            self._connected = True
            logger.info("Alpaca connected successfully")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Alpaca connection failed: {e}")
            await self._client.aclose()
            self._client = None
            return False

    async def disconnect(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False

    # ── Internal helpers ────────────────────────────────────────────────

    def _require_client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError("Alpaca not connected. Call connect() first.")
        return self._client

    async def _get(self, path: str) -> Any:
        client = self._require_client()
        resp = await client.get(path)
        resp.raise_for_status()
        return resp.json()

    # ── Account ─────────────────────────────────────────────────────────

    async def get_account(self) -> AccountInfo:
        data = await self._get("/v2/account")
        return AccountInfo(
            broker="alpaca",
            account_id=data.get("id", ""),
            cash=float(data.get("cash", 0)),
            equity=float(data.get("equity", 0)),
            buying_power=float(data.get("buying_power", 0)),
            currency=data.get("currency", "USD"),
            status=data.get("status", "ACTIVE"),
        )

    async def get_positions(self) -> list[Position]:
        data = await self._get("/v2/positions")
        positions = []
        for item in data:
            qty = float(item.get("qty", 0))
            avg_entry = float(item.get("avg_entry_price", 0))
            current = float(item.get("current_price", 0))
            market_value = float(item.get("market_value", 0))
            unrealized_pl = float(item.get("unrealized_pl", 0))
            unrealized_pl_pct = float(item.get("unrealized_plpc", 0)) * 100
            positions.append(Position(
                symbol=item.get("symbol", ""),
                qty=qty,
                avg_entry_price=avg_entry,
                current_price=current,
                market_value=market_value,
                unrealized_pl=unrealized_pl,
                unrealized_pl_pct=unrealized_pl_pct,
                asset_class=item.get("asset_class", "us_equity"),
            ))
        return positions

    async def get_orders(self, status: str | None = None) -> list[Order]:
        params = {"limit": 50, "sort": "desc"}
        if status:
            params["status"] = status
        client = self._require_client()
        resp = await client.get("/v2/orders", params=params)
        resp.raise_for_status()
        data = resp.json()
        orders = []
        for item in data:
            orders.append(Order(
                order_id=item.get("id", ""),
                symbol=item.get("symbol", ""),
                side=item.get("side", ""),
                qty=float(item.get("qty", 0)),
                filled_qty=float(item.get("filled_qty", 0)),
                price=float(item["limit_price"]) if item.get("limit_price") else None,
                avg_fill_price=float(item["filled_avg_price"]) if item.get("filled_avg_price") else None,
                status=item.get("status", ""),
                type=item.get("type", ""),
                created_at=item.get("created_at", ""),
            ))
        return orders

    async def get_trades(self, limit: int = 100) -> list[Trade]:
        """Get recent fills from account activities."""
        data = await self._get(f"/v2/account/activities?activity_types=FILL&limit={limit}")
        trades = []
        for item in data:
            trades.append(Trade(
                trade_id=item.get("id", ""),
                symbol=item.get("symbol", ""),
                side=item.get("side", ""),
                qty=float(item.get("qty", 0)),
                price=float(item.get("price", 0)),
                realized_pl=float(item["realized_pl"]) if item.get("realized_pl") else None,
                commission=float(item["commission"]) if item.get("commission") else None,
                timestamp=item.get("transaction_time", ""),
            ))
        return trades
