"""
Example usage and demonstrations of the Multi-Agent System

This module provides working examples of how to use the enhanced multi-agent
system with LangChain, LangGraph, and the various components.

Examples included:
1. Basic agent interaction
2. Multi-agent workflow
3. Tool usage
4. Memory and context management
5. Custom agent creation

Run this file to see the system in action:
    python -m tests.examples.usage_examples
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from src.agents.implementations.general_assistant_enhanced import GeneralAssistant
from src.agents.registry.manager import AgentManager
from src.orchestrator.workflow import WorkflowBuilder, MultiAgentWorkflow
from src.memory.conversation import MemoryManager, MemoryConfig
from src.prompts.manager import PromptManager, create_agent_prompt
from src.tools.base_tools import get_tool
from src.config.settings import get_settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_agent_interaction():
    """Example 1: Basic agent interaction"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Agent Interaction")
    print("="*60)
    
    try:
        # Create a general assistant
        assistant = GeneralAssistant(
            agent_id="demo_assistant",
            use_tools=True,
            use_web_search=False  # Disable web search for demo
        )
        
        # Initialize the agent
        await assistant.initialize()
        
        # Test conversation
        session_id = "demo_session"
        
        messages = [
            "Hello! What can you help me with?",
            "Can you calculate 15 * 24?",
            "What are the main features of this system?"
        ]
        
        for message in messages:
            print(f"\nUser: {message}")
            response = await assistant.process_message(
                message=message,
                session_id=session_id
            )
            print(f"Assistant: {response.content}")
            print(f"Metadata: {response.metadata}")
        
        # Cleanup
        await assistant.cleanup()
        
    except Exception as e:
        print(f"Error in basic agent interaction: {e}")


async def example_memory_system():
    """Example 2: Memory system demonstration"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Memory System")
    print("="*60)
    
    try:
        # Create memory manager
        memory_manager = MemoryManager()
        
        # Create conversation memory
        session_id = "memory_demo"
        memory = memory_manager.create_conversation_memory(session_id)
        
        # Add some messages
        await memory.add_message("user", "My name is Alice")
        await memory.add_message("assistant", "Nice to meet you, Alice!")
        await memory.add_message("user", "What's my favorite color?")
        await memory.add_message("assistant", "I don't know your favorite color yet. Could you tell me?")
        await memory.add_message("user", "It's blue")
        await memory.add_message("assistant", "Great! I'll remember that your favorite color is blue.")
        
        # Get conversation history
        history = await memory.get_conversation_history()
        print(f"\nConversation History ({len(history)} messages):")
        for msg in history[-4:]:  # Show last 4 messages
            role = "User" if msg.__class__.__name__ == "HumanMessage" else "Assistant"
            print(f"{role}: {msg.content}")
        
        # Test memory persistence
        await memory.save_to_storage()
        print(f"\nMemory saved to storage")
        
        # Create hybrid memory with vector search
        hybrid_memory = memory_manager.create_hybrid_memory(session_id="hybrid_demo")
        
        # Add some contextual information
        await hybrid_memory.add_message("user", "I work as a software engineer")
        await hybrid_memory.add_message("user", "I enjoy Python programming")
        await hybrid_memory.add_message("user", "I'm learning about AI and machine learning")
        
        # Search for relevant context
        relevant = await hybrid_memory.search_relevant_context("programming languages")
        print(f"\nRelevant context for 'programming languages':")
        for item in relevant:
            print(f"- {item['content']}")
        
    except Exception as e:
        print(f"Error in memory system demo: {e}")


async def example_prompt_templates():
    """Example 3: Prompt template system"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Prompt Template System")
    print("="*60)
    
    try:
        # Create prompt manager
        prompt_manager = PromptManager()
        
        # Create a custom agent prompt
        custom_prompt = create_agent_prompt(
            agent_name="Code Helper",
            task_description="Help users with programming questions and code review",
            personality_traits=["helpful", "technical", "patient"],
            constraints=["Always provide code examples", "Explain complex concepts simply"]
        )
        
        # Register the template
        prompt_manager.register_template("code_helper", custom_prompt)
        
        # Use the template
        formatted_prompt = await prompt_manager.get_prompt(
            "code_helper",
            {"user_input": "How do I create a Python class?"}
        )
        
        print("Custom Prompt Template:")
        if isinstance(formatted_prompt, list):
            for msg in formatted_prompt:
                print(f"{msg.__class__.__name__}: {msg.content[:200]}...")
        else:
            print(formatted_prompt[:400] + "...")
        
        # List available templates
        templates = prompt_manager.list_templates()
        print(f"\nAvailable templates: {len(templates)}")
        for template in templates:
            print(f"- {template.id}: {template.name} (v{template.version})")
        
    except Exception as e:
        print(f"Error in prompt templates demo: {e}")


