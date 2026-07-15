"""
Tests for Phase 2 — Research Team Agents

Uses lightweight mocks so tests run without network access.
"""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent.multi_agent.research import (
    MarketAnalystAgent,
    DataMinerAgent,
    NewsAnalystAgent,
    FundamentalAnalystAgent,
    TechnicalAnalystAgent,
)
from agent.llm_client import LLMClient
from agent.config import settings


# ── Shared fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def llm():
    return LLMClient(provider=settings.llm_provider)


def _mock_llm_response(obj):
    """Patch ask_llm_structured to return a fixed value synchronously."""
    async def _fake(*args, **kwargs):
        return obj
    return _fake


# ── MarketAnalystAgent ─────────────────────────────────────────────────────────

class TestMarketAnalystAgent:

    def test_init(self, llm):
        agent = MarketAnalystAgent(llm)
        assert agent.name == "MarketAnalyst"
        assert "get_market_overview" in agent.tools

    @pytest.mark.asyncio
    async def test_analyze_returns_required_fields(self, llm):
        agent = MarketAnalystAgent(llm)

        fixed = {
            "trend": "BULL", "trend_confidence": 0.8,
            "hot_sectors": ["Tech"], "weak_sectors": [],
            "macro_risk": "LOW", "strategy_bias": "AGGRESSIVE",
            "key_observations": ["Markets up"], "timestamp": "2026-07-15T00:00:00",
        }
        agent.ask_llm_structured = _mock_llm_response(fixed)

        # Tools return empty dicts (network unavailable)
        with patch.object(agent, 'call_tool', new=AsyncMock(return_value={})):
            result = await agent.analyze_market("us_stock")

        assert result["trend"] in ("BULL", "BEAR", "SIDEWAYS")
        assert "macro_risk" in result
        assert result["agent"] == "MarketAnalyst"

    @pytest.mark.asyncio
    async def test_execute_analyze_task(self, llm):
        agent = MarketAnalystAgent(llm)
        agent.ask_llm_structured = _mock_llm_response({
            "trend": "SIDEWAYS", "trend_confidence": 0.5,
            "hot_sectors": [], "weak_sectors": [],
            "macro_risk": "MEDIUM", "strategy_bias": "NEUTRAL",
            "key_observations": [], "timestamp": "2026-07-15T00:00:00",
        })
        with patch.object(agent, 'call_tool', new=AsyncMock(return_value={})):
            result = await agent.execute({
                "task_id": "t1", "type": "analyze",
                "input": {"market": "us_stock"}, "context": {}
            })
        assert result["status"] == "SUCCESS"

    @pytest.mark.asyncio
    async def test_fallback_on_llm_error(self, llm):
        agent = MarketAnalystAgent(llm)

        async def _boom(*a, **k):
            raise ValueError("LLM down")

        agent.ask_llm_structured = _boom
        with patch.object(agent, 'call_tool', new=AsyncMock(return_value={})):
            result = await agent.analyze_market("us_stock")

        assert result["trend"] == "SIDEWAYS"
        assert result["strategy_bias"] == "NEUTRAL"


# ── DataMinerAgent ────────────────────────────────────────────────────────────

class TestDataMinerAgent:

    def test_init(self, llm):
        agent = DataMinerAgent(llm)
        assert agent.name == "DataMiner"
        assert "get_stock_quote" in agent.tools

    @pytest.mark.asyncio
    async def test_mine_returns_candidates(self, llm):
        agent = DataMinerAgent(llm)

        fixed = [
            {"symbol": "AAPL", "market": "us_stock",
             "momentum_score": 80, "quality_score": 75,
             "risk_score": 30, "composite_score": 77,
             "reasoning": "Strong momentum"},
        ]
        agent.ask_llm_structured = _mock_llm_response(fixed)
        with patch.object(agent, 'call_tool', new=AsyncMock(return_value={})):
            result = await agent.mine_candidates("us_stock", ["AAPL", "MSFT"], top_n=5)

        assert result["agent"] == "DataMiner"
        assert isinstance(result["candidates"], list)
        assert len(result["candidates"]) >= 1
        assert result["candidates"][0]["symbol"] == "AAPL"

    @pytest.mark.asyncio
    async def test_fallback_candidates_on_error(self, llm):
        agent = DataMinerAgent(llm)

        async def _boom(*a, **k):
            raise RuntimeError("LLM error")

        agent.ask_llm_structured = _boom
        with patch.object(agent, 'call_tool', new=AsyncMock(return_value={})):
            result = await agent.mine_candidates("us_stock", ["AAPL", "MSFT", "GOOGL"])

        assert len(result["candidates"]) > 0
        assert result["candidates"][0]["reasoning"] == "fallback – LLM unavailable"


