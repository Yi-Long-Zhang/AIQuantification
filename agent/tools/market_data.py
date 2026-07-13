import logging

import pandas as pd

from .registry import tool

logger = logging.getLogger(__name__)


def _get_symbol_in_market(symbol: str, market: str) -> str:
    mapping = {
        "us_stock": lambda s: s,
        "crypto": lambda s: f"{s}-USD" if "-" not in s else s,
        "hk_stock": lambda s: f"{s}.HK" if "." not in s else s,
        "cn_stock": lambda s: s,
        "fund": lambda s: s,
    }
    return mapping.get(market, lambda s: s)(symbol)


def _validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """过滤异常 K 线：最高<最低、价格为负、成交量异常"""
    before = len(df)
    mask = (
        (df["high"] >= df["low"])
        & (df["open"] > 0)
        & (df["close"] > 0)
        & (df["volume"] >= 0)
    )
    df = df[mask]
    dropped = before - len(df)
    if dropped > 0:
        logger.warning("OHLCV validation dropped %d rows", dropped)
    return df


def _normalize_klines_df(df: pd.DataFrame) -> pd.DataFrame:
    """统一列名为英文标准格式"""
    col_map = {
        "日期": "date", "开盘": "open", "收盘": "close",
        "最高": "high", "最低": "low", "成交量": "volume",
        "成交额": "turnover", "振幅": "amplitude",
        "涨跌幅": "change_pct", "涨跌额": "change", "换手率": "turnover_rate",
        "Date": "date", "Open": "open", "Close": "close",
        "High": "high", "Low": "low", "Volume": "volume",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    return df


def _df_to_records(df: pd.DataFrame, max_rows: int = 500) -> list[dict]:
    """DataFrame 转 dict list，日期格式化"""
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df.tail(max_rows).to_dict(orient="records")


# ──────────────────────────────────────────────
#  US Stock (yfinance)
# ──────────────────────────────────────────────

async def _yfinance_klines(symbol: str, interval: str, period: str) -> list[dict] | None:
    try:
        import yfinance as yf
        sym = _get_symbol_in_market(symbol, "us_stock")
        ticker = yf.Ticker(sym)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return None
        df = df.reset_index()
        df = _normalize_klines_df(df)
        return _df_to_records(df)
    except Exception as e:
        logger.warning("yfinance US failed for %s: %s", symbol, e)
        return None


async def _yfinance_hk_klines(symbol: str, interval: str, period: str) -> list[dict] | None:
    try:
        import yfinance as yf
        sym = _get_symbol_in_market(symbol, "hk_stock")
        ticker = yf.Ticker(sym)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return None
        df = df.reset_index()
        df = _normalize_klines_df(df)
        return _df_to_records(df)
    except Exception as e:
        logger.warning("yfinance HK failed for %s: %s", symbol, e)
        return None


async def _yfinance_crypto_klines(symbol: str, interval: str, period: str) -> list[dict] | None:
    try:
        import yfinance as yf
        sym = _get_symbol_in_market(symbol, "crypto")
        ticker = yf.Ticker(sym)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return None
        df = df.reset_index()
        df = _normalize_klines_df(df)
        return _df_to_records(df)
    except Exception as e:
        logger.warning("yfinance crypto failed for %s: %s", symbol, e)
        return None


# ──────────────────────────────────────────────
#  A-Share (akshare)
# ──────────────────────────────────────────────

async def _akshare_cn_klines(symbol: str, interval: str, period: str) -> list[dict] | None:
    try:
        import akshare as ak
        freq_map = {"daily": "daily", "1d": "daily", "weekly": "weekly", "1wk": "weekly",
                     "monthly": "monthly", "1mo": "monthly"}
        freq = freq_map.get(interval, "daily")
        start_map = {"1mo": "20260601", "3mo": "20260401", "6mo": "20260101",
                      "1y": "20250701", "2y": "20240701", "5y": "20210701", "max": "20100101"}
        start = start_map.get(period, "20250701")
        df = ak.stock_zh_a_hist(symbol=symbol, period=freq, start_date=start, adjust="qfq")
        if df.empty:
            return None
        df = _normalize_klines_df(df)
        return _df_to_records(df)
    except Exception as e:
        logger.warning("akshare CN failed for %s: %s", symbol, e)
        return None


# ──────────────────────────────────────────────
#  HK Stock (akshare primary)
# ──────────────────────────────────────────────

async def _akshare_hk_klines(symbol: str, interval: str, period: str) -> list[dict] | None:
    try:
        import akshare as ak
        code = symbol.replace(".HK", "").zfill(5)
        freq_map = {"daily": "daily", "1d": "daily", "weekly": "weekly", "1wk": "weekly",
                     "monthly": "monthly", "1mo": "monthly"}
        freq = freq_map.get(interval, "daily")
        start_map = {"1mo": "20260601", "3mo": "20260401", "6mo": "20260101",
                      "1y": "20250701", "2y": "20240701", "5y": "20210701", "max": "20100101"}
        start = start_map.get(period, "20250701")
        df = ak.stock_hk_hist(symbol=code, period=freq, start_date=start, adjust="qfq")
        if df.empty:
            return None
        df = _normalize_klines_df(df)
        df = _validate_ohlcv(df)
        return _df_to_records(df)
    except Exception as e:
        logger.warning("akshare HK failed for %s: %s", symbol, e)
        return None


# ──────────────────────────────────────────────
#  Crypto (ccxt primary)
# ──────────────────────────────────────────────

async def _ccxt_klines(symbol: str, interval: str, period: str, exchange_id: str = "binance") -> list[dict] | None:
    try:
        import ccxt
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
    except Exception as e:
        logger.warning("ccxt failed for %s: %s", symbol, e)
        return None


async def _coingecko_klines(symbol: str, interval: str, period: str) -> list[dict] | None:
    try:
        from pycoingecko import CoinGeckoAPI
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
    except Exception as e:
        logger.warning("CoinGecko failed for %s: %s", symbol, e)
        return None


# ──────────────────────────────────────────────
#  Fallback wrapper
# ──────────────────────────────────────────────

async def _get_klines_with_fallback(symbol: str, market: str, interval: str, period: str) -> list[dict]:
    source_chains = {
        "us_stock": [lambda s, i, p: _yfinance_klines(s, i, p)],
        "cn_stock": [lambda s, i, p: _akshare_cn_klines(s, i, p),
                     lambda s, i, p: _yfinance_klines(s, i, p)],
        "hk_stock": [lambda s, i, p: _akshare_hk_klines(s, i, p),
                     lambda s, i, p: _yfinance_hk_klines(s, i, p)],
        "crypto": [lambda s, i, p: _ccxt_klines(s, i, p),
                   lambda s, i, p: _yfinance_crypto_klines(s, i, p)],
    }
    sources = source_chains.get(market, source_chains["us_stock"])
    for source_fn in sources:
        result = await source_fn(symbol, interval, period)
        if result:
            return result
    return []


# ──────────────────────────────────────────────
#  Public tools
# ──────────────────────────────────────────────

@tool(
    name="get_stock_quote",
    description="获取实时行情报价（支持美股/A股/港股/加密货币）",
    parameters={
        "symbol": {"type": "string", "description": "股票代码，如 AAPL、600519、00700、BTC"},
        "market": {"type": "string", "description": "市场: us_stock, cn_stock, hk_stock, crypto", "default": "us_stock"},
    },
)
async def get_stock_quote(symbol: str, market: str = "us_stock") -> dict:
    if market == "hk_stock":
        return await _get_hk_quote(symbol)
    if market == "crypto":
        return await _get_crypto_quote(symbol)
    import yfinance as yf
    sym = _get_symbol_in_market(symbol, market)
    ticker = yf.Ticker(sym)
    info = ticker.info
    return {
        "symbol": symbol,
        "price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "change": info.get("regularMarketChange"),
        "change_percent": info.get("regularMarketChangePercent"),
        "volume": info.get("volume") or info.get("regularMarketVolume"),
        "market_cap": info.get("marketCap"),
        "name": info.get("longName") or info.get("shortName"),
    }


async def _get_hk_quote(symbol: str) -> dict:
    try:
        import akshare as ak
        code = symbol.replace(".HK", "").zfill(5)
        df = ak.stock_hk_spot_em()
        row = df[df["代码"] == code]
        if row.empty:
            return {"error": f"HK stock {symbol} not found"}
        r = row.iloc[0]
        return {
            "symbol": symbol, "name": r.get("名称"),
            "price": r.get("最新价"), "change": r.get("涨跌额"),
            "change_percent": r.get("涨跌幅"), "volume": r.get("成交量"),
            "turnover": r.get("成交额"), "pe": r.get("市盈率"),
            "market_cap": r.get("总市值"),
        }
    except Exception as e:
        return {"error": str(e)}


async def _get_crypto_quote(symbol: str) -> dict:
    try:
        import ccxt
        exchange = ccxt.binance({"enableRateLimit": True})
        pair = symbol.upper()
        if "/" not in pair:
            pair = f"{pair}/USDT"
        ticker = exchange.fetch_ticker(pair)
        return {
            "symbol": symbol, "price": ticker.get("last"),
            "bid": ticker.get("bid"), "ask": ticker.get("ask"),
            "change_percent": ticker.get("percentage"),
            "volume_24h": ticker.get("baseVolume"),
            "high_24h": ticker.get("high"), "low_24h": ticker.get("low"),
            "market_cap": ticker.get("info", {}).get("marketCap"),
        }
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="get_klines",
    description="获取K线数据（支持美股/A股/港股/加密货币，自动数据源切换）",
    parameters={
        "symbol": {"type": "string", "description": "股票代码，如 AAPL、00700、BTC"},
        "market": {"type": "string", "description": "市场: us_stock, cn_stock, hk_stock, crypto", "default": "us_stock"},
        "interval": {"type": "string", "description": "周期: 1d, 1wk, 1mo", "default": "1d"},
        "period": {"type": "string", "description": "时期: 1mo, 3mo, 6mo, 1y, 2y, 5y, max", "default": "1y"},
    },
)
async def get_klines(symbol: str, market: str = "us_stock", interval: str = "1d", period: str = "1y") -> list:
    return await _get_klines_with_fallback(symbol, market, interval, period)


