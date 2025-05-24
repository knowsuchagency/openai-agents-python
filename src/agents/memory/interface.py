from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..items import TResponseInputItem


@runtime_checkable
class SessionMemory(Protocol):
    """Protocol for session memory implementations.

    Session memory allows agents to automatically persist and retrieve conversation
    history across multiple runs, eliminating the need for users to manually manage
    conversation state using result.to_input_list().
    """

    async def load_session(self, session_id: str) -> list[TResponseInputItem]:
        """Load the conversation history for a given session.

        Args:
            session_id: Unique identifier for the conversation session

        Returns:
            List of input items representing the conversation history.
            Returns empty list if session doesn't exist.
        """
        ...

    async def save_session(
        self, session_id: str, conversation_history: list[TResponseInputItem]
    ) -> None:
        """Save the conversation history for a given session.

        Args:
            session_id: Unique identifier for the conversation session
            conversation_history: Complete conversation history to save
        """
        ...

    async def append_to_session(
        self, session_id: str, new_items: list[TResponseInputItem]
    ) -> None:
        """Append new items to an existing session's conversation history.

        Args:
            session_id: Unique identifier for the conversation session
            new_items: New conversation items to append
        """
        ...

    async def clear_session(self, session_id: str) -> None:
        """Clear the conversation history for a given session.

        Args:
            session_id: Unique identifier for the conversation session
        """
        ...

    async def list_sessions(self) -> list[str]:
        """List all available session IDs.

        Returns:
            List of session IDs that have stored conversation history
        """
        ...

    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists.

        Args:
            session_id: Unique identifier for the conversation session

        Returns:
            True if the session exists, False otherwise
        """
        ...

    async def cleanup(self) -> None:
        """Clean up any resources used by the memory implementation.

        This method is called when the memory instance is no longer needed.
        Subclasses can override this to perform cleanup operations like
        closing database connections.
        """
        pass
