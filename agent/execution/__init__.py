"""
Execution Package — Convert trading decisions into broker orders.

Bridges the multi-agent decision output (final_decision.decisions) to the
PaperBroker order API. Supports dry-run (default) and live execution modes.
"""

from .order_executor import OrderExecutor, ExecutionReport

__all__ = ["OrderExecutor", "ExecutionReport"]
