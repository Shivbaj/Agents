"""
Test the agent registry functionality
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from src.agents.registry.manager import AgentManager
from src.agents.base.agent import BaseAgent


class MockAgent(BaseAgent):
    """Mock agent for testing"""
    
    def __init__(self, agent_id="test_agent"):
        super().__init__(
            agent_id=agent_id,
            name="Test Agent",
            description="A test agent for unit testing",
            agent_type="test",
            capabilities=["testing", "mock_processing"]
        )
    
    async def _initialize_agent(self):
        """Mock initialization"""
        pass
    
    async def _process_message(self, message, session_id, context):
        """Mock message processing"""
        from src.agents.base.agent import AgentResponse
        return AgentResponse(
            content=f"Mock response to: {message}",
            metadata={"test": True}
        )


@pytest.fixture
async def agent_registry():
    """Create an agent registry for testing"""
    registry = AgentManager()
    await registry.initialize()
    return registry


@pytest.fixture
async def mock_agent():
    """Create a mock agent for testing"""
    agent = MockAgent()
    await agent.initialize()
    return agent


@pytest.mark.asyncio
async def test_agent_registry_initialization(agent_registry):
    """Test agent registry initialization"""
    assert agent_registry.agents == {}
    assert agent_registry.agent_metadata == {}


@pytest.mark.asyncio
async def test_register_agent(agent_registry, mock_agent):
    """Test manual agent registration"""
    await agent_registry.register_agent(mock_agent)
    
    assert mock_agent.id in agent_registry.agents
    assert mock_agent.id in agent_registry.agent_metadata
    
    agent_info = agent_registry.get_agent_info(mock_agent.id)
    assert agent_info is not None
    assert agent_info["name"] == "Test Agent"
    assert agent_info["agent_type"] == "test"


@pytest.mark.asyncio
async def test_list_agents(agent_registry, mock_agent):
    """Test listing agents"""
    await agent_registry.register_agent(mock_agent)
    
    agents = agent_registry.list_agents()
    assert len(agents) == 1
    assert agents[0]["id"] == mock_agent.id
    
    # Test filtering by type
    test_agents = agent_registry.list_agents(agent_type="test")
    assert len(test_agents) == 1
    
    other_agents = agent_registry.list_agents(agent_type="other")
    assert len(other_agents) == 0


@pytest.mark.asyncio
async def test_discover_agents(agent_registry, mock_agent):
    """Test agent discovery"""
    await agent_registry.register_agent(mock_agent)
    
    # Test discovery with relevant query
    results = await agent_registry.discover_agents("testing")
    assert len(results) == 1
    assert results[0]["id"] == mock_agent.id
    
    # Test discovery with irrelevant query
    results = await agent_registry.discover_agents("irrelevant")
    assert len(results) == 0


@pytest.mark.asyncio
async def test_unregister_agent(agent_registry, mock_agent):
    """Test agent unregistration"""
    await agent_registry.register_agent(mock_agent)
    
    # Verify agent is registered
    assert mock_agent.id in agent_registry.agents
    
    # Unregister agent
    success = await agent_registry.unregister_agent(mock_agent.id)
    assert success
    assert mock_agent.id not in agent_registry.agents
    assert mock_agent.id not in agent_registry.agent_metadata


@pytest.mark.asyncio
async def test_get_agent(agent_registry, mock_agent):
    """Test getting agent instance"""
    await agent_registry.register_agent(mock_agent)
    
    retrieved_agent = agent_registry.get_agent(mock_agent.id)
    assert retrieved_agent is mock_agent
    
    nonexistent_agent = agent_registry.get_agent("nonexistent")
    assert nonexistent_agent is None


@pytest.mark.asyncio
async def test_cleanup(agent_registry, mock_agent):
    """Test registry cleanup"""
    await agent_registry.register_agent(mock_agent)
    
    # Verify agent is registered
    assert len(agent_registry.agents) == 1
    
    # Cleanup
    await agent_registry.cleanup()
    
    # Verify cleanup
    assert len(agent_registry.agents) == 0
    assert len(agent_registry.agent_metadata) == 0