async def example_tool_usage():
    """Example 4: Tool usage demonstration"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Tool Usage")
    print("="*60)
    
    try:
        # Test calculator tool
        calc_tool = get_tool("calculator")
        calc_result = await calc_tool._arun("(15 + 25) * 2")
        print(f"Calculator: (15 + 25) * 2 = {calc_result.get('result', 'Error')}")
        
        # Test web search (if configured)
        try:
            search_tool = get_tool("web_search")
            search_results = await search_tool._arun("Python programming tutorial", max_results=2)
            print(f"\nWeb Search Results:")
            for i, result in enumerate(search_results[:2], 1):
                if "error" not in result:
                    print(f"{i}. {result.get('title', 'N/A')}")
                    print(f"   {result.get('snippet', 'No description')[:100]}...")
        except Exception as e:
            print(f"Web search not available: {e}")
        
        # Test file processor (create a test file first)
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document.\nIt contains multiple lines.\nFor testing the file processor.")
            test_file = f.name
        
        try:
            file_tool = get_tool("file_processor")
            file_result = await file_tool._arun(test_file)
            print(f"\nFile Processing Result:")
            print(f"File: {file_result.get('file_path', 'N/A')}")
            print(f"Content: {file_result.get('content', 'Error')[:100]}...")
            print(f"Word count: {file_result.get('word_count', 0)}")
        finally:
            # Clean up test file
            os.unlink(test_file)
        
    except Exception as e:
        print(f"Error in tool usage demo: {e}")


async def example_workflow_orchestration():
    """Example 5: Multi-agent workflow orchestration"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Workflow Orchestration")
    print("="*60)
    
    try:
        # Create workflow builder
        builder = WorkflowBuilder()
        
        # Create a simple research workflow
        workflow = builder.create_research_workflow("demo_research")
        
        # Execute workflow
        print("Executing research workflow...")
        initial_input = {
            "message": "Research the benefits of Python programming language"
        }
        
        result = await workflow.execute(initial_input)
        
        print(f"\nWorkflow Status: {result['status']}")
        print(f"Steps Completed: {result['steps_completed']}")
        print(f"Execution Time: {result['execution_time']:.2f} seconds")
        
        if result.get('final_output'):
            output = result['final_output']
            print(f"Final Output: {str(output).get('message', 'No output')[:200]}...")
        
        if result.get('error_message'):
            print(f"Error: {result['error_message']}")
        
    except Exception as e:
        print(f"Error in workflow orchestration demo: {e}")


async def example_agent_registry():
    """Example 6: Agent registry and management"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Agent Registry")
    print("="*60)
    
    try:
        # Create agent manager
        agent_manager = AgentManager()
        await agent_manager.initialize()
        
        # Load agents
        await agent_manager.discover_and_load_agents()
        
        # List available agents
        agents = agent_manager.list_agents()
        print(f"Available agents: {len(agents)}")
        for agent_id, info in agents.items():
            print(f"- {agent_id}: {info.get('name', 'Unknown')} ({info.get('agent_type', 'unknown')})")
        
        # Get specific agent
        if agents:
            agent_id = list(agents.keys())[0]
            agent = await agent_manager.get_agent(agent_id)
            if agent:
                print(f"\nGot agent: {agent.name}")
                print(f"Capabilities: {agent.capabilities}")
        
        # Discover agents by type
        assistants = await agent_manager.discover_agents("general_assistant")
        print(f"\nGeneral assistants found: {len(assistants)}")
        
        # Cleanup
        await agent_manager.cleanup()
        
    except Exception as e:
        print(f"Error in agent registry demo: {e}")


async def run_all_examples():
    """Run all examples"""
    print("Multi-Agent System - Usage Examples")
    print("==================================")
    
    examples = [
        ("Basic Agent Interaction", example_basic_agent_interaction),
        ("Memory System", example_memory_system),
        ("Prompt Templates", example_prompt_templates),
        ("Tool Usage", example_tool_usage),
        ("Workflow Orchestration", example_workflow_orchestration),
        ("Agent Registry", example_agent_registry),
    ]
    
    for name, example_func in examples:
        try:
            print(f"\nRunning: {name}")
            await example_func()
            print(f"✓ {name} completed successfully")
        except Exception as e:
            print(f"✗ {name} failed: {e}")
            logger.exception(f"Example '{name}' failed")
    
    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60)


if __name__ == "__main__":
    # Run examples
    asyncio.run(run_all_examples())