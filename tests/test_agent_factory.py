"""
Agent Factory unit tests.
"""
from __future__ import annotations

import pytest

from agent.multi_agent import CoordinatorAgent, MessageBroker
from agent.multi_agent.agent_factory import register_default_agents, AGENT_FACTORIES


@pytest.fixture
def coordinator():
    return CoordinatorAgent(llm_client=None, broker=MessageBroker())


def test_agent_factory_registry_complete():
    assert len(AGENT_FACTORIES) == 8
    assert set(AGENT_FACTORIES.keys()) == {
        "DataMiner", "TechnicalAnalyst", "FundamentalAnalyst",
        "NewsAnalyst", "MarketAnalyst", "Backtester",
        "PortfolioOptimizer", "RiskManager",
    }


def test_register_default_agents_registers_all(coordinator):
    registered = register_default_agents(coordinator, llm_client=None)
    assert len(registered) == 8
    assert set(registered) == set(AGENT_FACTORIES.keys())
    assert coordinator.list_agents() == registered


def test_register_respects_settings(coordinator):
    registered = register_default_agents(
        coordinator, llm_client=None,
        settings={"DataMiner": False, "RiskManager": False},
    )
    assert "DataMiner" not in registered
    assert "RiskManager" not in registered
    assert len(registered) == 6


def test_register_is_idempotent(coordinator):
    register_default_agents(coordinator, llm_client=None)
    names_first = coordinator.list_agents()
    register_default_agents(coordinator, llm_client=None)
    assert coordinator.list_agents() == names_first
