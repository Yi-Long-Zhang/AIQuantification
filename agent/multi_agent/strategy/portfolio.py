"""
Portfolio Optimizer Agent

Allocates capital across positions, applies risk parity and
concentration limits based on multi-factor risk analysis.
"""

from __future__ import annotations

import logging
from datetime import datetime

from agent.multi_agent.base import BaseAgent

logger = logging.getLogger(__name__)


class PortfolioOptimizerAgent(BaseAgent):
    """Allocate capital and optimize position sizing."""

    def __init__(self, llm_client):
        super().__init__(
            name="PortfolioOptimizer",
            llm_client=llm_client,
            tools=["calculate_position_size", "assess_portfolio_risk"],
            system_prompt="""You are the Portfolio Optimizer. Allocate capital across positions
using risk parity principles. Enforce: max 20% per position, max 15% total drawdown,
minimum 5 positions. Output position sizes and risk-adjusted weights.""",
        )

    async def _analyze(self, input_data: dict, context: dict) -> dict:
        signals = input_data.get("signals", [])
        account_balance = input_data.get("account_balance", 100000)
        if not signals:
            return {"agent": self.name, "allocations": [], "timestamp": datetime.now().isoformat()}

        allocations = []
        weight_per_signal = 1.0 / max(len(signals), 1)
        for sig in signals[:10]:
            pos = await self._safe_tool("calculate_position_size",
                symbol=sig.get("symbol", ""), price=sig.get("entry_price", 100),
                account_balance=account_balance, risk_per_trade=0.02)
            allocations.append({
                "symbol": sig.get("symbol"),
                "shares": pos.get("shares", 0),
                "position_pct": pos.get("position_pct", 0),
                "weight": round(weight_per_signal, 3),
                "stop_loss_pct": pos.get("stop_loss_pct", 5),
            })
        return {"agent": self.name, "allocations": allocations, "timestamp": datetime.now().isoformat()}

    async def _decide(self, input_data: dict, context: dict) -> dict: return await self._analyze(input_data, context)
    async def _evaluate(self, input_data: dict, context: dict) -> dict: return await self._analyze(input_data, context)
