import pandas as pd

from .registry import tool


def _get_symbol_in_market(symbol: str, market: str) -> str:
    mapping = {
        "us_stock": lambda s: s,
        "crypto": lambda s: f"{s}-USD" if "-" not in s else s,
        "hk_stock": lambda s: f"{s}.HK" if "." not in s else s,
        "cn_stock": lambda s: s,
        "fund": lambda s: s,
    }
    return mapping.get(market, lambda s: s)(symbol)


@tool(
    name="get_stock_quote",
    description="获取实时行情报价",
    parameters={
        "symbol": {"type": "string", "description": "股票代码，如 AAPL、600519.SH"},
        "market": {"type": "string", "description": "市场: us_stock, cn_stock, hk_stock, crypto", "default": "us_stock"},
    },
)
async def get_stock_quote(symbol: str, market: str = "us_stock") -> dict:
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
    description="获取K线数据",
    parameters={
        "symbol": {"type": "string", "description": "股票代码"},
        "market": {"type": "string", "description": "市场", "default": "us_stock"},
        "interval": {"type": "string", "description": "周期: 1d, 1wk, 1mo", "default": "1d"},
        "period": {"type": "string", "description": "时期: 1mo, 3mo, 6mo, 1y, 2y, 5y, max", "default": "1y"},
    },
)
async def get_klines(symbol: str, market: str = "us_stock", interval: str = "1d", period: str = "1y") -> list:
    import yfinance as yf
    sym = _get_symbol_in_market(symbol, market)
    ticker = yf.Ticker(sym)
    df = ticker.history(period=period, interval=interval)
    if df.empty:
        return []
    df = df.reset_index()
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    return df.tail(500).to_dict(orient="records")


@tool(
    name="get_cn_klines",
    description="获取A股K线数据（通过 AKShare）",
    parameters={
        "symbol": {"type": "string", "description": "A股代码，如 sh600519, sz000001"},
        "interval": {"type": "string", "description": "周期: daily, weekly, monthly", "default": "daily"},
        "period": {"type": "string", "description": "年数", "default": "1y"},
    },
)
async def get_cn_klines(symbol: str, interval: str = "daily", period: str = "1y") -> list:
    import akshare as ak
    freq_map = {"daily": "daily", "weekly": "weekly", "monthly": "monthly"}
    freq = freq_map.get(interval, "daily")
    start_map = {"1mo": "20260101", "3mo": "20260401", "6mo": "20260101", "1y": "20250701", "2y": "20240701", "5y": "20210701", "max": "20100101"}
    start = start_map.get(period, "20250701")
    try:
        df = ak.stock_zh_a_hist(symbol=symbol, period=freq, start_date=start, adjust="qfq")
        if df.empty:
            return []
        df = df.rename(columns={
            "日期": "Date", "开盘": "Open", "收盘": "Close",
            "最高": "High", "最低": "Low", "成交量": "Volume",
        })
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
        return df.tail(500).to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]


@tool(
    name="get_market_overview",
    description="获取市场概况（主要指数行情）",
    parameters={
        "market": {"type": "string", "description": "市场", "default": "us_stock"},
    },
)
async def get_market_overview(market: str = "us_stock") -> list[dict]:
    indices = {
        "us_stock": ["^GSPC", "^DJI", "^IXIC", "^RUT"],
        "cn_stock": ["000001.SH", "399001.SZ", "399006.SZ"],
        "hk_stock": ["^HSI"],
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
