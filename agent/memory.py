"""
Agent Memory — SQLite + FTS5 storage for sessions, messages, trades, knowledge.

This module re-exports from the split modules for backward compatibility:
  - memory_sql.py:   SQL constants + helper functions
  - memory_async.py: AsyncAgentMemory (aiosqlite)
  - memory_sync.py:  AgentMemory (stdlib sqlite3)
"""

from __future__ import annotations

from .memory_sql import SQL_SCHEMA, SQL_FTS5_TABLES, SQL_FTS5_TRIGGERS
from .memory_async import AsyncAgentMemory
from .memory_sync import AgentMemory

__all__ = [
    "AsyncAgentMemory",
    "AgentMemory",
    "SQL_SCHEMA",
    "SQL_FTS5_TABLES",
    "SQL_FTS5_TRIGGERS",
]
