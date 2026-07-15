from __future__ import annotations

import asyncio
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


# ──────────────────────────────────────────────
#  Mock data for fallback (when network fails)
# ──────────────────────────────────────────────

def _get_mock_quote(symbol: str, market: str) -> dict:
    """返回模拟行情数据（用于网络故障时的降级）"""
    import random

    base_prices = {
        "AAPL": 180.0,
        "MSFT": 380.0,
        "GOOGL": 140.0,
        "TSLA": 250.0,
        "AMZN": 175.0,
        "META": 485.0,
        "NVDA": 880.0,
        "AMD": 165.0,
        "BTC": 65000.0,
        "ETH": 3200.0,
    }

    base_price = base_prices.get(symbol.upper(), 100.0)
    change_pct = random.uniform(-3.0, 3.0)
    change = base_price * (change_pct / 100)

    logger.warning(f"Using mock data for {symbol} (network unavailable)")

    return {
        "symbol": symbol,
        "price": round(base_price + change, 2),
        "change": round(change, 2),
        "change_percent": round(change_pct, 2),
        "volume": random.randint(10000000, 100000000),
        "market_cap": int(base_price * 1e9),
        "name": symbol,
        "_mock": True,  # 标记为模拟数据
    }


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

        def _fetch():
            sym = _get_symbol_in_market(symbol, "us_stock")
            # 添加重试逻辑和更好的错误处理
            ticker = yf.Ticker(sym)

            # 尝试获取数据，带超时和重试
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    df = ticker.history(period=period, interval=interval, timeout=10)
                    if not df.empty:
                        break
                except Exception as retry_error:
                    if attempt == max_retries - 1:
                        raise
                    import time
                    time.sleep(1)

            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return None

            df = df.reset_index()
            df = _normalize_klines_df(df)
            return _df_to_records(df)

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        logger.error("yfinance US failed for %s: %s", symbol, e, exc_info=True)
        return None


# ──────────────────────────────────────────────
#  A-Share (akshare)
# ──────────────────────────────────────────────

async def _akshare_cn_klines(symbol: str, interval: str, period: str) -> list[dict] | None:
    try:
        import akshare as ak

        def _fetch():
            freq_map = {"daily": "daily", "1d": "daily", "weekly": "weekly", "1wk": "weekly",
                         "monthly": "monthly", "1mo": "monthly"}
            freq = freq_map.get(interval, "daily")
            start = _get_start_date(period)
            df = ak.stock_zh_a_hist(symbol=symbol, period=freq, start_date=start, adjust="qfq")
            if df.empty:
                return None
            df = _normalize_klines_df(df)
            return _df_to_records(df)

        return await asyncio.to_thread(_fetch)
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
        try:
            results = await get_hk_realtime([symbol])
            return results[0] if results else {"error": f"HK stock {symbol} not found"}
        except Exception as e:
            logger.error(f"Failed to get HK stock quote for {symbol}: {e}")
            return _get_mock_quote(symbol, market)

    if market == "crypto":
        from .crypto import get_crypto_realtime
        try:
            return await get_crypto_realtime(symbol)
        except Exception as e:
            logger.error(f"Failed to get crypto quote for {symbol}: {e}")
            return _get_mock_quote(symbol, market)

    import yfinance as yf

    def _fetch():
        sym = _get_symbol_in_market(symbol, market)

        # 尝试获取数据，带重试
        for attempt in range(2):
            try:
                ticker = yf.Ticker(sym)
                info = ticker.info

                # 验证数据有效性
                price = info.get("currentPrice") or info.get("regularMarketPrice")
                if price:
                    return {
                        "symbol": symbol,
                        "price": price,
                        "change": info.get("regularMarketChange", 0),
                        "change_percent": info.get("regularMarketChangePercent", 0),
                        "volume": info.get("volume") or info.get("regularMarketVolume", 0),
                        "market_cap": info.get("marketCap"),
                        "name": info.get("longName") or info.get("shortName", symbol),
                    }
            except Exception as e:
                if attempt == 0:
                    import time
                    time.sleep(1)
                else:
                    logger.error(f"yfinance failed for {symbol}: {e}")

        return None

    try:
        result = await asyncio.to_thread(_fetch)
        if result:
            return result
    except Exception as e:
        logger.error(f"Failed to get stock quote for {symbol}: {e}")

    # 返回模拟数据
    return _get_mock_quote(symbol, market)


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
        try:
            from .crypto import get_crypto_overview
            overview = await get_crypto_overview()
            return overview.get("top_10", [])
        except Exception as e:
            logger.error(f"Failed to get crypto overview: {e}")
            return _get_mock_market_overview("crypto")

    indices = {
        "us_stock": ["^GSPC", "^DJI", "^IXIC", "^RUT"],
        "cn_stock": ["000001.SH", "399001.SZ", "399006.SZ"],
        "hk_stock": ["^HSI", "^HSTECH"],
    }
    syms = indices.get(market, indices["us_stock"])

    import yfinance as yf

    def _fetch():
        results = []
        for sym in syms:
            try:
                ticker = yf.Ticker(sym)
                info = ticker.info
                price = info.get("regularMarketPrice")
                if price:  # 只添加有效数据
                    results.append({
                        "symbol": sym,
                        "name": info.get("shortName") or info.get("symbol", sym),
                        "price": price,
                        "change_percent": info.get("regularMarketChangePercent", 0),
                    })
            except Exception as e:
                logger.debug(f"Failed to get {sym}: {e}")
                continue
        return results

    try:
        results = await asyncio.to_thread(_fetch)
        if results:
            return results
    except Exception as e:
        logger.error(f"Failed to get market overview: {e}")

    # 返回模拟数据
    return _get_mock_market_overview(market)


