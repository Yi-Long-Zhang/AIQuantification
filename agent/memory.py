from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class AgentMemory:
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = str(Path.home() / ".aiquantification" / "memory.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        self._conn.executescript("""
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
        """)
        self._conn.commit()

    def create_session(self, session_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT OR IGNORE INTO sessions (session_id, created_at, updated_at) VALUES (?, ?, ?)",
            (session_id, now, now),
        )
        self._conn.commit()

    def save_message(self, session_id: str, role: str, content: str, metadata: dict | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
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
        result = []
        for role, content, metadata, created_at in reversed(rows):
            msg = {"role": role, "content": content, "created_at": created_at}
            if metadata:
                try:
                    msg["metadata"] = json.loads(metadata)
                except json.JSONDecodeError:
                    pass
            result.append(msg)
        return result

    def save_trade(self, session_id: str, symbol: str, direction: str, confidence: float,
                   entry_price: float | None, reason: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            "INSERT INTO trades (session_id, symbol, direction, confidence, entry_price, reason, opened_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, symbol, direction, confidence, entry_price, reason, now),
        )
        self._conn.commit()
        return cur.lastrowid

    def save_knowledge(self, market: str, symbol: str, key: str, value: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
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
        return [{"market": r[0], "symbol": r[1], "key": r[2], "value": r[3]} for r in rows]

    def close(self):
        self._conn.close()