@tool(
    name="get_cn_klines",
    description="获取A股K线数据（通过 AKShare）",
    parameters={
        "symbol": {"type": "string", "description": "A股代码，如 600519、000001"},
        "interval": {"type": "string", "description": "周期: daily, weekly, monthly", "default": "daily"},
        "period": {"type": "string", "description": "年数", "default": "1y"},
    },
)
async def get_cn_klines(symbol: str, interval: str = "daily", period: str = "1y") -> list:
    result = await _akshare_cn_klines(symbol, interval, period)
    return result if result else []


# ──────────────────────────────────────────────
#  HK Stock tools
# ──────────────────────────────────────────────

@tool(
    name="get_hk_klines",
    description="获取港股K线数据（通过 AKShare）",
    parameters={
        "symbol": {"type": "string", "description": "港股代码，如 00700、09988"},
        "interval": {"type": "string", "description": "周期: daily, weekly, monthly", "default": "daily"},
        "period": {"type": "string", "description": "时期: 1mo, 3mo, 6mo, 1y, 2y, 5y", "default": "1y"},
    },
)
async def get_hk_klines(symbol: str, interval: str = "daily", period: str = "1y") -> list:
    result = await _akshare_hk_klines(symbol, interval, period)
    return result if result else []


@tool(
    name="get_hk_realtime",
    description="获取港股实时行情（批量，返回多只股票）",
    parameters={
        "symbols": {
            "type": "array", "items": {"type": "string"},
            "description": "港股代码列表，如 ['00700', '09988']，不传则返回全部",
        },
    },
)
async def get_hk_realtime(symbols: list[str] | None = None) -> list[dict]:
    try:
        import akshare as ak
        df = ak.stock_hk_spot_em()
        if symbols:
            codes = [s.replace(".HK", "").zfill(5) for s in symbols]
            df = df[df["代码"].isin(codes)]
        result = []
        for _, r in df.iterrows():
            result.append({
                "symbol": r.get("代码"), "name": r.get("名称"),
                "price": r.get("最新价"), "change": r.get("涨跌额"),
                "change_percent": r.get("涨跌幅"), "volume": r.get("成交量"),
                "turnover": r.get("成交额"), "pe": r.get("市盈率"),
                "market_cap": r.get("总市值"),
            })
        return result[:50]
    except Exception as e:
        return [{"error": str(e)}]


