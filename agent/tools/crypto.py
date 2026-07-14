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


@tool(
    name="get_crypto_fear_greed",
    description="获取加密货币恐惧贪婪指数（历史数据）",
    parameters={
        "days": {"type": "integer", "description": "历史天数，默认30", "default": 30},
    },
)
async def get_crypto_fear_greed(days: int = 30) -> dict:
    try:
        import httpx

        def _fetch():
            resp = httpx.get(f"https://api.alternative.me/fng/?limit={days}", timeout=10)
            data = resp.json()
            if not data.get("data"):
                return {"error": "No data available"}
            records = []
            for item in data["data"]:
                records.append({
                    "date": item.get("timestamp"),
                    "value": int(item.get("value", 50)),
                    "classification": item.get("value_classification", "Neutral"),
                })
            return {
                "current": records[0] if records else None,
                "history": records,
                "average_30d": round(sum(r["value"] for r in records) / len(records), 1) if records else None,
            }

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="get_crypto_top_coins",
    description="获取加密货币市值 Top N 排名",
    parameters={
        "top_n": {"type": "integer", "description": "返回数量，默认20", "default": 20},
    },
)
async def get_crypto_top_coins(top_n: int = 20) -> dict:
    try:
        from pycoingecko import CoinGeckoAPI

        def _fetch():
            cg = CoinGeckoAPI()
            coins = cg.get_coins_markets(
                vs_currency="usd",
                per_page=min(top_n, 100),
                order="market_cap_desc",
                price_change_percentage="1h,24h,7d",
            )
            result = []
            for i, c in enumerate(coins or []):
                result.append({
                    "rank": i + 1,
                    "symbol": c["symbol"].upper(),
                    "name": c["name"],
                    "price": c["current_price"],
                    "market_cap": c["market_cap"],
                    "market_cap_rank": c.get("market_cap_rank"),
                    "volume_24h": c.get("total_volume"),
                    "change_1h": c.get("price_change_percentage_1h_in_currency"),
                    "change_24h": c.get("price_change_percentage_24h_in_currency"),
                    "change_7d": c.get("price_change_percentage_7d_in_currency"),
                    "ath": c.get("ath"),
                    "ath_change_pct": c.get("ath_change_percentage"),
                    "circulating_supply": c.get("circulating_supply"),
                })
            return {"coins": result, "count": len(result)}

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="get_crypto_funding_rate",
    description="获取加密货币永续合约资金费率",
    parameters={
        "symbol": {"type": "string", "description": "交易对，如 BTC、ETH"},
        "exchange": {"type": "string", "description": "交易所: binance, okx, bybit", "default": "binance"},
    },
)
async def get_crypto_funding_rate(symbol: str, exchange: str = "binance") -> dict:
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
            funding = ex.fetch_funding_rate(pair)
            return {
                "symbol": symbol,
                "exchange": exchange,
                "funding_rate": funding.get("fundingRate"),
                "funding_timestamp": funding.get("fundingTimestamp"),
                "next_funding_rate": funding.get("nextFundingRate"),
                "next_funding_timestamp": funding.get("nextFundingTimestamp"),
            }

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="get_crypto_open_interest",
    description="获取加密货币合约持仓量",
    parameters={
        "symbol": {"type": "string", "description": "交易对，如 BTC、ETH"},
        "exchange": {"type": "string", "description": "交易所: binance, okx, bybit", "default": "binance"},
    },
)
async def get_crypto_open_interest(symbol: str, exchange: str = "binance") -> dict:
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
            oi = ex.fetch_open_interest(pair)
            return {
                "symbol": symbol,
                "exchange": exchange,
                "open_interest": oi.get("openInterestAmount"),
                "open_interest_value": oi.get("openInterestValue"),
                "timestamp": oi.get("timestamp"),
            }

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="calculate_crypto_indicators",
    description="计算加密货币链上指标（MVRV/NVT/NUPL）",
    parameters={
        "symbol": {"type": "string", "description": "币种代码，如 BTC、ETH"},
    },
)
async def calculate_crypto_indicators(symbol: str) -> dict:
    try:
        from pycoingecko import CoinGeckoAPI

        def _fetch():
            cg = CoinGeckoAPI()
            coin = symbol.upper().replace("-USD", "").replace("/USDT", "")
            coin_id_map = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
                            "BNB": "binancecoin", "XRP": "ripple", "DOGE": "dogecoin"}
            coin_id = coin_id_map.get(coin, coin.lower())

            market = cg.get_coin_market_chart_by_id(id=coin_id, vs_currency="usd", days=365)
            prices = market.get("prices", [])
            volumes = market.get("total_volumes", [])

            if not prices or not volumes:
                return {"error": "Insufficient data"}

            df = pd.DataFrame(prices, columns=["timestamp", "price"])
            df["volume"] = [v[1] for v in volumes]
            df["date"] = pd.to_datetime(df["timestamp"], unit="ms")

            current_price = df["price"].iloc[-1]
            avg_price_200d = df["price"].tail(200).mean() if len(df) >= 200 else df["price"].mean()
            avg_volume = df["volume"].tail(30).mean()

            mvrv = current_price / avg_price_200d if avg_price_200d > 0 else None
            nvt = current_price / (avg_volume / 1e9) if avg_volume > 0 else None

            returns = df["price"].pct_change().dropna()
            volatility_30d = returns.tail(30).std() * (365 ** 0.5) * 100

            return {
                "symbol": symbol,
                "current_price": round(current_price, 2),
                "mvrv_ratio": round(mvrv, 4) if mvrv else None,
                "nvt_ratio": round(nvt, 2) if nvt else None,
                "volatility_30d_pct": round(volatility_30d, 2),
                "avg_price_200d": round(avg_price_200d, 2),
                "price_vs_avg_200d_pct": round((current_price / avg_price_200d - 1) * 100, 2) if avg_price_200d > 0 else None,
                "interpretation": {
                    "mvrv": "overvalued" if mvrv and mvrv > 3.5 else "undervalued" if mvrv and mvrv < 1.0 else "fair",
                    "volatility": "high" if volatility_30d > 80 else "medium" if volatility_30d > 40 else "low",
                },
            }

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        return {"error": str(e)}