def _get_mock_market_overview(market: str) -> list[dict]:
    """返回模拟市场概况（网络故障时的降级）"""
    import random

    mock_data = {
        "us_stock": [
            {"symbol": "AAPL", "name": "Apple Inc.", "price": 180.0, "change_percent": random.uniform(-2, 2)},
            {"symbol": "MSFT", "name": "Microsoft", "price": 380.0, "change_percent": random.uniform(-2, 2)},
            {"symbol": "GOOGL", "name": "Alphabet", "price": 140.0, "change_percent": random.uniform(-2, 2)},
            {"symbol": "TSLA", "name": "Tesla", "price": 250.0, "change_percent": random.uniform(-2, 2)},
        ],
        "crypto": [
            {"symbol": "BTC", "name": "Bitcoin", "price": 65000.0, "change_percent": random.uniform(-5, 5)},
            {"symbol": "ETH", "name": "Ethereum", "price": 3200.0, "change_percent": random.uniform(-5, 5)},
            {"symbol": "BNB", "name": "Binance Coin", "price": 580.0, "change_percent": random.uniform(-5, 5)},
        ],
        "cn_stock": [
            {"symbol": "000001", "name": "平安银行", "price": 12.50, "change_percent": random.uniform(-2, 2)},
            {"symbol": "600519", "name": "贵州茅台", "price": 1680.0, "change_percent": random.uniform(-2, 2)},
        ],
        "hk_stock": [
            {"symbol": "00700", "name": "腾讯控股", "price": 380.0, "change_percent": random.uniform(-2, 2)},
            {"symbol": "09988", "name": "阿里巴巴", "price": 78.0, "change_percent": random.uniform(-2, 2)},
        ],
    }

    data = mock_data.get(market, mock_data["us_stock"])
    for item in data:
        item["_mock"] = True
        item["change_percent"] = round(item["change_percent"], 2)

    logger.warning(f"Using mock market overview for {market} (network unavailable)")
    return data


# ──────────────────────────────────────────────
#  Global Macro (akshare)
# ──────────────────────────────────────────────

async def _fetch_macro_data(data_type: str) -> list[dict] | None:
    try:
        import akshare as ak

        def _fetch():
            fetchers = {
                "gdp": lambda: ak.macro_china_gdp(),
                "cpi": lambda: ak.macro_china_cpi(),
                "pmi": lambda: ak.macro_china_pmi(),
                "interest_rate": lambda: ak.macro_china_interest_rate(),
                "social_financing": lambda: ak.macro_china_shrzgm(),
                "money_supply": lambda: ak.macro_china_money_supply(),
                "trade_balance": lambda: ak.macro_china_trade_balance(),
                "industrial_production": lambda: ak.macro_china_industrial_production_yoy(),
                "retail_sales": lambda: ak.macro_china_consumer_goods_retail(),
                "unemployment": lambda: ak.macro_china_urban_unemployment(),
            }
            fetcher = fetchers.get(data_type)
            if not fetcher:
                return None
            df = fetcher()
            if df is None or df.empty:
                return None
            df = df.head(12)
            col_map = {"日期": "date", "今值": "value", "前值": "prev", "预测值": "forecast"}
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
            return _df_to_records(df, max_rows=12)

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        logger.warning("akshare macro %s failed: %s", data_type, e)
        return None


@tool(
    name="get_global_macro",
    description="获取全球宏观经济数据（GDP/CPI/PMI/利率/社融/M2/贸易差/工业增加值/零售/失业率）",
    parameters={
        "indicator": {"type": "string", "description": "指标: gdp, cpi, pmi, interest_rate, social_financing, money_supply, trade_balance, industrial_production, retail_sales, unemployment"},
    },
)
async def get_global_macro(indicator: str = "gdp") -> dict:
    result = await _fetch_macro_data(indicator)
    if result is None:
        return {"error": f"Indicator '{indicator}' not available or fetch failed"}
    return {"indicator": indicator, "data": result, "count": len(result)}


# ──────────────────────────────────────────────
#  Sector Rotation (akshare)
# ──────────────────────────────────────────────

@tool(
    name="get_sector_rotation",
    description="获取板块轮动分析（行业板块涨跌幅排名）",
    parameters={
        "top_n": {"type": "integer", "description": "返回数量，默认15", "default": 15},
    },
)
async def get_sector_rotation(top_n: int = 15) -> dict:
    try:
        import akshare as ak

        def _fetch():
            df = ak.stock_board_industry_name_em()
            if df is None or df.empty:
                return {"error": "No sector data available"}
            col_map = {"板块名称": "name", "板块代码": "code", "最新价": "price",
                       "涨跌幅": "change_pct", "涨跌额": "change", "总市值": "market_cap",
                       "换手率": "turnover_rate", "上涨家数": "up_count", "下跌家数": "down_count"}
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
            if "change_pct" in df.columns:
                df = df.sort_values("change_pct", ascending=False)
            top_gainers = _df_to_records(df.head(top_n), max_rows=top_n)
            top_losers = _df_to_records(df.tail(top_n).iloc[::-1], max_rows=top_n)
            return {
                "market": "A股行业板块",
                "top_gainers": top_gainers,
                "top_losers": top_losers,
                "total_sectors": len(df),
            }

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        return {"error": str(e)}
