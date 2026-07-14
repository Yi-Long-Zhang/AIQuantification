from __future__ import annotations

import logging
from datetime import datetime, timedelta

import pandas as pd

from .registry import tool


def _get_start_date(period: str) -> str:
    """根据 period 动态计算开始日期"""
    now = datetime.now()
    period_map = {
        "1mo": timedelta(days=30),
        "3mo": timedelta(days=90),
        "6mo": timedelta(days=180),
        "1y": timedelta(days=365),
        "2y": timedelta(days=730),
        "5y": timedelta(days=1825),
        "max": timedelta(days=3650),
    }
    delta = period_map.get(period, timedelta(days=365))
    start = now - delta
    return start.strftime("%Y%m%d")

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


# ──────────────────────────────────────────────
#  A-Share (akshare)
# ──────────────────────────────────────────────

async def _akshare_cn_klines(symbol: str, interval: str, period: str) -> list[dict] | None:
    try:
        import akshare as ak
        freq_map = {"daily": "daily", "1d": "daily", "weekly": "weekly", "1wk": "weekly",
                     "monthly": "monthly", "1mo": "monthly"}
        freq = freq_map.get(interval, "daily")
        start = _get_start_date(period)
        df = ak.stock_zh_a_hist(symbol=symbol, period=freq, start_date=start, adjust="qfq")
        if df.empty:
            return None
        df = _normalize_klines_df(df)
        return _df_to_records(df)
    except Exception as e:
        logger.warning("akshare CN failed for %s: %s", symbol, e)
        return None


# ──────────────────────────────────────────────
#  Fallback wrapper
# ──────────────────────────────────────────────

async def _get_klines_with_fallback(symbol: str, market: str, interval: str, period: str) -> list[dict]:
    from .hk_stock import _get_hk_klines_with_fallback
    from .crypto import _get_crypto_klines_with_fallback

    source_chains = {
        "us_stock": [lambda s, i, p: _yfinance_klines(s, i, p)],
        "cn_stock": [lambda s, i, p: _akshare_cn_klines(s, i, p),
                     lambda s, i, p: _yfinance_klines(s, i, p)],
        "hk_stock": [lambda s, i, p: _get_hk_klines_with_fallback(s, i, p)],
        "crypto": [lambda s, i, p: _get_crypto_klines_with_fallback(s, i, p)],
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
        from .hk_stock import get_hk_realtime
        results = await get_hk_realtime([symbol])
        return results[0] if results else {"error": f"HK stock {symbol} not found"}
    if market == "crypto":
        from .crypto import get_crypto_realtime
        return await get_crypto_realtime(symbol)
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
        from .crypto import get_crypto_overview
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
