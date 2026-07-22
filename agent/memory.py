from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

# ── Shared SQL Constants ─────────────────────────────────────────────────────

SQL_SCHEMA = """
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT,
        metadata TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        symbol TEXT NOT NULL,
        direction TEXT NOT NULL,
        confidence REAL,
        entry_price REAL,
        exit_price REAL,
        pnl REAL,
        reason TEXT,
        opened_at TEXT NOT NULL,
        closed_at TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );
    CREATE TABLE IF NOT EXISTS knowledge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        market TEXT,
        symbol TEXT,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
    CREATE INDEX IF NOT EXISTS idx_trades_session ON trades(session_id);
"""

SQL_FTS5_TABLES = """
    CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
        content, role, session_id, created_at,
        content=messages, content_rowid=id
    );
    CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
        key, value, market, symbol,
        content=knowledge, content_rowid=id
    );
"""

SQL_FTS5_TRIGGERS = """
    CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
        INSERT INTO messages_fts(rowid, content, role, session_id, created_at)
        VALUES (new.id, new.content, new.role, new.session_id, new.created_at);
    END;
    CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
        INSERT INTO messages_fts(messages_fts, rowid, content, role, session_id, created_at)
        VALUES ('delete', old.id, old.content, old.role, old.session_id, old.created_at);
    END;
    CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
        INSERT INTO messages_fts(messages_fts, rowid, content, role, session_id, created_at)
        VALUES ('delete', old.id, old.content, old.role, old.session_id, old.created_at);
        INSERT INTO messages_fts(rowid, content, role, session_id, created_at)
        VALUES (new.id, new.content, new.role, new.session_id, new.created_at);
    END;
    CREATE TRIGGER IF NOT EXISTS knowledge_ai AFTER INSERT ON knowledge BEGIN
        INSERT INTO knowledge_fts(rowid, key, value, market, symbol)
        VALUES (new.id, new.key, new.value, new.market, new.symbol);
    END;
    CREATE TRIGGER IF NOT EXISTS knowledge_ad AFTER DELETE ON knowledge BEGIN
        INSERT INTO knowledge_fts(knowledge_fts, rowid, key, value, market, symbol)
        VALUES ('delete', old.id, old.key, old.value, old.market, old.symbol);
    END;
    CREATE TRIGGER IF NOT EXISTS knowledge_au AFTER UPDATE ON knowledge BEGIN
        INSERT INTO knowledge_fts(knowledge_fts, rowid, key, value, market, symbol)
        VALUES ('delete', old.id, old.key, old.value, old.market, old.symbol);
        INSERT INTO knowledge_fts(rowid, key, value, market, symbol)
        VALUES (new.id, new.key, new.value, new.market, new.symbol);
    END;
"""

# ── Shared helpers ───────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_row(role: str, content: str | None, metadata: str | None, created_at: str) -> dict:
    msg: dict = {"role": role, "content": content, "created_at": created_at}
    if metadata:
        try:
            msg["metadata"] = json.loads(metadata)
        except json.JSONDecodeError:
            pass
    return msg


def _parse_rows(rows: list, with_metadata: bool = True) -> list[dict]:
    result = []
    for row in reversed(rows):
        if with_metadata:
            result.append(_parse_row(row[0], row[1], row[2], row[3]))
        else:
            result.append({"market": row[0], "symbol": row[1], "key": row[2], "value": row[3]})
    return result


def _get_db_path(db_path: str | None) -> str:
    if db_path is None:
        db_path = str(Path.home() / ".aiquantification" / "memory.db")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return db_path


# ── Async Agent Memory ───────────────────────────────────────────────────────

class AsyncAgentMemory:
    def __init__(self, db_path: str | None = None):
        self._db_path = _get_db_path(db_path)
        self._conn: aiosqlite.Connection | None = None

    async def _get_conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            self._conn = await aiosqlite.connect(self._db_path)
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


# ── Sync Agent Memory ────────────────────────────────────────────────────────

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
