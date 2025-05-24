"""
Example demonstrating session memory functionality.

This example shows how to use session memory to automatically manage conversation
history across multiple agent runs, eliminating the need to manually use 
result.to_input_list().
"""

import asyncio

from agents import Agent, Runner, trace


async def main():
    # Create an agent with session memory enabled
    agent = Agent(
        name="Assistant", 
        instructions="You are a helpful assistant. Remember what users tell you.",
        memory=True  # Enable default SQLite session memory
    )

    session_id = "conversation_1"

    with trace(workflow_name="Session Memory Example", group_id=session_id):
        # First turn - introduce yourself
        print("=== First Turn ===")
        result1 = await Runner.run(
            agent, 
            "Hi, my name is Alice and I'm a software engineer.",
            session_id=session_id
        )
        print(f"Assistant: {result1.final_output}")

        # Second turn - ask about previous information
        print("\n=== Second Turn ===")
        result2 = await Runner.run(
            agent,
            "What's my name and profession?",
            session_id=session_id
        )
        print(f"Assistant: {result2.final_output}")

        # Third turn - continue the conversation
        print("\n=== Third Turn ===")
        result3 = await Runner.run(
            agent,
            "I'm working on a Python project. Can you help me with it?",
            session_id=session_id
        )
        print(f"Assistant: {result3.final_output}")

    # Demonstrate multiple sessions
    print("\n" + "="*50)
    print("=== Different Session ===")
    
    session_id_2 = "conversation_2"
    
    with trace(workflow_name="Session Memory Example", group_id=session_id_2):
        # This should not remember Alice from the previous session
        result4 = await Runner.run(
            agent,
            "What's my name?",
            session_id=session_id_2
        )
        print(f"Assistant: {result4.final_output}")

    print("\n" + "="*50)
    print("=== Back to First Session ===")
    
    with trace(workflow_name="Session Memory Example", group_id=session_id):
        # This should still remember Alice
        result5 = await Runner.run(
            agent,
            "What did I tell you about my work?",
            session_id=session_id
        )
        print(f"Assistant: {result5.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