# ── NewsAnalystAgent ──────────────────────────────────────────────────────────

class TestNewsAnalystAgent:

    def test_init(self, llm):
        agent = NewsAnalystAgent(llm)
        assert agent.name == "NewsAnalyst"
        assert "get_market_news" in agent.tools

    @pytest.mark.asyncio
    async def test_analyze_news_structure(self, llm):
        agent = NewsAnalystAgent(llm)

        fixed = {
            "market_sentiment": {"score": 0.3, "label": "BULLISH", "key_themes": ["AI boom"]},
            "symbol_sentiments": [
                {"symbol": "NVDA", "score": 0.8, "impact": "HIGH",
                 "key_points": ["Record earnings"], "implication": "BULLISH"}
            ],
            "risk_events": [],
            "timestamp": "2026-07-15T00:00:00",
        }
        agent.ask_llm_structured = _mock_llm_response(fixed)
        with patch.object(agent, 'call_tool', new=AsyncMock(return_value={})):
            result = await agent.analyze_news("us_stock", ["NVDA"])

        assert result["agent"] == "NewsAnalyst"
        assert "market_sentiment" in result
        assert result["market_sentiment"]["label"] in ("BULLISH", "BEARISH", "NEUTRAL")

    @pytest.mark.asyncio
    async def test_fallback_neutral_on_error(self, llm):
        agent = NewsAnalystAgent(llm)

        async def _boom(*a, **k):
            raise Exception("fail")

        agent.ask_llm_structured = _boom
        with patch.object(agent, 'call_tool', new=AsyncMock(return_value={})):
            result = await agent.analyze_news("us_stock", [])

        assert result["market_sentiment"]["label"] == "NEUTRAL"


# ── FundamentalAnalystAgent ────────────────────────────────────────────────────

class TestFundamentalAnalystAgent:

    def test_init(self, llm):
        agent = FundamentalAnalystAgent(llm)
        assert agent.name == "FundamentalAnalyst"

    @pytest.mark.asyncio
    async def test_analyze_fundamentals(self, llm):
        agent = FundamentalAnalystAgent(llm)

        fixed = [
            {"symbol": "AAPL", "overall_rating": "BUY", "valuation": "FAIR",
             "growth_quality": "HIGH", "fundamental_score": 78,
             "key_strengths": ["Strong cash flow"], "key_risks": ["Valuation"],
             "confidence": 0.8}
        ]
        agent.ask_llm_structured = _mock_llm_response(fixed)
        with patch.object(agent, 'call_tool', new=AsyncMock(return_value={})):
            result = await agent.analyze_fundamentals(["AAPL"], "us_stock")

        assert result["agent"] == "FundamentalAnalyst"
        assert len(result["ratings"]) == 1
        assert result["ratings"][0]["overall_rating"] == "BUY"

    @pytest.mark.asyncio
    async def test_empty_symbols_returns_empty_ratings(self, llm):
        agent = FundamentalAnalystAgent(llm)
        result = await agent.analyze_fundamentals([], "us_stock")
        assert result["ratings"] == []


# ── TechnicalAnalystAgent ──────────────────────────────────────────────────────