@tool(
    name="get_hk_index",
    description="获取港股指数行情（恒生指数、恒生科技指数等）",
    parameters={},
)
async def get_hk_index() -> list[dict]:
    indices = {"^HSI": "恒生指数", "^HSTECH": "恒生科技指数"}
    import yfinance as yf
    results = []
    for sym, name in indices.items():
        try:
            ticker = yf.Ticker(sym)
            info = ticker.info
            results.append({
                "symbol": sym, "name": name,
                "price": info.get("regularMarketPrice"),
                "change_percent": info.get("regularMarketChangePercent"),
            })
        except Exception:
            continue
    return results


@tool(
    name="get_hk_flow",
    description="获取港股南向/北向资金流数据",
    parameters={
        "direction": {"type": "string", "description": "方向: northbound(北向), southbound(南向), both", "default": "both"},
    },
)
async def get_hk_flow(direction: str = "both") -> dict:
    try:
        import akshare as ak
        result = {}
        if direction in ("northbound", "both"):
            df_n = ak.stock_hsgt_hist_em(symbol="北向资金")
            if not df_n.empty:
                result["northbound"] = df_n.tail(10).to_dict(orient="records")
        if direction in ("southbound", "both"):
            df_s = ak.stock_hsgt_hist_em(symbol="南向资金")
            if not df_s.empty:
                result["southbound"] = df_s.tail(10).to_dict(orient="records")
        return result
    except Exception as e:
        return {"error": str(e)}


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
    result = await _ccxt_klines(symbol, interval, period, exchange)
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
        cg = CoinGeckoAPI()
        global_data = cg.get_global()
        fg = cg.get恐惧与贪婪指数() if hasattr(cg, 'get_恐惧与贪婪指数') else None
        try:
            fg_data = cg.get_global()  
            fg = None
        except Exception:
            fg = None
        top_coins = cg.get_coins_markets(vs_currency="usd", per_page=10, order="market_cap_desc")
        result = {
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
        return result
    except Exception as e:
        return {"error": str(e)}


# ──────────────────────────────────────────────
#  Market overview (multi-market)
# ──────────────────────────────────────────────

@tool(
    name="get_market_overview",
    description="获取市场概况（主要指数行情）",
    parameters={
        "market": {"type": "string", "description": "市场: us_stock, cn_stock, hk_stock, crypto", "default": "us_stock"},
    },
)
async def get_market_overview(market: str = "us_stock") -> list[dict]:
    if market == "crypto":
        overview = await get_crypto_overview()
        return overview.get("top_10", [])

    indices = {
        "us_stock": ["^GSPC", "^DJI", "^IXIC", "^RUT"],
        "cn_stock": ["000001.SH", "399001.SZ", "399006.SZ"],
        "hk_stock": ["^HSI", "^HSTECH"],
    }
    syms = indices.get(market, indices["us_stock"])
    import yfinance as yf
    results = []
    for sym in syms:
        try:
            ticker = yf.Ticker(sym)
            info = ticker.info
            results.append({
                "symbol": sym,
                "name": info.get("shortName") or info.get("symbol"),
                "price": info.get("regularMarketPrice"),
                "change_percent": info.get("regularMarketChangePercent"),
            })
        except Exception:
            continue
    return results
