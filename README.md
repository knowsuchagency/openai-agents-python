# OpenAI Agents SDK

The OpenAI Agents SDK is a lightweight yet powerful framework for building multi-agent workflows. It is provider-agnostic, supporting the OpenAI Responses and Chat Completions APIs, as well as 100+ other LLMs.

<img src="https://cdn.openai.com/API/docs/images/orchestration.png" alt="Image of the Agents Tracing UI" style="max-height: 803px;">

### Core concepts:

1. [**Agents**](https://openai.github.io/openai-agents-python/agents): LLMs configured with instructions, tools, guardrails, and handoffs
2. [**Handoffs**](https://openai.github.io/openai-agents-python/handoffs/): A specialized tool call used by the Agents SDK for transferring control between agents
3. [**Guardrails**](https://openai.github.io/openai-agents-python/guardrails/): Configurable safety checks for input and output validation
4. [**Tracing**](https://openai.github.io/openai-agents-python/tracing/): Built-in tracking of agent runs, allowing you to view, debug and optimize your workflows

Explore the [examples](examples) directory to see the SDK in action, and read our [documentation](https://openai.github.io/openai-agents-python/) for more details.

## Get started

1. Set up your Python environment

```
python -m venv env
source env/bin/activate
```

2. Install Agents SDK

```
pip install openai-agents
```

For voice support, install with the optional `voice` group: `pip install 'openai-agents[voice]'`.

## Hello world example

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are a helpful assistant")

result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)

# Code within the code,
# Functions calling themselves,
# Infinite loop's dance.
```

(_If running this, ensure you set the `OPENAI_API_KEY` environment variable_)

(_For Jupyter notebook users, see [hello_world_jupyter.py](examples/basic/hello_world_jupyter.py)_)

## Handoffs example

```python
from agents import Agent, Runner
import asyncio

spanish_agent = Agent(
    name="Spanish agent",
    instructions="You only speak Spanish.",
)

english_agent = Agent(
    name="English agent",
    instructions="You only speak English",
)

triage_agent = Agent(
    name="Triage agent",
    instructions="Handoff to the appropriate agent based on the language of the request.",
    handoffs=[spanish_agent, english_agent],
)


async def main():
    result = await Runner.run(triage_agent, input="Hola, ¿cómo estás?")
    print(result.final_output)
    # ¡Hola! Estoy bien, gracias por preguntar. ¿Y tú, cómo estás?


if __name__ == "__main__":
    asyncio.run(main())
```

## Functions example

```python
import asyncio

from agents import Agent, Runner, function_tool


@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny."


agent = Agent(
    name="Hello world",
    instructions="You are a helpful agent.",
    tools=[get_weather],
)


async def main():
    result = await Runner.run(agent, input="What's the weather in Tokyo?")
    print(result.final_output)
    # The weather in Tokyo is sunny.


if __name__ == "__main__":
    asyncio.run(main())
```

## Session Memory

Session memory allows agents to automatically persist and retrieve conversation history across multiple runs, eliminating the need for users to manually manage conversation state using `result.to_input_list()`.

### Before (Manual History Management)

```python
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

### After (Automatic Session Memory)

```python
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

### Configuration Options

The `memory` parameter on the `Agent` class accepts three types of values:

-   **`None` (Default)**: No session memory. Users must manually manage conversation history.
-   **`True`**: Use the default in-memory SQLite session memory implementation.
-   **`SessionMemory` instance**: Use a custom session memory implementation.

```python
from agents import Agent, SQLiteSessionMemory

# Default: no session memory
agent = Agent(name="Assistant")

# Enable default in-memory session memory
agent = Agent(name="Assistant", memory=True)

# Use persistent SQLite database
custom_memory = SQLiteSessionMemory(db_path="conversations.db")
agent = Agent(name="Assistant", memory=custom_memory)
```

### Multiple Sessions

Different session IDs maintain separate conversation histories:

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

### Custom Session Memory

You can implement custom session memory by implementing the `SessionMemory` protocol:

```python
from agents.memory import SessionMemory
from agents.items import TResponseInputItem

class CustomSessionMemory:
    async def load_session(self, session_id: str) -> list[TResponseInputItem]:
        # Load conversation history for the session
        ...

    async def save_session(self, session_id: str, conversation_history: list[TResponseInputItem]) -> None:
        # Save conversation history for the session
        ...

    # ... implement other required methods
```

Session memory is completely backward compatible. Existing code that doesn't use session memory will continue to work unchanged.

## The agent loop

When you call `Runner.run()`, we run a loop until we get a final output.

1. We call the LLM, using the model and settings on the agent, and the message history.
2. The LLM returns a response, which may include tool calls.
3. If the response has a final output (see below for more on this), we return it and end the loop.
4. If the response has a handoff, we set the agent to the new agent and go back to step 1.
5. We process the tool calls (if any) and append the tool responses messages. Then we go to step 1.

There is a `max_turns` parameter that you can use to limit the number of times the loop executes.

### Final output

Final output is the last thing the agent produces in the loop.

1.  If you set an `output_type` on the agent, the final output is when the LLM returns something of that type. We use [structured outputs](https://platform.openai.com/docs/guides/structured-outputs) for this.
2.  If there's no `output_type` (i.e. plain text responses), then the first LLM response without any tool calls or handoffs is considered as the final output.

As a result, the mental model for the agent loop is:

1. If the current agent has an `output_type`, the loop runs until the agent produces structured output matching that type.
2. If the current agent does not have an `output_type`, the loop runs until the current agent produces a message without any tool calls/handoffs.

## Common agent patterns

The Agents SDK is designed to be highly flexible, allowing you to model a wide range of LLM workflows including deterministic flows, iterative loops, and more. See examples in [`examples/agent_patterns`](examples/agent_patterns).

## Tracing

The Agents SDK automatically traces your agent runs, making it easy to track and debug the behavior of your agents. Tracing is extensible by design, supporting custom spans and a wide variety of external destinations, including [Logfire](https://logfire.pydantic.dev/docs/integrations/llms/openai/#openai-agents), [AgentOps](https://docs.agentops.ai/v1/integrations/agentssdk), [Braintrust](https://braintrust.dev/docs/guides/traces/integrations#openai-agents-sdk), [Scorecard](https://docs.scorecard.io/docs/documentation/features/tracing#openai-agents-sdk-integration), and [Keywords AI](https://docs.keywordsai.co/integration/development-frameworks/openai-agent). For more details about how to customize or disable tracing, see [Tracing](http://openai.github.io/openai-agents-python/tracing), which also includes a larger list of [external tracing processors](http://openai.github.io/openai-agents-python/tracing/#external-tracing-processors-list).

## Development (only needed if you need to edit the SDK/examples)

0. Ensure you have [`uv`](https://docs.astral.sh/uv/) installed.

```bash
uv --version
```

1. Install dependencies

```bash
make sync
```

2. (After making changes) lint/test

```
make tests  # run tests
make mypy   # run typechecker
make lint   # run linter
```

## Acknowledgements

We'd like to acknowledge the excellent work of the open-source community, especially:

-   [Pydantic](https://docs.pydantic.dev/latest/) (data validation) and [PydanticAI](https://ai.pydantic.dev/) (advanced agent framework)
-   [MkDocs](https://github.com/squidfunk/mkdocs-material)
-   [Griffe](https://github.com/mkdocstrings/griffe)
-   [uv](https://github.com/astral-sh/uv) and [ruff](https://github.com/astral-sh/ruff)

We're committed to continuing to build the Agents SDK as an open source framework so others in the community can expand on our approach.
