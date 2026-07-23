"""
Strategy Backtester Agent

Validates trading signals through rigorous backtesting.
"""

from __future__ import annotations

import logging
from datetime import datetime

from agent.multi_agent.base import BaseAgent

logger = logging.getLogger(__name__)


class BacktesterAgent(BaseAgent):
    """Backtest strategy signals to validate performance."""

    def __init__(self, llm_client):
        super().__init__(
            name="Backtester",
            llm_client=llm_client,
            tools=["run_backtest", "compare_strategies", "walk_forward_test"],
            system_prompt="""You are the Backtester, responsible for validating trading strategies.

Run backtests on proposed signals. Compare strategies. Report Sharpe ratio,
max drawdown, win rate, and annualized return. Recommend best strategy.""",
        )

    async def _analyze(self, input_data: dict, context: dict) -> dict:
        symbols = input_data.get("symbols", ["AAPL"])
        market = input_data.get("market", "us_stock")
        strategies = input_data.get("strategies", ["sma_cross", "macd"])
        results = []
        for symbol in symbols[:5]:
            for strategy in strategies[:3]:
                r = await self._safe_tool("run_backtest", symbol=symbol, market=market, strategy=strategy)
                if r:
                    results.append({"symbol": symbol, "strategy": strategy, **{k: v for k, v in r.items() if k != "trade_log"}})
        return {"agent": self.name, "market": market, "results": sorted(results, key=lambda x: x.get("sharpe_ratio", 0) or 0, reverse=True), "timestamp": datetime.now().isoformat()}

    async def _decide(self, input_data: dict, context: dict) -> dict: return await self._analyze(input_data, context)
    async def _evaluate(self, input_data: dict, context: dict) -> dict: return await self._analyze(input_data, context)
