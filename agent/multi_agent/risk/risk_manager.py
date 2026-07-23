"""
Risk Manager Agent

Checks positions against constitution rules, enforces stop-loss,
and validates risk constraints before any trade execution.
"""

from __future__ import annotations

import logging
from datetime import datetime

from agent.multi_agent.base import BaseAgent

logger = logging.getLogger(__name__)


class RiskManagerAgent(BaseAgent):
    """Multi-layer risk vetting before trade execution."""

    def __init__(self, llm_client):
        super().__init__(
            name="RiskManager",
            llm_client=llm_client,
            tools=["check_constitution", "assess_portfolio_risk", "calculate_position_size"],
            system_prompt="""You are the Risk Manager. Enforce all trading constitution rules:
1. Max 20% per position, 2% stop-loss per trade
2. Min 5 positions for diversification, max 15% total drawdown
3. Veto any signal that violates these rules
Output approved/rejected signals with veto reasons.""",
        )

    async def _analyze(self, input_data: dict, context: dict) -> dict:
        signals = input_data.get("signals", [])
        rejected: list[dict] = []

        for sig in signals:
            const_result = await self._safe_tool("check_constitution",
                symbol=sig.get("symbol", ""), signal=sig)
            violations = const_result.get("violations", [])
            if violations:
                rejected.append({"symbol": sig.get("symbol"), "reason": violations, "action": sig.get("action")})

        portfolio_risk = await self._safe_tool("assess_portfolio_risk",
            symbols=[s.get("symbol", "") for s in signals])

        approved = [s for s in signals if s.get("symbol") not in {r["symbol"] for r in rejected}]
        return {
            "agent": self.name, "approved_signals": len(approved),
            "rejected_signals": len(rejected), "rejected_detail": rejected,
            "portfolio_risk": portfolio_risk, "timestamp": datetime.now().isoformat(),
        }

    async def _decide(self, input_data: dict, context: dict) -> dict: return await self._analyze(input_data, context)
    async def _evaluate(self, input_data: dict, context: dict) -> dict: return await self._analyze(input_data, context)
