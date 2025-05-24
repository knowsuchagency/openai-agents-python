from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ..items import TResponseInputItem
from .interface import SessionMemory


class SQLiteSessionMemory(SessionMemory):
    """SQLite-based implementation of session memory.

    This implementation stores conversation history in a local SQLite database.
    Each session is identified by a unique session_id, and the conversation
    history is stored as JSON.
    """

    def __init__(self, db_path: str | Path = ":memory:"):
        """Initialize the SQLite session memory.

        Args:
            db_path: Path to the SQLite database file. Defaults to ":memory:" for
                    in-memory database. Use a file path for persistent storage.
        """
        self.db_path = str(db_path) if db_path != ":memory:" else ":memory:"
        self._connection: sqlite3.Connection | None = None

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create a database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    conversation_history TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            self._connection.execute(
                """
                CREATE TRIGGER IF NOT EXISTS update_sessions_timestamp
                AFTER UPDATE ON sessions
                BEGIN
                    UPDATE sessions SET updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = NEW.session_id;
                END
            """
            )
            self._connection.commit()
        return self._connection

    async def load_session(self, session_id: str) -> list[TResponseInputItem]:
        """Load the conversation history for a given session."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT conversation_history FROM sessions WHERE session_id = ?",
            (session_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return []

        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            # If JSON is corrupted, return empty list
            return []

    async def save_session(
        self, session_id: str, conversation_history: list[TResponseInputItem]
    ) -> None:
        """Save the conversation history for a given session."""
        conn = self._get_connection()
        history_json = json.dumps(conversation_history)

        conn.execute(
            """
            INSERT OR REPLACE INTO sessions (session_id, conversation_history)
            VALUES (?, ?)
        """,
            (session_id, history_json),
        )
        conn.commit()

    async def append_to_session(
        self, session_id: str, new_items: list[TResponseInputItem]
    ) -> None:
        """Append new items to an existing session's conversation history."""
        existing_history = await self.load_session(session_id)
        updated_history = existing_history + new_items
        await self.save_session(session_id, updated_history)

    async def clear_session(self, session_id: str) -> None:
        """Clear the conversation history for a given session."""
        conn = self._get_connection()
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()

    async def list_sessions(self) -> list[str]:
        """List all available session IDs."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT session_id FROM sessions ORDER BY updated_at DESC"
        )
        return [row[0] for row in cursor.fetchall()]

    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT 1 FROM sessions WHERE session_id = ? LIMIT 1", (session_id,)
        )
        return cursor.fetchone() is not None

    async def cleanup(self) -> None:
        """Clean up database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
