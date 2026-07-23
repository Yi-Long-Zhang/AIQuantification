"""
Research Agent 3 / 5 — NewsAnalystAgent

Responsibilities:
- Fetch and analyse recent market and stock-level news
- Compute sentiment score per symbol
- Flag high-impact events (earnings, FDA, Fed)
- Output sentiment signals consumed by the Strategy team
"""

from __future__ import annotations

import logging
from datetime import datetime

from agent.multi_agent.base import BaseAgent
from agent.llm_client import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a financial news analyst specialised in quantitative sentiment scoring.

For each news batch:
1. Compute sentiment score: -1 (very negative) to +1 (very positive)
2. Classify event impact: LOW / MEDIUM / HIGH / CRITICAL
3. Extract top 3 key themes
4. Trading implication: BULLISH / BEARISH / NEUTRAL

Weights: regulatory/policy > earnings > analyst ratings > general news.

Output ONLY valid JSON: {"market_sentiment": {"score": 0.3, "label": "SLIGHTLY_BULLISH", "key_themes": ["AI boom", "rate cuts"]}, "symbol_sentiments": [{"symbol": "AAPL", "score": 0.5, "impact": "MEDIUM"}], "risk_events": ["geopolitical tension"], "timestamp": "..."}
"""


class NewsAnalystAgent(BaseAgent):
    """Fetches news and converts it into structured sentiment signals."""

    TOOLS = [
        "get_market_news",
        "get_stock_news",
        "analyze_sentiment",
    ]

    def __init__(self, llm_client: LLMClient):
        super().__init__(
            name="NewsAnalyst",
            llm_client=llm_client,
            tools=self.TOOLS,
            system_prompt=SYSTEM_PROMPT,
        )

    # ── BaseAgent implementation ──────────────────────────────────────────────

    async def _analyze(self, input_data: dict, context: dict) -> dict:
        market   = input_data.get("market", "us_stock")
        symbols  = input_data.get("symbols", [])
        return await self.analyze_news(market, symbols)

    async def _decide(self, input_data: dict, context: dict) -> dict:
        return await self._analyze(input_data, context)

    async def _evaluate(self, input_data: dict, context: dict) -> dict:
        return await self._analyze(input_data, context)

    # ── Core logic ────────────────────────────────────────────────────────────

    async def analyze_news(
        self,
        market: str = "us_stock",
        symbols: list[str] | None = None,
    ) -> dict:
        """
        News sentiment pipeline.

        1. Fetch market-wide news
        2. Fetch per-symbol news for top candidates
        3. LLM rates sentiment and identifies events
        """
        symbols = symbols or []
        logger.info(f"NewsAnalyst fetching news for {market}, symbols={symbols[:5]}")

        # ── 1. Market-level news ─────────────────────────────────────────────
        market_news = await self._safe_tool("get_market_news", category="general", limit=10)
        sentiment   = await self._safe_tool("analyze_sentiment")

        # ── 2. Per-symbol news ───────────────────────────────────────────────
        symbol_news: dict[str, list] = {}
        for sym in symbols[:5]:          # limit to top 5 to avoid rate limits
            news = await self._safe_tool("get_stock_news", symbol=sym, limit=5)
            symbol_news[sym] = news if isinstance(news, list) else []

        # ── 3. LLM analysis ──────────────────────────────────────────────────
        prompt = f"""Analyse the following financial news and produce a sentiment report.

Market-wide news ({market}):
{market_news}

Overall market sentiment indicator:
{sentiment}

Per-symbol news:
{symbol_news}

Return a JSON object:
{{
  "market_sentiment": {{
    "score": <-1.0 to +1.0>,
    "label": "BULLISH" | "BEARISH" | "NEUTRAL",
    "key_themes": ["theme1", "theme2"]
  }},
  "symbol_sentiments": [
    {{
      "symbol": "...",
      "score": <-1.0 to +1.0>,
      "impact": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
      "key_points": ["point1", "point2"],
      "implication": "BULLISH" | "BEARISH" | "NEUTRAL"
    }}
  ],
  "risk_events": ["event1", "event2"],
  "timestamp": "{datetime.now().isoformat()}"
}}"""

        schema = {
            "type": "object",
            "properties": {
                "market_sentiment": {"type": "object"},
                "symbol_sentiments": {"type": "array"},
                "risk_events": {"type": "array", "items": {"type": "string"}},
                "timestamp": {"type": "string"},
            },
        }

        try:
            report = await self.ask_llm_structured(prompt, schema)
        except Exception as e:
            logger.error(f"NewsAnalyst LLM failed: {e}")
            report = self._fallback_report()

        report["agent"]  = self.name
        report["market"] = market
        logger.info(f"NewsAnalyst done: market_sentiment={report.get('market_sentiment', {}).get('label')}")
        return report

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _fallback_report() -> dict:
        return {
            "market_sentiment":  {"score": 0.0, "label": "NEUTRAL", "key_themes": []},
            "symbol_sentiments": [],
            "risk_events":       [],
            "timestamp":         datetime.now().isoformat(),
        }
