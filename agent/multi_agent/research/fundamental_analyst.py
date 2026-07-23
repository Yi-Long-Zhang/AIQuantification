"""
Research Agent 5 / 5 — FundamentalAnalystAgent

Responsibilities:
- Analyze fundamental valuation of symbols (PE, PB, ROE, earnings growth)
- Rate investment quality (STRONG_BUY / BUY / HOLD / SELL)
- Provide long-term value perspective to complement technical signals
"""

from __future__ import annotations

import logging
from datetime import datetime

from agent.multi_agent.base import BaseAgent
from agent.llm_client import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a fundamental investment analyst in a quantitative trading system.

For each symbol, analyze:
1. Valuation: PE/PB vs sector, historical percentile → CHEAP / FAIR / EXPENSIVE
2. Growth: revenue/EPS trend, margin expansion → HIGH / MEDIUM / LOW
3. Financial health: debt ratio, cash flow, ROE → STRONG / STABLE / WEAK
4. Macro exposure: sector sensitivity to rates/inflation/PMI

Output ONLY valid JSON: [{"symbol": "AAPL", "overall_rating": "BUY", "valuation": "FAIR", "growth_quality": "HIGH", "fundamental_score": 78, "key_strengths": ["high ROE"], "key_risks": ["revenue concentration"]}]
"""


class FundamentalAnalystAgent(BaseAgent):
    """Evaluates fundamental quality and valuation of candidate symbols."""

    TOOLS = [
        "get_stock_quote",
        "get_global_macro",
        "get_sector_rotation",
        "get_market_news",
    ]

    def __init__(self, llm_client: LLMClient):
        super().__init__(
            name="FundamentalAnalyst",
            llm_client=llm_client,
            tools=self.TOOLS,
            system_prompt=SYSTEM_PROMPT,
        )

    # ── BaseAgent implementation ──────────────────────────────────────────────

    async def _analyze(self, input_data: dict, context: dict) -> dict:
        market   = input_data.get("market", "us_stock")
        symbols  = input_data.get("symbols", [])
        # Accept candidates forwarded from DataMiner
        candidates = (
            input_data.get("research", {})
            .get("agents", {})
            .get("DataMiner", {})
            .get("output", {})
            .get("candidates", [])
        )
        if candidates:
            symbols = [c["symbol"] for c in candidates]
        return await self.analyze_fundamentals(symbols, market)

    async def _decide(self, input_data: dict, context: dict) -> dict:
        return await self._analyze(input_data, context)

    async def _evaluate(self, input_data: dict, context: dict) -> dict:
        return await self._analyze(input_data, context)

    # ── Core logic ────────────────────────────────────────────────────────────

    async def analyze_fundamentals(
        self,
        symbols: list[str],
        market: str = "us_stock",
    ) -> dict:
        """
        Fundamental analysis pipeline.

        1. Fetch quote data (price, market-cap as proxy)
        2. Fetch macro context (GDP / CPI trend)
        3. LLM rates each symbol's fundamentals
        """
        if not symbols:
            return {"agent": self.name, "ratings": [], "timestamp": datetime.now().isoformat()}

        logger.info(f"FundamentalAnalyst analysing {len(symbols)} symbols in {market}")

        # ── 1. Collect quote data ─────────────────────────────────────────────
        quotes = []
        for sym in symbols[:8]:
            q = await self._safe_tool("get_stock_quote", symbol=sym, market=market)
            quotes.append({"symbol": sym, "quote": q})

        # ── 2. Macro context ──────────────────────────────────────────────────
        macro_gdp = await self._safe_tool("get_global_macro", indicator="gdp")
        macro_cpi = await self._safe_tool("get_global_macro", indicator="cpi")

        # ── 3. LLM fundamental rating ─────────────────────────────────────────
        prompt = f"""Rate the fundamental quality of the following symbols.

Quotes and available data:
{quotes}

Macro context:
GDP trend: {macro_gdp}
CPI trend: {macro_cpi}

For each symbol return a JSON object in this array:
[
  {{
    "symbol": "...",
    "overall_rating": "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL",
    "valuation": "CHEAP" | "FAIR" | "EXPENSIVE",
    "growth_quality": "HIGH" | "MEDIUM" | "LOW",
    "fundamental_score": <0-100>,
    "key_strengths": ["..."],
    "key_risks": ["..."],
    "confidence": <0.0-1.0>
  }}
]"""

        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "symbol":            {"type": "string"},
                    "overall_rating":    {"type": "string"},
                    "valuation":         {"type": "string"},
                    "growth_quality":    {"type": "string"},
                    "fundamental_score": {"type": "number"},
                    "key_strengths":     {"type": "array", "items": {"type": "string"}},
                    "key_risks":         {"type": "array", "items": {"type": "string"}},
                    "confidence":        {"type": "number"},
                },
            },
        }

        try:
            ratings = await self.ask_llm_structured(prompt, schema)
            if not isinstance(ratings, list):
                ratings = []
        except Exception as e:
            logger.error(f"FundamentalAnalyst LLM failed: {e}")
            ratings = [
                {"symbol": q["symbol"], "overall_rating": "HOLD",
                 "fundamental_score": 50, "confidence": 0.4}
                for q in quotes
            ]

        result = {
            "agent":     self.name,
            "market":    market,
            "ratings":   ratings,
            "timestamp": datetime.now().isoformat(),
        }
        logger.info(f"FundamentalAnalyst done: {len(ratings)} ratings")
        return result

    # ── Helpers ───────────────────────────────────────────────────────────────
