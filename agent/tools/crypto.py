from __future__ import annotations

import asyncio
import logging

import pandas as pd

from .registry import tool
from .market_data import _validate_ohlcv, _df_to_records

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
#  Crypto data sources
# ──────────────────────────────────────────────

async def _ccxt_klines(symbol: str, interval: str, period: str, exchange_id: str = "binance") -> list[dict] | None:
    try:
        import ccxt

        def _fetch():
            exchange_class = getattr(ccxt, exchange_id, None)
            if not exchange_class:
                return None
            exchange = exchange_class({"enableRateLimit": True})
            pair = symbol.upper()
            if "/" not in pair:
                pair = f"{pair}/USDT"
            tf_map = {"1d": "1d", "daily": "1d", "1h": "1h", "4h": "4h", "1wk": "1w", "weekly": "1w"}
            tf = tf_map.get(interval, "1d")
            limit_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730, "5y": 1825, "max": 1825}
            limit = limit_map.get(period, 365)
            ohlcv = exchange.fetch_ohlcv(pair, tf, limit=min(limit, 1000))
            if not ohlcv:
                return None
            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.strftime("%Y-%m-%d")
            df = df.drop(columns=["timestamp"])
            df = _validate_ohlcv(df)
            return _df_to_records(df)

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        logger.warning("ccxt failed for %s: %s", symbol, e)
        return None


async def _yfinance_crypto_klines(symbol: str, interval: str, period: str) -> list[dict] | None:
    try:
        import yfinance as yf

        def _fetch():
            coin = symbol.upper().replace("-USD", "").replace("/USDT", "")
            sym = f"{coin}-USD"
            ticker = yf.Ticker(sym)
            df = ticker.history(period=period, interval=interval)
            if df.empty:
                return None
            df = df.reset_index()
            from .market_data import _normalize_klines_df
            df = _normalize_klines_df(df)
            return _df_to_records(df)

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        logger.warning("yfinance crypto failed for %s: %s", symbol, e)
        return None


