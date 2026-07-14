from __future__ import annotations

import asyncio
import logging

import pandas as pd

from .registry import tool
from .market_data import (
    _get_start_date,
    _normalize_klines_df,
    _validate_ohlcv,
    _df_to_records,
    _get_symbol_in_market,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
#  HK Stock data sources
# ──────────────────────────────────────────────

async def _yfinance_hk_klines(symbol: str, interval: str, period: str) -> list[dict] | None:
    try:
        import yfinance as yf

        def _fetch():
            sym = _get_symbol_in_market(symbol, "hk_stock")
            ticker = yf.Ticker(sym)
            df = ticker.history(period=period, interval=interval)
            if df.empty:
                return None
            df = df.reset_index()
            df = _normalize_klines_df(df)
            return _df_to_records(df)

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        logger.warning("yfinance HK failed for %s: %s", symbol, e)
        return None


async def _akshare_hk_klines(symbol: str, interval: str, period: str) -> list[dict] | None:
    try:
        import akshare as ak

        def _fetch():
            code = symbol.replace(".HK", "").zfill(5)
            freq_map = {"daily": "daily", "1d": "daily", "weekly": "weekly", "1wk": "weekly",
                         "monthly": "monthly", "1mo": "monthly"}
            freq = freq_map.get(interval, "daily")
            start = _get_start_date(period)
            df = ak.stock_hk_hist(symbol=code, period=freq, start_date=start, adjust="qfq")
            if df.empty:
                return None
            df = _normalize_klines_df(df)
            df = _validate_ohlcv(df)
            return _df_to_records(df)

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        logger.warning("akshare HK failed for %s: %s", symbol, e)
        return None


async def _get_hk_klines_with_fallback(symbol: str, interval: str, period: str) -> list[dict]:
    result = await _akshare_hk_klines(symbol, interval, period)
    if result:
        return result
    result = await _yfinance_hk_klines(symbol, interval, period)
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
    result = await _get_hk_klines_with_fallback(symbol, interval, period)
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

        def _fetch():
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

        return await asyncio.to_thread(_fetch)
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

    def _fetch():
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

    return await asyncio.to_thread(_fetch)


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

        def _fetch():
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

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="get_hk_fund_flow",
    description="获取港股个股资金流向（主力/散户资金）",
    parameters={
        "symbol": {"type": "string", "description": "港股代码，如 00700、09988"},
    },
)
async def get_hk_fund_flow(symbol: str) -> dict:
    try:
        import akshare as ak

        def _fetch():
            code = symbol.replace(".HK", "").zfill(5)
            df = ak.stock_hk_ggt_components_em(symbol=code)
            if df is None or df.empty:
                return {"error": f"No fund flow data for {symbol}"}
            df = df.tail(10)
            result = {
                "symbol": symbol,
                "records": [],
            }
            for _, r in df.iterrows():
                result["records"].append({
                    "date": r.get("日期"),
                    "main_net_inflow": r.get("主力净流入"),
                    "main_net_pct": r.get("主力净流入占比"),
                    "super_large_net": r.get("超大单净流入"),
                    "large_net": r.get("大单净流入"),
                    "medium_net": r.get("中单净流入"),
                    "small_net": r.get("小单净流入"),
                })
            return result

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="get_hk_valuation",
    description="获取港股估值数据（PE/PB/股息率）",
    parameters={
        "symbol": {"type": "string", "description": "港股代码，如 00700、09988"},
    },
)
async def get_hk_valuation(symbol: str) -> dict:
    try:
        import akshare as ak

        def _fetch():
            code = symbol.replace(".HK", "").zfill(5)
            df = ak.stock_hk_valuation_baidu(symbol=code, indicator="总市值", period="近一年")
            if df is None or df.empty:
                return {"error": f"No valuation data for {symbol}"}
            latest = df.iloc[-1] if len(df) > 0 else {}
            return {
                "symbol": symbol,
                "valuation": {
                    "date": str(latest.get("日期", "")),
                    "market_cap": latest.get("总市值"),
                    "pe_ttm": latest.get("市盈率(TTM)"),
                    "pb": latest.get("市净率"),
                    "ps_ttm": latest.get("市销率(TTM)"),
                },
                "history": df.tail(20).to_dict(orient="records"),
            }

        return await asyncio.to_thread(_fetch)
    except Exception as e:
        return {"error": str(e)}
