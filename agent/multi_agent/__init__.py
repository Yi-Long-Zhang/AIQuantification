"""
Multi-Agent System Package

This package implements the multi-agent system for quantitative trading.
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
