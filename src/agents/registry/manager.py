"""
Agent Manager - Manages agent discovery, loading, and lifecycle

This module provides a centralized registry for managing all agents in the system.
It handles agent discovery, loading, lifecycle management, and provides
query-based agent selection capabilities.

Example:
    ```python
    from src.agents.registry.manager import AgentManager
    
    # Create and initialize manager
    manager = AgentManager()
    await manager.initialize()
    
    # Discover agents for a task
    agents = await manager.discover_agents("text summarization")
    
    # Get specific agent
    agent = manager.get_agent("text_processor_agent")
    ```
"""
import asyncio
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from loguru import logger

from src.agents.base.agent import BaseAgent
from src.config.settings import get_settings


class AgentManager:
    """
    Central registry for managing all agents in the system
    
    Handles agent discovery, loading, lifecycle management, and provides
    query-based agent selection capabilities.
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_metadata: Dict[str, Dict[str, Any]] = {}
        self.settings = get_settings()
        
    async def initialize(self):
        """Initialize the agent registry"""
        logger.info("Initializing Agent Registry...")
        
        # Ensure agents implementations directory exists
        agents_dir = Path("src/agents/implementations")
        agents_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Agent Registry initialized")
    
    async def discover_and_load_agents(self):
        """Discover and load all available agents"""
        logger.info("Discovering and loading agents...")
        
        # Load agents from the implementations directory
        agents_dir = Path("src/agents/implementations")
        if not agents_dir.exists():
            logger.warning(f"Agents directory not found: {agents_dir}")
            return
        
        # Scan for agent files
        for agent_file in agents_dir.glob("*.py"):
            if agent_file.name.startswith("_"):
                continue
                
            try:
                await self._load_agent_from_file(agent_file)
            except Exception as e:
                logger.error(f"Failed to load agent from {agent_file}: {str(e)}")
        
        logger.info(f"Loaded {len(self.agents)} agents")
    
    async def _load_agent_from_file(self, agent_file: Path):
        """Load an agent from a Python file"""
        module_name = f"src.agents.implementations.{agent_file.stem}"
        
        try:
            # Import the module
            module = importlib.import_module(module_name)
            
            # Find agent classes in the module
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseAgent) and 
                    obj != BaseAgent):
                    
                    # Instantiate the agent
                    agent_instance = obj()
                    await agent_instance.initialize()
                    
                    # Register the agent
                    self.agents[agent_instance.id] = agent_instance
                    self.agent_metadata[agent_instance.id] = {
                        "name": agent_instance.name,
                        "description": agent_instance.description,
                        "agent_type": agent_instance.agent_type,
                        "capabilities": agent_instance.capabilities,
                        "model_provider": agent_instance.model_provider,
                        "model_name": agent_instance.model_name,
                        "status": "active",
                        "supports_streaming": agent_instance.supports_streaming,
                        "supports_multimodal": agent_instance.supports_multimodal,
                        "created_at": datetime.now(),
                        "updated_at": datetime.now(),
                    }
                    
                    logger.info(f"Loaded agent: {agent_instance.id} ({agent_instance.name})")
                    break
                    
        except Exception as e:
            logger.error(f"Error loading agent from {agent_file}: {str(e)}")
            raise
    
    async def discover_agents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Discover agents based on a natural language query
        
        Uses semantic matching to find the most relevant agents for a given query.
        """
        logger.info(f"Discovering agents for query: {query}")
        
        if not self.agents:
            return []
        
        # Simple keyword-based matching for now
        # In production, this could use embedding-based similarity
        query_lower = query.lower()
        scored_agents = []
        
        for agent_id, metadata in self.agent_metadata.items():
            score = 0
            
            # Check name and description
            if query_lower in metadata["name"].lower():
                score += 10
            if query_lower in metadata["description"].lower():
                score += 5
            
            # Check capabilities
            for capability in metadata["capabilities"]:
                if any(word in capability.lower() for word in query_lower.split()):
                    score += 3
            
            # Check agent type
            if query_lower in metadata["agent_type"].lower():
                score += 2
            
            if score > 0:
                agent_info = dict(metadata)
                agent_info["id"] = agent_id
                agent_info["relevance_score"] = score
                scored_agents.append(agent_info)
        
        # Sort by relevance score and limit results
        scored_agents.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_agents[:limit]
    
    def list_agents(self, agent_type: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all registered agents with optional filtering"""
        agents = []
        
        for agent_id, metadata in self.agent_metadata.items():
            # Apply filters
            if agent_type and metadata["agent_type"] != agent_type:
                continue
            if status and metadata["status"] != status:
                continue
            
            agent_info = dict(metadata)
            agent_info["id"] = agent_id
            agents.append(agent_info)
        
        return agents
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent instance by ID"""
        return self.agents.get(agent_id)
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent metadata by ID"""
        if agent_id in self.agent_metadata:
            info = dict(self.agent_metadata[agent_id])
            info["id"] = agent_id
            return info
        return None
    
    async def reload_agent(self, agent_id: str) -> bool:
        """Reload a specific agent"""
        try:
            if agent_id not in self.agents:
                return False
            
            # Get the agent class and reload it
            agent = self.agents[agent_id]
            
            # Remove old instance
            await agent.cleanup()
            del self.agents[agent_id]
            del self.agent_metadata[agent_id]
            
            # Try to reload from file
            # This is a simplified approach - in production you'd want more robust reloading
            await self.discover_and_load_agents()
            
            return agent_id in self.agents
            
        except Exception as e:
            logger.error(f"Failed to reload agent {agent_id}: {str(e)}")
            return False
    
    async def register_agent(self, agent: BaseAgent):
        """Manually register an agent instance"""
        try:
            await agent.initialize()
            
            self.agents[agent.id] = agent
            self.agent_metadata[agent.id] = {
                "name": agent.name,
                "description": agent.description,
                "agent_type": agent.agent_type,
                "capabilities": agent.capabilities,
                "model_provider": agent.model_provider,
                "model_name": agent.model_name,
                "status": "active",
                "supports_streaming": agent.supports_streaming,
                "supports_multimodal": agent.supports_multimodal,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
            
            logger.info(f"Registered agent: {agent.id}")
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent.id}: {str(e)}")
            raise
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        try:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                await agent.cleanup()
                del self.agents[agent_id]
                del self.agent_metadata[agent_id]
                logger.info(f"Unregistered agent: {agent_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unregister agent {agent_id}: {str(e)}")
            return False
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent instance (synchronous version)"""
        try:
            self.agents[agent.agent_id] = agent
            self.agent_metadata[agent.agent_id] = {
                "id": agent.agent_id,
                "name": agent.name,
                "description": agent.description,
                "agent_type": getattr(agent, 'agent_type', 'general'),
                "capabilities": agent.capabilities,
                "model_provider": getattr(agent, 'model_provider', 'ollama'),
                "model_name": getattr(agent, 'model_name', 'phi3:mini'),
                "status": "active",
                "supports_streaming": getattr(agent, 'supports_streaming', False),
                "supports_multimodal": getattr(agent, 'supports_multimodal', False),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
            
            logger.info(f"Registered agent: {agent.agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent.agent_id}: {str(e)}")
            raise
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent (synchronous version)"""
        try:
            if agent_id in self.agents:
                # Note: cleanup is async, but we can't await here
                # In production, you might want to handle this differently
                del self.agents[agent_id]
                del self.agent_metadata[agent_id]
                logger.info(f"Unregistered agent: {agent_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unregister agent {agent_id}: {str(e)}")
            return False

    async def cleanup(self):
        """Cleanup all agents and resources"""
        logger.info("Cleaning up Agent Registry...")
        
        for agent_id, agent in self.agents.items():
            try:
                await agent.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up agent {agent_id}: {str(e)}")
        
        self.agents.clear()
        self.agent_metadata.clear()
        
        logger.info("Agent Registry cleanup complete")