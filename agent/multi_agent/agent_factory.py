"""
Agent Factory — Instantiate and register all specialist agents.

Centralizes agent wiring so the scheduler and API routes share one
registration path. Each agent takes an LLM client and registers with the
Coordinator under its canonical name.
"""

from __future__ import annotations

import logging
from typing import Any

from agent.llm_client import LLMClient
from agent.multi_agent.base import BaseAgent
from agent.multi_agent.coordinator import CoordinatorAgent
from agent.multi_agent.research import (
    DataMinerAgent,
    FundamentalAnalystAgent,
    MarketAnalystAgent,
    NewsAnalystAgent,
    TechnicalAnalystAgent,
)
from agent.multi_agent.strategy.backtester import BacktesterAgent
from agent.multi_agent.strategy.portfolio import PortfolioOptimizerAgent
from agent.multi_agent.risk.risk_manager import RiskManagerAgent

logger = logging.getLogger(__name__)

# Agent class registry keyed by canonical name. `enabled` can be overridden
# via coordinator context ("agent_settings") for selective registration.
AGENT_FACTORIES: dict[str, tuple[type[BaseAgent], bool]] = {
    "DataMiner": (DataMinerAgent, True),
    "TechnicalAnalyst": (TechnicalAnalystAgent, True),
    "FundamentalAnalyst": (FundamentalAnalystAgent, True),
    "NewsAnalyst": (NewsAnalystAgent, True),
    "MarketAnalyst": (MarketAnalystAgent, True),
    "Backtester": (BacktesterAgent, True),
    "PortfolioOptimizer": (PortfolioOptimizerAgent, True),
    "RiskManager": (RiskManagerAgent, True),
}


def register_default_agents(
    coordinator: CoordinatorAgent,
    llm_client: LLMClient,
    settings: dict[str, Any] | None = None,
) -> list[str]:
    """
    Instantiate and register all enabled agents onto the coordinator.

    Args:
        coordinator: CoordinatorAgent to register agents onto.
        llm_client: Shared LLM client for all agents.
        settings: Optional per-agent enabled flags, e.g.
            {"DataMiner": True, "RiskManager": False}. Defaults to all enabled.

    Returns:
        List of registered agent names.
    """
    settings = settings or {}
    registered: list[str] = []
    for name, (factory, default_enabled) in AGENT_FACTORIES.items():
        enabled = settings.get(name, default_enabled)
        if not enabled:
            logger.info("Agent %s disabled by settings", name)
            continue
        agent = factory(llm_client)
        coordinator.register_agent(agent)
        registered.append(name)
        logger.info("Agent registered: %s", name)
    logger.info("Registered %d agents: %s", len(registered), ", ".join(registered))
    return registered
