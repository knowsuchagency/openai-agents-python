import pytest

from agents import Agent, RunConfig, Runner
from agents.memory import SQLiteSessionMemory

from .fake_model import FakeModel
from .test_responses import get_text_message


@pytest.mark.asyncio
async def test_session_memory_round_trip() -> None:
    model = FakeModel()
    memory = SQLiteSessionMemory()
    agent = Agent(name="assistant", model=model, memory=memory)
    run_config = RunConfig(session_id="s1")

    model.set_next_output([get_text_message("a")])
    result1 = await Runner.run(agent, "hi", run_config=run_config)
    assert memory.load("s1") == result1.to_input_list()

    model.set_next_output([get_text_message("b")])
    result2 = await Runner.run(agent, "question", run_config=run_config)
    assert model.last_turn_args["input"] == [
        {"content": "hi", "role": "user"},
        {"content": "a", "role": "assistant"},
        {"content": "question", "role": "user"},
    ]
    assert memory.load("s1") == result2.to_input_list()


@pytest.mark.asyncio
async def test_memory_true_initializes_default() -> None:
    model = FakeModel()
    agent = Agent(name="assistant", model=model, memory=True)
    run_config = RunConfig(session_id="x")
    model.set_next_output([get_text_message("ok")])
    await Runner.run(agent, "hi", run_config=run_config)
    assert agent.memory is not None
