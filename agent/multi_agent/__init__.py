"""
Multi-Agent System Package

This package implements the multi-agent system for quantitative trading.
NOTE: imports at module level — if agent.tools or agent.broker ever
reference multi_agent, convert these to lazy imports to avoid cycles.
"""

from .base import BaseAgent
from .communication import AgentMessage, MessageBroker, MessageType, MessagePriority
from .coordinator import CoordinatorAgent
from .research import (
    MarketAnalystAgent,
    DataMinerAgent,
    NewsAnalystAgent,
    FundamentalAnalystAgent,
    TechnicalAnalystAgent,
)

__all__ = [
    'BaseAgent',
    'AgentMessage', 'MessageBroker', 'MessageType', 'MessagePriority',
    'CoordinatorAgent',
    'MarketAnalystAgent', 'DataMinerAgent', 'NewsAnalystAgent',
    'FundamentalAnalystAgent', 'TechnicalAnalystAgent',
]
