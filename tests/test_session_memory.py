import tempfile
from pathlib import Path

import pytest

from agents import Agent, Runner, SQLiteSessionMemory
from tests.fake_model import FakeModel
from tests.test_responses import get_text_message


class TestSessionMemory:
    """Test session memory functionality."""

    @pytest.mark.asyncio
    async def test_sqlite_session_memory_basic_operations(self):
        """Test basic SQLite session memory operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            memory = SQLiteSessionMemory(db_path)

            # Test empty session
            history = await memory.load_session("test_session")
            assert history == []

            # Test session doesn't exist
            exists = await memory.session_exists("test_session")
            assert not exists

            # Test save session
            test_history = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ]
            await memory.save_session("test_session", test_history)

            # Test session exists
            exists = await memory.session_exists("test_session")
            assert exists

            # Test load session
            loaded_history = await memory.load_session("test_session")
            assert loaded_history == test_history

            # Test append to session
            new_items = [{"role": "user", "content": "How are you?"}]
            await memory.append_to_session("test_session", new_items)

            updated_history = await memory.load_session("test_session")
            assert len(updated_history) == 3
            assert updated_history[-1] == new_items[0]

            # Test list sessions
            sessions = await memory.list_sessions()
            assert "test_session" in sessions

            # Test clear session
            await memory.clear_session("test_session")
            history = await memory.load_session("test_session")
            assert history == []

            # Cleanup
            await memory.cleanup()

    @pytest.mark.asyncio
    async def test_agent_with_session_memory_boolean(self):
        """Test agent with session memory enabled via boolean."""
        model = FakeModel()
        model.set_next_output([get_text_message("Hello! How can I help you?")])

        agent = Agent(
            name="test_agent", model=model, memory=True  # Enable default SQLite memory
        )

        # First conversation turn
        result1 = await Runner.run(
            agent, "Hi, my name is Alice", session_id="test_conversation"
        )

        assert result1.final_output == "Hello! How can I help you?"

        # Second conversation turn - should have memory of previous conversation
        model.set_next_output([get_text_message("Nice to meet you, Alice!")])

        result2 = await Runner.run(
            agent, "What's my name?", session_id="test_conversation"
        )

        assert result2.final_output == "Nice to meet you, Alice!"

        # Verify the model received the conversation history
        # The input should include the previous conversation
        last_call_input = model.last_turn_args["input"]
        assert len(last_call_input) >= 3  # Original message + response + new message

        # Check that the conversation history is preserved
        assert any("Alice" in str(item) for item in last_call_input)

    @pytest.mark.asyncio
    async def test_agent_with_custom_session_memory(self):
        """Test agent with custom session memory implementation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "custom.db"
            custom_memory = SQLiteSessionMemory(db_path)

            model = FakeModel()
            model.set_next_output([get_text_message("Response 1")])

            agent = Agent(name="test_agent", model=model, memory=custom_memory)

            # First turn
            result1 = await Runner.run(
                agent, "First message", session_id="custom_session"
            )

            assert result1.final_output == "Response 1"

            # Verify session was saved
            exists = await custom_memory.session_exists("custom_session")
            assert exists

            # Cleanup
            await custom_memory.cleanup()

    @pytest.mark.asyncio
    async def test_agent_without_session_memory(self):
        """Test agent without session memory (default behavior)."""
        model = FakeModel()
        model.set_next_output([get_text_message("Response without memory")])

        agent = Agent(name="test_agent", model=model, memory=None)  # No session memory

        # Run with session_id but no memory enabled - should work normally
        result = await Runner.run(agent, "Test message", session_id="ignored_session")

        assert result.final_output == "Response without memory"

    @pytest.mark.asyncio
    async def test_session_memory_with_multiple_sessions(self):
        """Test session memory with multiple different sessions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "multi.db"
            memory = SQLiteSessionMemory(db_path)

            # Save different conversations
            await memory.save_session(
                "session1", [{"role": "user", "content": "I like cats"}]
            )

            await memory.save_session(
                "session2", [{"role": "user", "content": "I like dogs"}]
            )

            # Verify sessions are separate
            session1_history = await memory.load_session("session1")
            session2_history = await memory.load_session("session2")

            assert "cats" in session1_history[0]["content"]
            assert "dogs" in session2_history[0]["content"]

            # List all sessions
            sessions = await memory.list_sessions()
            assert "session1" in sessions
            assert "session2" in sessions
            assert len(sessions) == 2

            # Cleanup
            await memory.cleanup()

    def test_invalid_memory_configuration(self):
        """Test that invalid memory configuration raises an error."""
        with pytest.raises(ValueError, match="Invalid memory configuration"):
            agent = Agent(
                name="test_agent", memory="invalid_string"  # Invalid memory type
            )

            # This should raise an error when trying to get session memory
            Runner._get_session_memory(agent)
