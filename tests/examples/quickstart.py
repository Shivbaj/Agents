"""
Quick start guide and simple usage examples
"""

import asyncio
import os
from pathlib import Path

from src.agents.implementations.general_assistant_enhanced import GeneralAssistant
from src.config.settings import get_settings


async def quick_start_example():
    """Simple example to get started quickly"""
    print("🚀 Multi-Agent System - Quick Start")
    print("=" * 50)
    
    # Check if OpenAI API key is configured
    settings = get_settings()
    if not settings.openai_api_key:
        print("⚠️  OpenAI API key not found!")
        print("Please set OPENAI_API_KEY environment variable or add it to .env file")
        print("\nExample .env file:")
        print("OPENAI_API_KEY=your_api_key_here")
        return
    
    try:
        # Create a simple assistant
        print("\n1️⃣  Creating General Assistant...")
        assistant = GeneralAssistant(
            agent_id="quickstart_assistant",
            use_tools=True,
            use_web_search=False  # Disable web search for simplicity
        )
        
        # Initialize
        print("2️⃣  Initializing agent...")
        await assistant.initialize()
        print(f"✅ Agent initialized with {len(assistant.tools)} tools")
        
        # Simple conversation
        print("\n3️⃣  Starting conversation...")
        session_id = "quickstart_session"
        
        # Test messages
        test_messages = [
            "Hello! Can you introduce yourself?",
            "What can you help me with?",
            "Can you calculate 25 * 17 + 100?",
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n💬 Message {i}:")
            print(f"User: {message}")
            
            response = await assistant.process_message(
                message=message,
                session_id=session_id
            )
            
            print(f"Assistant: {response.content}")
            
            # Show tools used if any
            tools_used = response.metadata.get("tools_used", [])
            if tools_used:
                print(f"🛠️  Tools used: {', '.join(tools_used)}")
        
        print("\n4️⃣  Conversation completed!")
        
        # Show conversation history
        history = assistant.get_conversation_history(session_id)
        print(f"\n📚 Total messages in conversation: {len(history)}")
        
        # Cleanup
        await assistant.cleanup()
        print("✅ Cleanup completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(quick_start_example())