class TestTechnicalAnalystAgent:

    def test_init(self, llm):
        agent = TechnicalAnalystAgent(llm)
        assert agent.name == "TechnicalAnalyst"
        assert "get_klines" in agent.tools

    @pytest.mark.asyncio
    async def test_analyze_technicals(self, llm):
        agent = TechnicalAnalystAgent(llm)

        fixed = [
            {"symbol": "AAPL", "trend": "UP", "strength": "STRONG",
             "support": 175.0, "resistance": 190.0,
             "rsi_zone": "NEUTRAL", "macd_signal": "BULLISH",
             "sma_cross": "GOLDEN", "entry": "BUY", "confidence": 0.82}
        ]
        agent.ask_llm_structured = _mock_llm_response(fixed)
        with patch.object(agent, 'call_tool', new=AsyncMock(return_value=[])):
            result = await agent.analyze_technicals(["AAPL"], "us_stock")

        assert result["agent"] == "TechnicalAnalyst"
        assert len(result["signals"]) == 1
        assert result["signals"][0]["entry"] == "BUY"

    @pytest.mark.asyncio
    async def test_empty_symbols(self, llm):
        agent = TechnicalAnalystAgent(llm)
        result = await agent.analyze_technicals([], "us_stock")
        assert result["signals"] == []


# ── Integration: all 5 agents run in parallel ─────────────────────────────────

class TestResearchTeamIntegration:

    @pytest.mark.asyncio
    async def test_all_five_agents_parallel(self, llm):
        """All five research agents run concurrently without error."""

        def _make_mock(agent, return_val):
            agent.ask_llm_structured = _mock_llm_response(return_val)
            return agent

        market_agent = _make_mock(MarketAnalystAgent(llm), {
            "trend": "BULL", "trend_confidence": 0.7,
            "hot_sectors": ["Tech"], "weak_sectors": [],
            "macro_risk": "LOW", "strategy_bias": "AGGRESSIVE",
            "key_observations": [], "timestamp": "2026-07-15T00:00:00",
        })
        miner_agent = _make_mock(DataMinerAgent(llm), [
            {"symbol": "AAPL", "market": "us_stock",
             "momentum_score": 80, "quality_score": 75,
             "risk_score": 30, "composite_score": 77, "reasoning": "ok"}
        ])
        news_agent = _make_mock(NewsAnalystAgent(llm), {
            "market_sentiment": {"score": 0.2, "label": "BULLISH", "key_themes": []},
            "symbol_sentiments": [], "risk_events": [],
            "timestamp": "2026-07-15T00:00:00",
        })
        fund_agent = _make_mock(FundamentalAnalystAgent(llm), [
            {"symbol": "AAPL", "overall_rating": "BUY", "valuation": "FAIR",
             "growth_quality": "HIGH", "fundamental_score": 75,
             "key_strengths": [], "key_risks": [], "confidence": 0.7}
        ])
        tech_agent = _make_mock(TechnicalAnalystAgent(llm), [
            {"symbol": "AAPL", "trend": "UP", "strength": "MODERATE",
             "support": None, "resistance": None,
             "rsi_zone": "NEUTRAL", "macd_signal": "BULLISH",
             "sma_cross": "GOLDEN", "entry": "BUY", "confidence": 0.75}
        ])

        with patch.object(market_agent, 'call_tool', new=AsyncMock(return_value={})), \
             patch.object(miner_agent,  'call_tool', new=AsyncMock(return_value={})), \
             patch.object(news_agent,   'call_tool', new=AsyncMock(return_value={})), \
             patch.object(fund_agent,   'call_tool', new=AsyncMock(return_value={})), \
             patch.object(tech_agent,   'call_tool', new=AsyncMock(return_value=[])):

            tasks = [
                market_agent.execute({"task_id": "m", "type": "analyze",
                                      "input": {"market": "us_stock"}, "context": {}}),
                miner_agent.execute({"task_id": "d", "type": "analyze",
                                     "input": {"market": "us_stock"}, "context": {}}),
                news_agent.execute({"task_id": "n", "type": "analyze",
                                    "input": {"market": "us_stock"}, "context": {}}),
                fund_agent.execute({"task_id": "f", "type": "analyze",
                                    "input": {"market": "us_stock"}, "context": {}}),
                tech_agent.execute({"task_id": "t", "type": "analyze",
                                    "input": {"market": "us_stock"}, "context": {}}),
            ]
            results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r["status"] == "SUCCESS" for r in results)