async def _coingecko_klines(symbol: str, interval: str, period: str) -> list[dict] | None:
    try:
        from pycoingecko import CoinGeckoAPI

        def _fetch():
            cg = CoinGeckoAPI()
            coin_id_map = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
                            "BNB": "binancecoin", "XRP": "ripple", "DOGE": "dogecoin",
                            "ADA": "cardano", "AVAX": "avalanche-2", "DOT": "polkadot",
                            "MATIC": "matic-network", "LINK": "chainlink", "UNI": "uniswap"}
            coin = symbol.upper().replace("-USD", "").replace("/USDT", "")
            coin_id = coin_id_map.get(coin, coin.lower())
            days_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730, "5y": 1825, "max": "max"}
            days = days_map.get(period, 365)
            chart = cg.get_coin_market_chart_by_id(id=coin_id, vs_currency="usd", days=days)
            prices = chart.get("prices", [])
            if not prices:
                return None
            df = pd.DataFrame(prices, columns=["timestamp", "close"])
            df["date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.strftime("%Y-%m-%d")
            df = df.drop(columns=["timestamp"])
            df["open"] = df["close"]
            df["high"] = df["close"]
            df["low"] = df["close"]
            df["volume"] = 0
            df = df[["date", "open", "high", "low", "close", "volume"]]
            return _df_to_records(df)

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        logger.warning("CoinGecko failed for %s: %s", symbol, e)
        return None


async def _get_crypto_klines_with_fallback(symbol: str, interval: str, period: str, exchange: str = "binance") -> list[dict]:
    result = await _ccxt_klines(symbol, interval, period, exchange)
    if result:
        return result
    result = await _yfinance_crypto_klines(symbol, interval, period)
    if result:
        return result
    result = await _coingecko_klines(symbol, interval, period)
    return result if result else []


# ──────────────────────────────────────────────
#  Crypto tools
# ──────────────────────────────────────────────

@tool(
    name="get_crypto_klines",
    description="获取加密货币K线数据（通过 CCXT，默认 Binance）",
    parameters={
        "symbol": {"type": "string", "description": "交易对，如 BTC、ETH、SOL"},
        "interval": {"type": "string", "description": "周期: 1d, 4h, 1h, 1wk", "default": "1d"},
        "period": {"type": "string", "description": "时期: 1mo, 3mo, 6mo, 1y, 2y", "default": "1y"},
        "exchange": {"type": "string", "description": "交易所: binance, okx, bybit", "default": "binance"},
    },
)
async def get_crypto_klines(symbol: str, interval: str = "1d", period: str = "1y", exchange: str = "binance") -> list:
    result = await _get_crypto_klines_with_fallback(symbol, interval, period, exchange)
    return result if result else []


@tool(
    name="get_crypto_realtime",
    description="获取加密货币实时行情",
    parameters={
        "symbol": {"type": "string", "description": "交易对，如 BTC、ETH"},
        "exchange": {"type": "string", "description": "交易所", "default": "binance"},
    },
)
async def get_crypto_realtime(symbol: str, exchange: str = "binance") -> dict:
    try:
        import ccxt

        def _fetch():
            exchange_class = getattr(ccxt, exchange, None)
            if not exchange_class:
                return {"error": f"Exchange {exchange} not found"}
            ex = exchange_class({"enableRateLimit": True})
            pair = symbol.upper()
            if "/" not in pair:
                pair = f"{pair}/USDT"
            ticker = ex.fetch_ticker(pair)
            return {
                "symbol": symbol, "exchange": exchange,
                "price": ticker.get("last"),
                "bid": ticker.get("bid"), "ask": ticker.get("ask"),
                "change_percent": ticker.get("percentage"),
                "volume_24h": ticker.get("baseVolume"),
                "high_24h": ticker.get("high"), "low_24h": ticker.get("low"),
                "vwap_24h": ticker.get("vwap"),
            }

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="get_crypto_orderbook",
    description="获取加密货币买五卖五盘口",
    parameters={
        "symbol": {"type": "string", "description": "交易对，如 BTC、ETH"},
        "exchange": {"type": "string", "description": "交易所", "default": "binance"},
        "depth": {"type": "integer", "description": "深度档位，默认5", "default": 5},
    },
)
async def get_crypto_orderbook(symbol: str, exchange: str = "binance", depth: int = 5) -> dict:
    try:
        import ccxt

        def _fetch():
            exchange_class = getattr(ccxt, exchange, None)
            if not exchange_class:
                return {"error": f"Exchange {exchange} not found"}
            ex = exchange_class({"enableRateLimit": True})
            pair = symbol.upper()
            if "/" not in pair:
                pair = f"{pair}/USDT"
            ob = ex.fetch_order_book(pair, limit=depth)
            return {
                "symbol": symbol, "exchange": exchange,
                "bids": ob.get("bids", [])[:depth],
                "asks": ob.get("asks", [])[:depth],
                "spread": round(ob["asks"][0][0] - ob["bids"][0][0], 2) if ob.get("asks") and ob.get("bids") else None,
            }

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="get_crypto_overview",
    description="获取加密货币全市场概览（总市值、BTC占比、恐惧贪婪指数）",
    parameters={},
)
async def get_crypto_overview() -> dict:
    try:
        from pycoingecko import CoinGeckoAPI

        def _fetch():
            cg = CoinGeckoAPI()
            global_data = cg.get_global()
            top_coins = cg.get_coins_markets(vs_currency="usd", per_page=10, order="market_cap_desc")
            return {
                "total_market_cap_usd": global_data.get("total_market_cap", {}).get("usd"),
                "total_volume_24h": global_data.get("total_volume", {}).get("usd"),
                "btc_dominance": global_data.get("market_cap_percentage", {}).get("btc"),
                "eth_dominance": global_data.get("market_cap_percentage", {}).get("eth"),
                "active_cryptos": global_data.get("active_cryptocurrencies"),
                "top_10": [
                    {"symbol": c["symbol"].upper(), "name": c["name"],
                     "price": c["current_price"], "market_cap": c["market_cap"],
                     "change_24h": c["price_change_percentage_24h"]}
                    for c in (top_coins or [])
                ],
            }

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        return {"error": str(e)}
