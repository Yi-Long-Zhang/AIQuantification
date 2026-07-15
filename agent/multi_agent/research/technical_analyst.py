"""
Research Agent 4 / 5 — TechnicalAnalystAgent

Responsibilities:
- Fetch K-line data for candidate symbols
- Compute technical indicators (SMA, EMA, RSI, MACD, Bollinger, ATR)
- Detect trend direction, support/resistance levels
- Provide per-symbol technical signals
"""

from __future__ import annotations

import logging
from datetime import datetime

from agent.multi_agent.base import BaseAgent
from agent.llm_client import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a technical analysis specialist in a quantitative trading system.

For each symbol you receive K-line data and computed indicators.
Produce a structured technical signal with:
- trend direction (UP / DOWN / SIDEWAYS)
- signal strength (STRONG / MODERATE / WEAK)
- key support and resistance levels
- indicator summary (SMA cross, RSI zone, MACD alignment)
- entry recommendation (BUY / SELL / WAIT)

Output ONLY valid JSON.
"""


class TechnicalAnalystAgent(BaseAgent):
    """Computes technical indicators and generates per-symbol entry signals."""

    TOOLS = [
        "get_klines",
        "get_cn_klines",
        "calculate_indicators",
        "calculate_factor",
    ]

    def __init__(self, llm_client: LLMClient):
        super().__init__(
            name="TechnicalAnalyst",
            llm_client=llm_client,
            tools=self.TOOLS,
            system_prompt=SYSTEM_PROMPT,
        )

    # ── BaseAgent implementation ──────────────────────────────────────────────

    async def _analyze(self, input_data: dict, context: dict) -> dict:
        market    = input_data.get("market", "us_stock")
        symbols   = input_data.get("symbols", [])
        candidates = input_data.get("research", {}).get("agents", {}).get(
            "DataMiner", {}
        ).get("output", {}).get("candidates", [])
        if candidates:
            symbols = [c["symbol"] for c in candidates]
        return await self.analyze_technicals(symbols, market)

    async def _decide(self, input_data: dict, context: dict) -> dict:
        return await self._analyze(input_data, context)

    async def _evaluate(self, input_data: dict, context: dict) -> dict:
        return await self._analyze(input_data, context)

    # ── Core logic ────────────────────────────────────────────────────────────

    async def analyze_technicals(
        self,
        symbols: list[str],
        market: str = "us_stock",
        interval: str = "1d",
        period: str = "3mo",
    ) -> dict:
        """
        Technical analysis pipeline for a list of symbols.
        """
        if not symbols:
            return {"agent": self.name, "signals": [], "timestamp": datetime.now().isoformat()}

        logger.info(f"TechnicalAnalyst analysing {len(symbols)} symbols")

        # ── Collect indicators per symbol ─────────────────────────────────────
        symbol_data = []
        for sym in symbols[:8]:     # cap at 8 to stay within token budget
            klines = await self._safe_klines(sym, market, interval, period)
            indics = await self._safe_tool("calculate_indicators", symbol=sym, market=market)
            symbol_data.append({
                "symbol":     sym,
                "klines_len": len(klines) if isinstance(klines, list) else 0,
                "klines_tail": klines[-5:] if isinstance(klines, list) and klines else [],
                "indicators": indics,
            })

        # ── LLM synthesis ─────────────────────────────────────────────────────
        prompt = f"""Analyse the technical data below and produce a signal for each symbol.

Symbols and their latest K-lines + indicators:
{symbol_data}

For each symbol return a JSON object in this array:
[
  {{
    "symbol": "...",
    "trend": "UP" | "DOWN" | "SIDEWAYS",
    "strength": "STRONG" | "MODERATE" | "WEAK",
    "support": <price or null>,
    "resistance": <price or null>,
    "rsi_zone": "OVERSOLD" | "NEUTRAL" | "OVERBOUGHT",
    "macd_signal": "BULLISH" | "BEARISH" | "NEUTRAL",
    "sma_cross": "GOLDEN" | "DEATH" | "NONE",
    "entry": "BUY" | "SELL" | "WAIT",
    "confidence": <0.0-1.0>
  }}
]"""

        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "symbol":     {"type": "string"},
                    "trend":      {"type": "string"},
                    "strength":   {"type": "string"},
                    "support":    {"type": ["number", "null"]},
                    "resistance": {"type": ["number", "null"]},
                    "rsi_zone":   {"type": "string"},
                    "macd_signal":{"type": "string"},
                    "sma_cross":  {"type": "string"},
                    "entry":      {"type": "string"},
                    "confidence": {"type": "number"},
                },
            },
        }

        try:
            signals = await self.ask_llm_structured(prompt, schema)
            if not isinstance(signals, list):
                signals = []
        except Exception as e:
            logger.error(f"TechnicalAnalyst LLM failed: {e}")
            signals = [{"symbol": s["symbol"], "trend": "SIDEWAYS",
                        "entry": "WAIT", "confidence": 0.5} for s in symbol_data]

        result = {
            "agent":     self.name,
            "market":    market,
            "signals":   signals,
            "timestamp": datetime.now().isoformat(),
        }
        logger.info(f"TechnicalAnalyst done: {len(signals)} signals")
        return result

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _safe_klines(self, symbol: str, market: str, interval: str, period: str):
        """Use market-appropriate kline tool."""
        try:
            if market == "cn_stock":
                return await self.call_tool("get_cn_klines", symbol=symbol,
                                            interval="daily", period=period)
            return await self.call_tool("get_klines", symbol=symbol,
                                        market=market, interval=interval, period=period)
        except Exception as e:
            logger.warning(f"K-line fetch failed for {symbol}: {e}")
            return []

    async def _safe_tool(self, tool_name: str, **kwargs):
        try:
            return await self.call_tool(tool_name, **kwargs)
        except Exception as e:
            logger.warning(f"Tool {tool_name} failed: {e}")
            return {}
