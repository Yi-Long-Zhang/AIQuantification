from __future__ import annotations

import asyncio
import logging

import pandas as pd

from .registry import tool

logger = logging.getLogger(__name__)


async def _get_klines(symbol: str, market: str) -> list[dict] | None:
    from .market_data import _get_klines_with_fallback
    return await _get_klines_with_fallback(symbol, market, "1d", "1y")


@tool(
    name="compute_alpha_factors",
    description="计算 Alpha158 或 Alpha101 因子值（返回最近5日数据）",
    parameters={
        "symbol": {"type": "string", "description": "股票代码，如 AAPL、600519、BTC"},
        "market": {"type": "string", "description": "市场: us_stock, cn_stock, hk_stock, crypto", "default": "us_stock"},
        "factor_set": {"type": "string", "description": "因子集: alpha158, alpha101", "default": "alpha158"},
        "factor_names": {"type": "array", "items": {"type": "string"}, "description": "指定因子名（可选，留空计算全部）"},
    },
)
async def compute_alpha_factors(
    symbol: str,
    market: str = "us_stock",
    factor_set: str = "alpha158",
    factor_names: list[str] | None = None,
) -> dict:
    try:
        klines = await _get_klines(symbol, market)
        if not klines:
            return {"error": "No data available"}

        df = pd.DataFrame(klines)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])

        def _compute():
            from agent.alpha import Alpha158, Alpha101
            if factor_set == "alpha101":
                result_df = Alpha101.compute(df, factor_names)
            else:
                result_df = Alpha158.compute(df, factor_names)
            return result_df.tail(5).to_dict(orient="records")

        result = await asyncio.to_thread(_compute)
        return {"symbol": symbol, "factor_set": factor_set, "data": result, "rows": len(result)}
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="evaluate_alpha_factors",
    description="评估因子有效性（IC/IR/换手率/Sharpe/最大回撤）",
    parameters={
        "symbol": {"type": "string", "description": "股票代码"},
        "market": {"type": "string", "description": "市场: us_stock, cn_stock, hk_stock, crypto", "default": "us_stock"},
        "factor_set": {"type": "string", "description": "因子集: alpha158, alpha101", "default": "alpha158"},
        "top_n": {"type": "integer", "description": "返回排名前N的因子，默认20", "default": 20},
    },
)
async def evaluate_alpha_factors(
    symbol: str,
    market: str = "us_stock",
    factor_set: str = "alpha158",
    top_n: int = 20,
) -> dict:
    try:
        klines = await _get_klines(symbol, market)
        if not klines:
            return {"error": "No data available"}

        df = pd.DataFrame(klines)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])

        def _evaluate():
            from agent.alpha import Alpha158, Alpha101, FactorEvaluator
            forward_returns = df["close"].pct_change().shift(-1)
            if factor_set == "alpha101":
                factor_df = Alpha101.compute(df)
            else:
                factor_df = Alpha158.compute(df)
            metrics = FactorEvaluator.evaluate_batch(factor_df, forward_returns)
            ranked = FactorEvaluator.rank_factors(metrics, top_n=top_n)
            return {"top_factors": ranked, "total_evaluated": len(metrics)}

        result = await asyncio.to_thread(_evaluate)
        return {"symbol": symbol, "factor_set": factor_set, **result}
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="list_alpha_factors",
    description="列出可用的 Alpha 因子（Alpha158/Alpha101）",
    parameters={
        "factor_set": {"type": "string", "description": "因子集: alpha158, alpha101, all", "default": "all"},
    },
)
async def list_alpha_factors(factor_set: str = "all") -> dict:
    try:
        from agent.alpha import Alpha158, Alpha101

        result = {}
        if factor_set in ("alpha158", "all"):
            result["alpha158"] = Alpha158.list_factors()
        if factor_set in ("alpha101", "all"):
            result["alpha101"] = Alpha101.list_factors()
        return result
    except Exception as e:
        return {"error": str(e)}
