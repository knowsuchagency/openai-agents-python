from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod

from .items import TResponseInputItem


class SessionMemory(ABC):
    """Interface for session memory implementations."""

    @abstractmethod
    def load(self, session_id: str) -> list[TResponseInputItem]:
        """Load the conversation history for ``session_id``."""

    @abstractmethod
    def store(self, session_id: str, items: list[TResponseInputItem]) -> None:
        """Store ``items`` as the conversation history for ``session_id``."""


class SQLiteSessionMemory(SessionMemory):
    """SQLite-backed session memory."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path)
        self._ensure_table()

    def _ensure_table(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    session_id TEXT NOT NULL,
                    idx INTEGER NOT NULL,
                    item TEXT NOT NULL,
                    PRIMARY KEY(session_id, idx)
                )
                """
            )

    def load(self, session_id: str) -> list[TResponseInputItem]:
        cursor = self._conn.execute(
            "SELECT item FROM memory WHERE session_id=? ORDER BY idx ASC",
            (session_id,),
        )
        rows = cursor.fetchall()
        return [json.loads(row[0]) for row in rows]

    def store(self, session_id: str, items: list[TResponseInputItem]) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM memory WHERE session_id=?", (session_id,))
            for idx, item in enumerate(items):
                self._conn.execute(
                    "INSERT INTO memory (session_id, idx, item) VALUES (?, ?, ?)",
                    (session_id, idx, json.dumps(item)),
                )

    def close(self) -> None:
        self._conn.close()
