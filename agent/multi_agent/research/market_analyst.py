"""
Research Agent 1 / 5 — MarketAnalystAgent

Responsibilities:
- Analyze market-wide trends (bull / bear / sideways)
- Identify sector rotation leaders
- Assess macro risk environment
- Provide overall market stance for the cycle
"""

from __future__ import annotations

import logging
from datetime import datetime

from agent.multi_agent.base import BaseAgent
from agent.llm_client import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior market analyst in a quantitative trading system.

Your workflow:
1. Fetch market overview → sector rotation (top 10) → PMI → sentiment
2. Determine: trend direction (BULL/BEAR/SIDEWAYS), hot & weak sectors, macro risk
3. Output strategy bias: AGGRESSIVE / NEUTRAL / DEFENSIVE

Key signals:
- PMI > 50 + sector rotation to cyclicals → BULL
- PMI < 45 + rotation to defensives → BEAR
- Sentiment extreme (fear < 20 or greed > 80) → potential reversal

Output ONLY valid JSON: {"trend": "BULL", "trend_confidence": 0.75, "hot_sectors": ["tech"], "weak_sectors": ["utilities"], "macro_risk": "LOW", "strategy_bias": "AGGRESSIVE", "key_observations": ["reason1"], "timestamp": "..."}
"""


class MarketAnalystAgent(BaseAgent):
    """Analyzes macro market trends, sector rotation, and overall risk environment."""

    TOOLS = [
        "get_market_overview",
        "get_sector_rotation",
        "get_global_macro",
        "analyze_sentiment",
    ]

    def __init__(self, llm_client: LLMClient):
        super().__init__(
            name="MarketAnalyst",
            llm_client=llm_client,
            tools=self.TOOLS,
            system_prompt=SYSTEM_PROMPT,
        )

    # ── BaseAgent implementation ──────────────────────────────────────────────

    async def _analyze(self, input_data: dict, context: dict) -> dict:
        market = input_data.get("market", "us_stock")
        return await self.analyze_market(market)

    async def _decide(self, input_data: dict, context: dict) -> dict:
        return await self._analyze(input_data, context)

    async def _evaluate(self, input_data: dict, context: dict) -> dict:
        return await self._analyze(input_data, context)

    # ── Core logic ────────────────────────────────────────────────────────────

    async def analyze_market(self, market: str = "us_stock") -> dict:
        """
        Full market analysis pipeline.

        1. Fetch overview, sector rotation, macro data, sentiment
        2. Feed all data to LLM for synthesis
        3. Return structured report
        """
        logger.info(f"MarketAnalyst analysing market: {market}")

        # ── 1. Fetch data (failures degrade gracefully) ─────────────────────
        overview = await self._safe_tool("get_market_overview", market=market)
        sectors  = await self._safe_tool("get_sector_rotation", top_n=10)
        macro    = await self._safe_tool("get_global_macro", indicator="pmi")
        sentiment = await self._safe_tool("analyze_sentiment")

        # ── 2. LLM synthesis ─────────────────────────────────────────────────
        prompt = f"""Analyse the following live market data and produce a market report.

Market overview ({market}):
{overview}

Sector rotation (top gainers / losers):
{sectors}

PMI macro data:
{macro}

Market sentiment:
{sentiment}

Return a JSON object with exactly these keys:
{{
  "trend": "BULL" | "BEAR" | "SIDEWAYS",
  "trend_confidence": <0.0-1.0>,
  "hot_sectors": ["sector1", "sector2"],
  "weak_sectors": ["sector1"],
  "macro_risk": "LOW" | "MEDIUM" | "HIGH",
  "strategy_bias": "AGGRESSIVE" | "NEUTRAL" | "DEFENSIVE",
  "key_observations": ["obs1", "obs2", "obs3"],
  "timestamp": "{datetime.now().isoformat()}"
}}"""

        schema = {
            "type": "object",
            "properties": {
                "trend": {"type": "string"},
                "trend_confidence": {"type": "number"},
                "hot_sectors": {"type": "array", "items": {"type": "string"}},
                "weak_sectors": {"type": "array", "items": {"type": "string"}},
                "macro_risk": {"type": "string"},
                "strategy_bias": {"type": "string"},
                "key_observations": {"type": "array", "items": {"type": "string"}},
                "timestamp": {"type": "string"},
            },
        }

        try:
            report = await self.ask_llm_structured(prompt, schema)
        except Exception as e:
            logger.error(f"MarketAnalyst LLM failed: {e}")
            report = self._fallback_report(overview, sectors)

        report["market"] = market
        report["agent"]  = self.name
        logger.info(f"MarketAnalyst done: trend={report.get('trend')}, risk={report.get('macro_risk')}")
        return report

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _fallback_report(overview, sectors) -> dict:
        """Return a neutral fallback when LLM is unavailable."""
        return {
            "trend": "SIDEWAYS",
            "trend_confidence": 0.5,
            "hot_sectors": [],
            "weak_sectors": [],
            "macro_risk": "MEDIUM",
            "strategy_bias": "NEUTRAL",
            "key_observations": ["Data unavailable – using fallback"],
            "timestamp": datetime.now().isoformat(),
        }
