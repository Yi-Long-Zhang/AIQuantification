"""
Sync Agent Memory — SQLite + FTS5 using stdlib sqlite3.
"""

from __future__ import annotations

import json
import logging
import sqlite3

from .memory_sql import (
    SQL_SCHEMA, SQL_FTS5_TABLES, SQL_FTS5_TRIGGERS,
    _now, _parse_rows, _get_db_path,
)

logger = logging.getLogger(__name__)


class AgentMemory:
    def __init__(self, db_path: str | None = None):
        self._db_path = _get_db_path(db_path)
        self._conn = sqlite3.connect(self._db_path)
        self._init_db()

    def _init_db(self):
        self._conn.executescript(SQL_SCHEMA)
        try:
            self._conn.executescript(SQL_FTS5_TABLES)
            self._conn.executescript(SQL_FTS5_TRIGGERS)
        except Exception as e:
            logger.warning("FTS5 initialization failed (sync): %s", e)
        self._conn.commit()

    def create_session(self, session_id: str) -> None:
        now = _now()
        self._conn.execute(
            "INSERT OR IGNORE INTO sessions (session_id, created_at, updated_at) VALUES (?, ?, ?)",
            (session_id, now, now),
        )
        self._conn.commit()

    def save_message(self, session_id: str, role: str, content: str, metadata: dict | None = None) -> None:
        now = _now()
        self._conn.execute(
            "INSERT INTO messages (session_id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, json.dumps(metadata) if metadata else None, now),
        )
        self._conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE session_id = ?", (now, session_id)
        )
        self._conn.commit()

    def get_history(self, session_id: str, limit: int = 50) -> list[dict]:
        rows = self._conn.execute(
            "SELECT role, content, metadata, created_at FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return _parse_rows(rows, with_metadata=True)

    def save_trade(self, session_id: str, symbol: str, direction: str, confidence: float,
                   entry_price: float | None, reason: str) -> int:
        now = _now()
        cur = self._conn.execute(
            "INSERT INTO trades (session_id, symbol, direction, confidence, entry_price, reason, opened_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, symbol, direction, confidence, entry_price, reason, now),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_knowledge(self, market: str, symbol: str, key: str, value: str) -> None:
        now = _now()
        self._conn.execute(
            "INSERT INTO knowledge (market, symbol, key, value, created_at) VALUES (?, ?, ?, ?, ?)",
            (market, symbol, key, value, now),
        )
        self._conn.commit()

    def get_knowledge(self, market: str | None = None, symbol: str | None = None) -> list[dict]:
        query = "SELECT market, symbol, key, value FROM knowledge WHERE 1=1"
        params: list[str] = []
        if market:
            query += " AND market = ?"
            params.append(market)
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        rows = self._conn.execute(query, params).fetchall()
        return _parse_rows(rows, with_metadata=False)

    def search_history(self, keyword: str, session_id: str | None = None, limit: int = 20) -> list[dict]:
        if session_id:
            rows = self._conn.execute(
                """SELECT m.role, m.content, m.metadata, m.created_at
                   FROM messages_fts f
                   JOIN messages m ON m.id = f.rowid
                   WHERE messages_fts MATCH ? AND m.session_id = ?
                   ORDER BY m.id DESC LIMIT ?""",
                (keyword, session_id, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """SELECT m.role, m.content, m.metadata, m.created_at
                   FROM messages_fts f
                   JOIN messages m ON m.id = f.rowid
                   WHERE messages_fts MATCH ?
                   ORDER BY m.id DESC LIMIT ?""",
                (keyword, limit),
            ).fetchall()
        return _parse_rows(rows, with_metadata=True)

    def search_knowledge(self, keyword: str, market: str | None = None) -> list[dict]:
        if market:
            rows = self._conn.execute(
                """SELECT k.market, k.symbol, k.key, k.value
                   FROM knowledge_fts f
                   JOIN knowledge k ON k.id = f.rowid
                   WHERE knowledge_fts MATCH ? AND k.market = ?
                   ORDER BY k.id DESC""",
                (keyword, market),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """SELECT k.market, k.symbol, k.key, k.value
                   FROM knowledge_fts f
                   JOIN knowledge k ON k.id = f.rowid
                   WHERE knowledge_fts MATCH ?
                   ORDER BY k.id DESC""",
                (keyword,),
            ).fetchall()
        return [{"market": r[0], "symbol": r[1], "key": r[2], "value": r[3]} for r in rows]

    def close(self):
        self._conn.close()

    def rebuild_fts(self) -> None:
        try:
            self._conn.execute("INSERT INTO messages_fts(messages_fts) VALUES('rebuild')")
            self._conn.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('rebuild')")
            self._conn.commit()
        except Exception as e:
            logger.warning("FTS5 rebuild failed (sync): %s", e)
