"""Strategy + Risk agent tests"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, AsyncMock

from agent.multi_agent.strategy import BacktesterAgent, PortfolioOptimizerAgent
from agent.multi_agent.risk import RiskManagerAgent


def mock_llm():
    llm = MagicMock()
    llm.chat = AsyncMock(return_value="test")
    return llm


class TestBacktesterAgent:
    def test_init(self):
        agent = BacktesterAgent(mock_llm())
        assert agent.name == "Backtester"
        assert "run_backtest" in agent.tools

    @pytest.mark.asyncio
    async def test_analyze_empty(self):
        agent = BacktesterAgent(mock_llm())
        result = await agent._analyze({"symbols": ["AAPL"], "strategies": ["sma_cross"]}, {})
        assert result["agent"] == "Backtester"


class TestPortfolioOptimizerAgent:
    def test_init(self):
        agent = PortfolioOptimizerAgent(mock_llm())
        assert agent.name == "PortfolioOptimizer"
        assert "calculate_position_size" in agent.tools

    @pytest.mark.asyncio
    async def test_analyze_empty_signals(self):
        agent = PortfolioOptimizerAgent(mock_llm())
        result = await agent._analyze({"signals": []}, {})
        assert result["allocations"] == []


class TestRiskManagerAgent:
    def test_init(self):
        agent = RiskManagerAgent(mock_llm())
        assert agent.name == "RiskManager"
        assert "check_constitution" in agent.tools

    @pytest.mark.asyncio
    async def test_analyze_empty_signals(self):
        agent = RiskManagerAgent(mock_llm())
        result = await agent._analyze({"signals": []}, {})
        assert result["approved_signals"] == 0
