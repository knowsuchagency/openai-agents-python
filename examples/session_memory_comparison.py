"""
Comparison between manual conversation history management and automatic session memory.

This example demonstrates the difference between the old way of managing conversation
history manually using result.to_input_list() and the new session memory approach.
"""

import asyncio

from agents import Agent, Runner, trace


async def old_way_example():
    """Example of the old way - manual conversation history management."""
    print("=== OLD WAY: Manual History Management ===")
    
    agent = Agent(
        name="Assistant",
        instructions="You are a helpful assistant. Remember what users tell you."
    )

    thread_id = "manual_conversation"

    with trace(workflow_name="Manual Conversation", group_id=thread_id):
        # First turn
        result = await Runner.run(agent, "What city is the Golden Gate Bridge in?")
        print(f"Assistant: {result.final_output}")

        # Second turn - manually manage conversation history
        new_input = result.to_input_list() + [{"role": "user", "content": "What state is it in?"}]
        result = await Runner.run(agent, new_input)
        print(f"Assistant: {result.final_output}")

        # Third turn - manually manage conversation history again
        new_input = result.to_input_list() + [{"role": "user", "content": "What's the population of that city?"}]
        result = await Runner.run(agent, new_input)
        print(f"Assistant: {result.final_output}")


async def new_way_example():
    """Example of the new way - automatic session memory."""
    print("\n=== NEW WAY: Automatic Session Memory ===")
    
    agent = Agent(
        name="Assistant",
        instructions="You are a helpful assistant. Remember what users tell you.",
        memory=True  # Enable session memory
    )

    session_id = "auto_conversation"

    with trace(workflow_name="Automatic Conversation", group_id=session_id):
        # First turn
        result = await Runner.run(
            agent, 
            "What city is the Golden Gate Bridge in?",
            session_id=session_id
        )
        print(f"Assistant: {result.final_output}")

        # Second turn - conversation history is automatically managed
        result = await Runner.run(
            agent,
            "What state is it in?",
            session_id=session_id
        )
        print(f"Assistant: {result.final_output}")

        # Third turn - conversation history is still automatically managed
        result = await Runner.run(
            agent,
            "What's the population of that city?",
            session_id=session_id
        )
        print(f"Assistant: {result.final_output}")


async def main():
    await old_way_example()
    await new_way_example()
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print("- Old way: Manual conversation history with result.to_input_list()")
    print("- New way: Automatic session memory with session_id parameter")
    print("- Both approaches produce the same conversational behavior")
    print("- Session memory eliminates boilerplate and reduces errors")


if __name__ == "__main__":
    asyncio.run(main())
