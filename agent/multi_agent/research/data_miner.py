"""
Research Agent 2 / 5 — DataMinerAgent

Responsibilities:
- Screen a watchlist for high-scoring multi-factor candidates
- Compute alpha factors, technical indicators, and momentum scores
- Return a ranked shortlist for the Strategy team
"""

from __future__ import annotations

import logging
from datetime import datetime

from agent.multi_agent.base import BaseAgent
from agent.llm_client import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a quantitative data-mining specialist.

Your workflow:
1. Fetch quote + compute alpha factors for each symbol in watchlist
2. Score each candidate: momentum (30%), quality (30%), risk (20%), volume (20%)
3. Filter candidates with composite score < 40
4. Return top N ranked candidates

Output ONLY a valid JSON array: [{"symbol": "AAPL", "market": "us_stock", "momentum_score": 80, "quality_score": 75, "risk_score": 60, "composite_score": 72, "reasoning": "strong momentum + solid fundamentals"}]
"""

# Default watchlist per market (expandable)
DEFAULT_WATCHLIST: dict[str, list[str]] = {
    "us_stock": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "AMD", "CRM", "NFLX"],
    "cn_stock": ["600519", "000001", "300750", "600036", "601318"],
    "hk_stock": ["00700", "09988", "01810", "02318", "00005"],
    "crypto":   ["BTC", "ETH", "BNB", "SOL", "XRP"],
}


class DataMinerAgent(BaseAgent):
    """Screens symbols with multi-factor scoring and returns ranked candidates."""

    TOOLS = [
        "get_stock_quote",
        "get_klines",
        "compute_alpha_factors",
        "calculate_indicators",
        "calculate_factor",
    ]

    def __init__(self, llm_client: LLMClient):
        super().__init__(
            name="DataMiner",
            llm_client=llm_client,
            tools=self.TOOLS,
            system_prompt=SYSTEM_PROMPT,
        )

    # ── BaseAgent implementation ──────────────────────────────────────────────

    async def _analyze(self, input_data: dict, context: dict) -> dict:
        market = input_data.get("market", "us_stock")
        watchlist = input_data.get("watchlist", DEFAULT_WATCHLIST.get(market, []))
        top_n = input_data.get("top_n", 10)
        return await self.mine_candidates(market, watchlist, top_n)

    async def _decide(self, input_data: dict, context: dict) -> dict:
        return await self._analyze(input_data, context)

    async def _evaluate(self, input_data: dict, context: dict) -> dict:
        return await self._analyze(input_data, context)

    # ── Core logic ────────────────────────────────────────────────────────────

    async def mine_candidates(
        self,
        market: str = "us_stock",
        watchlist: list[str] | None = None,
        top_n: int = 10,
    ) -> dict:
        """
        Multi-factor screening pipeline.

        1. Fetch quotes for all symbols in watchlist
        2. Compute factor scores per symbol
        3. Ask LLM to rank and filter
        4. Return top_n candidates
        """
        watchlist = watchlist or DEFAULT_WATCHLIST.get(market, [])
        logger.info(f"DataMiner screening {len(watchlist)} symbols for {market}")

        # ── 1. Collect data for each symbol ──────────────────────────────────
        raw_data = []
        for symbol in watchlist:
            quote    = await self._safe_tool("get_stock_quote",  symbol=symbol, market=market)
            factors  = await self._safe_tool("compute_alpha_factors", symbol=symbol, market=market, factor_set="alpha101")
            raw_data.append({
                "symbol":  symbol,
                "market":  market,
                "quote":   quote,
                "factors": factors,
            })

        # ── 2. LLM ranking ───────────────────────────────────────────────────
        prompt = f"""You are screening {len(raw_data)} symbols for the {market} market.

Raw data per symbol:
{raw_data}

Score each symbol (0-100) across:
- momentum_score: recent price momentum
- quality_score: factor quality / consistency
- risk_score: volatility risk (lower is better)
- composite_score: weighted average (40% momentum, 40% quality, 20% inverse-risk)

Return a JSON array of the top {top_n} candidates, sorted by composite_score descending:
[
  {{
    "symbol": "...",
    "market": "{market}",
    "momentum_score": 0-100,
    "quality_score": 0-100,
    "risk_score": 0-100,
    "composite_score": 0-100,
    "reasoning": "one-line justification"
  }},
  ...
]"""

        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "symbol":          {"type": "string"},
                    "market":          {"type": "string"},
                    "momentum_score":  {"type": "number"},
                    "quality_score":   {"type": "number"},
                    "risk_score":      {"type": "number"},
                    "composite_score": {"type": "number"},
                    "reasoning":       {"type": "string"},
                },
            },
        }

        try:
            candidates = await self.ask_llm_structured(prompt, schema)
            if not isinstance(candidates, list):
                candidates = candidates.get("candidates", []) if isinstance(candidates, dict) else []
        except Exception as e:
            logger.error(f"DataMiner LLM failed: {e}")
            candidates = self._fallback_candidates(watchlist, market)

        result = {
            "agent":       self.name,
            "market":      market,
            "scanned":     len(watchlist),
            "candidates":  candidates[:top_n],
            "timestamp":   datetime.now().isoformat(),
        }
        logger.info(f"DataMiner done: {len(result['candidates'])} candidates from {len(watchlist)} symbols")
        return result

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _fallback_candidates(watchlist: list[str], market: str) -> list[dict]:
        """Return equal-weighted candidates when LLM fails."""
        return [
            {
                "symbol": s, "market": market,
                "momentum_score": 50, "quality_score": 50,
                "risk_score": 50, "composite_score": 50,
                "reasoning": "fallback – LLM unavailable",
            }
            for s in watchlist[:5]
        ]
