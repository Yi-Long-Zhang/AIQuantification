"""
Multi-Agent System Package

This package implements the multi-agent system for quantitative trading.
"""

from .base import BaseAgent
from .communication import AgentMessage, MessageBroker, MessageType, MessagePriority
from .coordinator import CoordinatorAgent

__all__ = [
    'BaseAgent',
    'AgentMessage', 'MessageBroker', 'MessageType', 'MessagePriority',
    'CoordinatorAgent',
]
