# Session Memory

Session memory allows agents to automatically persist and retrieve conversation history across multiple runs, eliminating the need for users to manually manage conversation state using `result.to_input_list()`.

## Overview

Previously, to maintain conversation history across multiple agent runs, you had to manually manage the conversation state:

```python
# Old way - manual conversation history management
agent = Agent(name="Assistant", instructions="Reply very concisely.")

with trace(workflow_name="Conversation", group_id=thread_id):
    # First turn
    result = await Runner.run(agent, "What city is the Golden Gate Bridge in?")
    print(result.final_output)
    # San Francisco

    # Second turn - manually manage conversation history
    new_input = result.to_input_list() + [{"role": "user", "content": "What state is it in?"}]
    result = await Runner.run(agent, new_input)
    print(result.final_output)
    # California
```

With session memory, this becomes much simpler:

```python
# New way - automatic session memory
agent = Agent(
    name="Assistant", 
    instructions="Reply very concisely.",
    memory=True  # Enable session memory
)

with trace(workflow_name="Conversation", group_id=thread_id):
    # First turn
    result = await Runner.run(agent, "What city is the Golden Gate Bridge in?", session_id="conversation_1")
    print(result.final_output)
    # San Francisco

    # Second turn - conversation history is automatically managed
    result = await Runner.run(agent, "What state is it in?", session_id="conversation_1")
    print(result.final_output)
    # California
```

## Configuration

The `memory` parameter on the `Agent` class accepts three types of values:

### 1. `None` (Default)
No session memory. Users must manually manage conversation history using `result.to_input_list()`.

```python
agent = Agent(name="Assistant", memory=None)  # or just omit the parameter
```

### 2. `True`
Use the default SQLite session memory implementation with default settings.

```python
agent = Agent(name="Assistant", memory=True)
```

This creates a SQLite database file named `agent_sessions.db` in the current directory.

### 3. Custom `SessionMemory` Instance
Use a custom session memory implementation.

```python
from agents import SQLiteSessionMemory

# Custom SQLite database path
custom_memory = SQLiteSessionMemory(db_path="my_conversations.db")
agent = Agent(name="Assistant", memory=custom_memory)
```

## Usage

When session memory is enabled, you need to provide a `session_id` parameter to `Runner.run()`:

```python
result = await Runner.run(
    agent, 
    "Your message here",
    session_id="unique_session_identifier"
)
```

The `session_id` identifies which conversation session to load/save. Different session IDs maintain separate conversation histories.

## Session Memory Interface

You can implement custom session memory by subclassing `SessionMemory`:

```python
from agents.memory import SessionMemory
from agents.items import TResponseInputItem

class CustomSessionMemory(SessionMemory):
    async def load_session(self, session_id: str) -> list[TResponseInputItem]:
        # Load conversation history for the session
        pass
    
    async def save_session(self, session_id: str, conversation_history: list[TResponseInputItem]) -> None:
        # Save conversation history for the session
        pass
    
    async def append_to_session(self, session_id: str, new_items: list[TResponseInputItem]) -> None:
        # Append new items to existing session
        pass
    
    async def clear_session(self, session_id: str) -> None:
        # Clear session history
        pass
    
    async def list_sessions(self) -> list[str]:
        # List all session IDs
        pass
    
    async def session_exists(self, session_id: str) -> bool:
        # Check if session exists
        pass
    
    async def cleanup(self) -> None:
        # Clean up resources (optional)
        pass
```

## SQLite Session Memory

The default `SQLiteSessionMemory` implementation:

- Stores conversation history in a local SQLite database
- Each session is identified by a unique `session_id`
- Conversation history is stored as JSON
- Supports multiple concurrent sessions
- Automatically creates database tables on first use

### Database Schema

```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    conversation_history TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Examples

### Multiple Sessions

```python
agent = Agent(name="Assistant", memory=True)

# Session 1
await Runner.run(agent, "Hi, I'm Alice", session_id="user_alice")
await Runner.run(agent, "What's my name?", session_id="user_alice")  # Remembers Alice

# Session 2  
await Runner.run(agent, "Hi, I'm Bob", session_id="user_bob")
await Runner.run(agent, "What's my name?", session_id="user_bob")    # Remembers Bob

# Back to Session 1
await Runner.run(agent, "What did I tell you?", session_id="user_alice")  # Still remembers Alice
```

### Custom Database Path

```python
from agents import SQLiteSessionMemory

memory = SQLiteSessionMemory(db_path="/path/to/my/conversations.db")
agent = Agent(name="Assistant", memory=memory)
```

### Session Management

```python
memory = SQLiteSessionMemory()

# List all sessions
sessions = await memory.list_sessions()

# Check if session exists
exists = await memory.session_exists("session_1")

# Clear a session
await memory.clear_session("session_1")

# Clean up resources
await memory.cleanup()
```

## Backward Compatibility

Session memory is completely backward compatible. Existing code that doesn't use session memory will continue to work unchanged. The `session_id` parameter is optional and only used when session memory is enabled on the agent.

## Benefits

1. **Simplified Code**: No need to manually manage `result.to_input_list()`
2. **Reduced Errors**: Eliminates common mistakes in conversation history management
3. **Multiple Sessions**: Easy support for multiple concurrent conversations
4. **Persistence**: Conversation history survives application restarts
5. **Pluggable**: Custom implementations for different storage backends
6. **Backward Compatible**: Existing code continues to work unchanged
