"""
Async Agent Memory — SQLite + FTS5 using aiosqlite.
"""

from __future__ import annotations

import json
import logging

import aiosqlite

from .memory_sql import (
    SQL_SCHEMA, SQL_FTS5_TABLES, SQL_FTS5_TRIGGERS,
    _now, _parse_rows, _get_db_path,
)

logger = logging.getLogger(__name__)


class AsyncAgentMemory:
    def __init__(self, db_path: str | None = None):
        self._db_path = _get_db_path(db_path)
        self._conn: aiosqlite.Connection | None = None

    async def _get_conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            self._conn = await aiosqlite.connect(self._db_path)
            await self._conn.execute("PRAGMA journal_mode=WAL")
            await self._conn.execute("PRAGMA synchronous=NORMAL")
            await self._init_db(self._conn)
        return self._conn

    async def _init_db(self, conn: aiosqlite.Connection) -> None:
        await conn.executescript(SQL_SCHEMA)
        try:
            await conn.executescript(SQL_FTS5_TABLES)
            await conn.executescript(SQL_FTS5_TRIGGERS)
        except Exception as e:
            logger.warning("FTS5 initialization failed (async): %s", e)

    async def create_session(self, session_id: str) -> None:
        now = _now()
        conn = await self._get_conn()
        await conn.execute(
            "INSERT OR IGNORE INTO sessions (session_id, created_at, updated_at) VALUES (?, ?, ?)",
            (session_id, now, now),
        )
        await conn.commit()

    async def save_message(self, session_id: str, role: str, content: str, metadata: dict | None = None) -> None:
        now = _now()
        conn = await self._get_conn()
        await conn.execute(
            "INSERT INTO messages (session_id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, json.dumps(metadata) if metadata else None, now),
        )
        await conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE session_id = ?", (now, session_id)
        )
        await conn.commit()

    async def get_history(self, session_id: str, limit: int = 50) -> list[dict]:
        conn = await self._get_conn()
        cursor = await conn.execute(
            "SELECT role, content, metadata, created_at FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        )
        rows = await cursor.fetchall()
        return _parse_rows(rows, with_metadata=True)

    async def save_trade(self, session_id: str, symbol: str, direction: str, confidence: float,
                         entry_price: float | None, reason: str) -> int:
        now = _now()
        conn = await self._get_conn()
        cursor = await conn.execute(
            "INSERT INTO trades (session_id, symbol, direction, confidence, entry_price, reason, opened_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, symbol, direction, confidence, entry_price, reason, now),
        )
        await conn.commit()
        return cursor.lastrowid if cursor.lastrowid is not None else 0

    async def save_knowledge(self, market: str, symbol: str, key: str, value: str) -> None:
        now = _now()
        conn = await self._get_conn()
        await conn.execute(
            "INSERT INTO knowledge (market, symbol, key, value, created_at) VALUES (?, ?, ?, ?, ?)",
            (market, symbol, key, value, now),
        )
        await conn.commit()

    async def get_knowledge(self, market: str | None = None, symbol: str | None = None) -> list[dict]:
        query = "SELECT market, symbol, key, value FROM knowledge WHERE 1=1"
        params: list[str] = []
        if market:
            query += " AND market = ?"
            params.append(market)
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        conn = await self._get_conn()
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        return _parse_rows(rows, with_metadata=False)

    async def search_history(self, keyword: str, session_id: str | None = None, limit: int = 20) -> list[dict]:
        conn = await self._get_conn()
        if session_id:
            cursor = await conn.execute(
                """SELECT m.role, m.content, m.metadata, m.created_at
                   FROM messages_fts f
                   JOIN messages m ON m.id = f.rowid
                   WHERE messages_fts MATCH ? AND m.session_id = ?
                   ORDER BY m.id DESC LIMIT ?""",
                (keyword, session_id, limit),
            )
        else:
            cursor = await conn.execute(
                """SELECT m.role, m.content, m.metadata, m.created_at
                   FROM messages_fts f
                   JOIN messages m ON m.id = f.rowid
                   WHERE messages_fts MATCH ?
                   ORDER BY m.id DESC LIMIT ?""",
                (keyword, limit),
            )
        rows = await cursor.fetchall()
        return _parse_rows(rows, with_metadata=True)

    async def search_knowledge(self, keyword: str, market: str | None = None) -> list[dict]:
        conn = await self._get_conn()
        if market:
            cursor = await conn.execute(
                """SELECT k.market, k.symbol, k.key, k.value
                   FROM knowledge_fts f
                   JOIN knowledge k ON k.id = f.rowid
                   WHERE knowledge_fts MATCH ? AND k.market = ?
                   ORDER BY k.id DESC""",
                (keyword, market),
            )
        else:
            cursor = await conn.execute(
                """SELECT k.market, k.symbol, k.key, k.value
                   FROM knowledge_fts f
                   JOIN knowledge k ON k.id = f.rowid
                   WHERE knowledge_fts MATCH ?
                   ORDER BY k.id DESC""",
                (keyword,),
            )
        rows = await cursor.fetchall()
        return _parse_rows(rows, with_metadata=False)

    async def close(self):
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def rebuild_fts(self) -> None:
        conn = await self._get_conn()
        try:
            await conn.execute("INSERT INTO messages_fts(messages_fts) VALUES('rebuild')")
            await conn.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('rebuild')")
            await conn.commit()
        except Exception as e:
            logger.warning("FTS5 rebuild failed (async): %s", e)
