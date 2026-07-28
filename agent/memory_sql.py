"""
SQL constants and shared helpers for agent memory.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

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
