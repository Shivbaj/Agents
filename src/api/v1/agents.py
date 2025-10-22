"""
Agent-related API endpoints
"""
from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from loguru import logger

from src.api.v1.schemas import (
    AgentChatRequest,
    AgentChatResponse,
    AgentDiscoveryRequest,
    AgentDiscoveryResponse,
    AgentListResponse,
    AgentDetailsResponse,
    MultimodalRequest,
    AgentStatsResponse,
    AgentCardResponse,
    AgentInfo,
    CreateAgentRequest,
)
from src.agents.registry.manager import AgentManager
from src.core.exceptions import AgentNotFoundException, AgentExecutionException

router = APIRouter()


def get_agent_registry(request: Request) -> AgentManager:
    """Get agent registry from app state"""
    return request.app.state.agent_registry


@router.get("/discover", response_model=AgentDiscoveryResponse)
async def discover_agents(
    query: str,
    limit: int = 10,
    agent_registry: AgentManager = Depends(get_agent_registry)
):
    """
    Discover agents based on a query
    
    This endpoint analyzes the query and returns the most suitable agents
    for the task based on their capabilities and descriptions.
    
    Example usage:
    ```bash
    curl -X GET "http://localhost:8000/api/v1/agents/discover?query=summarize document&limit=5"
    ```
    """
    try:
        agents = await agent_registry.discover_agents(query, limit)
        return AgentDiscoveryResponse(
            query=query,
            agents=agents,
            total=len(agents)
        )
    except Exception as e:
        logger.error(f"Agent discovery failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Agent discovery failed")


@router.get("/list", response_model=AgentListResponse)
async def list_agents(
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    agent_registry: AgentManager = Depends(get_agent_registry)
):
    """
    List all available agents
    
    Optionally filter by agent type or status.
    
    Example usage:
    ```bash
    curl -X GET "http://localhost:8000/api/v1/agents/list"
    curl -X GET "http://localhost:8000/api/v1/agents/list?agent_type=text&status=active"
    ```
    """
    try:
        agents = agent_registry.list_agents(agent_type=agent_type, status=status)
        return AgentListResponse(
            agents=agents,
            total=len(agents)
        )
    except Exception as e:
        logger.error(f"Failed to list agents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list agents")


@router.get("/{agent_id}", response_model=AgentDetailsResponse)
async def get_agent_details(
    agent_id: str,
    agent_registry: AgentManager = Depends(get_agent_registry)
):
    """
    Get detailed information about a specific agent
    
    Example usage:
    ```bash
    curl -X GET "http://localhost:8000/api/v1/agents/summarizer_agent"
    ```
    """
    try:
        agent_info = agent_registry.get_agent_info(agent_id)
        if not agent_info:
            raise AgentNotFoundException(agent_id)
        
        return AgentDetailsResponse(**agent_info)
    except AgentNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent details: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get agent details")


@router.post("/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    request: AgentChatRequest,
    agent_registry: AgentManager = Depends(get_agent_registry)
):
    """
    Chat with a specific agent
    
    Send a message to an agent and get a response. The agent will process
    the message according to its capabilities and configuration.
    
    Example usage:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/agents/chat" \
      -H "Content-Type: application/json" \
      -d '{
        "message": "Hello, can you help me summarize this document?",
        "agent_id": "summarizer_agent",
        "session_id": "session_123"
      }'
    ```
    """
    try:
        # Get agent
        agent = agent_registry.get_agent(request.agent_id)
        if not agent:
            raise AgentNotFoundException(request.agent_id)
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid4())
        
        # Process message with agent
        response = await agent.process_message(
            message=request.message,
            session_id=session_id,
            context=request.context or {},
            stream=request.stream
        )
        
        return AgentChatResponse(
            response=response.content,
            agent_id=request.agent_id,
            session_id=session_id,
            metadata=response.metadata
        )
        
    except AgentNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Chat with agent failed: {str(e)}")
        raise AgentExecutionException(request.agent_id, str(e))


@router.post("/chat/stream")
async def stream_chat_with_agent(
    request: AgentChatRequest,
    agent_registry: AgentManager = Depends(get_agent_registry)
):
    """
    Stream chat with an agent
    
    Similar to the chat endpoint but returns a streaming response.
    Useful for long-running tasks or real-time interaction.
    
    Example usage:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/agents/chat/stream" \
      -H "Content-Type: application/json" \
      -d '{
        "message": "Write a long story about AI agents",
        "agent_id": "writer_agent",
        "stream": true
      }'
    ```
    """
    try:
        # Get agent
        agent = agent_registry.get_agent(request.agent_id)
        if not agent:
            raise AgentNotFoundException(request.agent_id)
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid4())
        
        # Create streaming response
        async def generate_response():
            async for chunk in agent.process_message_stream(
                message=request.message,
                session_id=session_id,
                context=request.context or {}
            ):
                yield f"data: {chunk}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except AgentNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Stream chat with agent failed: {str(e)}")
        raise AgentExecutionException(request.agent_id, str(e))


@router.get("/stats", response_model=AgentStatsResponse)
async def get_agent_stats(
    agent_registry: AgentManager = Depends(get_agent_registry)
):
    """
    Get comprehensive statistics about all agents
    
    Returns detailed statistics including agent counts, types, providers, and capabilities.
    
    Example usage:
    ```bash
    curl http://localhost:8000/api/v1/agents/stats
    ```
    """
    try:
        agents = agent_registry.list_agents()
        
        # Calculate statistics
        total_agents = len(agents)
        active_agents = len([a for a in agents if a.get("status") == "active"])
        
        # Count by agent type
        agent_types = {}
        for agent in agents:
            agent_type = agent.get("agent_type", "unknown")
            agent_types[agent_type] = agent_types.get(agent_type, 0) + 1
        
        # Count by model provider
        model_providers = {}
        for agent in agents:
            provider = agent.get("model_provider", "unknown")
            model_providers[provider] = model_providers.get(provider, 0) + 1
        
        # Count capabilities
        capabilities_stats = {}
        for agent in agents:
            for capability in agent.get("capabilities", []):
                capabilities_stats[capability] = capabilities_stats.get(capability, 0) + 1
        
        return AgentStatsResponse(
            total_agents=total_agents,
            active_agents=active_agents,
            agent_types=agent_types,
            model_providers=model_providers,
            capabilities_stats=capabilities_stats
        )
        
    except Exception as e:
        logger.error(f"Failed to get agent stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get agent statistics")


@router.get("/{agent_id}/card", response_model=AgentCardResponse)
async def get_agent_card(
    agent_id: str,
    agent_registry: AgentManager = Depends(get_agent_registry)
):
    """
    Get detailed agent card with comprehensive information
    
    Returns a detailed "card" view of an agent including performance metrics,
    usage statistics, configuration, and health status.
    
    Example usage:
    ```bash
    curl http://localhost:8000/api/v1/agents/general_assistant/card
    ```
    """
    try:
        # Get basic agent info
        agent_info_dict = agent_registry.get_agent_info(agent_id)
        if not agent_info_dict:
            raise AgentNotFoundException(agent_id)
        
        # Convert to AgentInfo model
        agent_info = AgentInfo(**agent_info_dict)
        
        # Get agent instance for additional info
        agent = agent_registry.get_agent(agent_id)
        
        # Performance metrics (mock data for now)
        performance_metrics = {
            "average_response_time": 1.25,
            "success_rate": 98.5,
            "total_interactions": getattr(agent, 'interaction_count', 0) if agent else 0,
            "error_rate": 1.5,
            "uptime_percentage": 99.2
        }
        
        # Usage statistics
        usage_statistics = {
            "interactions_today": 45,
            "interactions_this_week": 312,
            "interactions_this_month": 1247,
            "popular_capabilities": agent_info.capabilities[:3] if agent_info.capabilities else [],
            "peak_usage_hour": "14:00-15:00"
        }
        
        # Configuration
        configuration = {
            "model_provider": agent_info.model_provider,
            "model_name": agent_info.model_name,
            "supports_streaming": agent_info.supports_streaming,
            "supports_multimodal": agent_info.supports_multimodal,
            "max_context_length": 4096,
            "temperature": 0.7
        }
        
        # Health status
        health_status = "healthy" if agent_info.status == "active" else "unhealthy"
        
        # Last interaction (mock)
        last_interaction = datetime.now() if agent else None
        
        return AgentCardResponse(
            agent_info=agent_info,
            performance_metrics=performance_metrics,
            usage_statistics=usage_statistics,
            configuration=configuration,
            health_status=health_status,
            last_interaction=last_interaction
        )
        
    except AgentNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent card for '{agent_id}': {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get agent card")


@router.post("/register", response_model=AgentDetailsResponse)
async def register_dummy_agent(
    request: CreateAgentRequest,
    agent_registry: AgentManager = Depends(get_agent_registry)
):
    """
    Register a new dummy agent for testing
    
    Creates and registers a new dummy agent with the specified configuration.
    
    Example usage:
    ```bash
    curl -X POST http://localhost:8000/api/v1/agents/register \
      -H "Content-Type: application/json" \
      -d '{
        "agent_id": "test_dummy",
        "name": "Test Dummy Agent",
        "description": "A test agent for demonstration",
        "capabilities": ["echo", "greeting", "math"]
      }'
    ```
    """
    try:
        # Check if agent already exists
        if agent_registry.get_agent(request.agent_id):
            raise HTTPException(
                status_code=400,
                detail=f"Agent with ID '{request.agent_id}' already exists"
            )
        
        # Import and create dummy agent
        from src.agents.implementations.dummy_agent import DummyAgent
        
        dummy_agent = DummyAgent(
            agent_id=request.agent_id,
            name=request.name,
            description=request.description,
            capabilities=request.capabilities
        )
        
        # Initialize the agent
        await dummy_agent.initialize()
        
        # Register with manager
        agent_registry.register_agent(dummy_agent)
        
        # Get registered agent info
        agent_info = agent_registry.get_agent_info(request.agent_id)
        
        return AgentDetailsResponse(
            **agent_info,
            performance_stats={"newly_created": True},
            recent_interactions=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register dummy agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to register agent: {str(e)}")


@router.delete("/{agent_id}")
async def unregister_agent(
    agent_id: str,
    agent_registry: AgentManager = Depends(get_agent_registry)
):
    """
    Unregister an agent from the system
    
    Removes an agent from the registry and cleans up its resources.
    
    Example usage:
    ```bash
    curl -X DELETE http://localhost:8000/api/v1/agents/test_dummy
    ```
    """
    try:
        # Check if agent exists
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            raise AgentNotFoundException(agent_id)
        
        # Unregister agent
        success = agent_registry.unregister_agent(agent_id)
        
        if success:
            return {"message": f"Agent '{agent_id}' unregistered successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to unregister agent '{agent_id}'")
            
    except AgentNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to unregister agent '{agent_id}': {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to unregister agent")


@router.post("/multimodal", response_model=AgentChatResponse)
async def multimodal_chat(
    request: MultimodalRequest = Depends(),
    file: UploadFile = File(...),
    agent_registry: AgentManager = Depends(get_agent_registry)
):
    """
    Multimodal chat with file upload
    
    Send a message along with a file (image, document, etc.) to a multimodal agent.
    
    Example usage:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/agents/multimodal" \
      -F "file=@image.jpg" \
      -F "message=Describe this image" \
      -F "agent_id=vision_agent"
    ```
    """
    try:
        # Validate agent supports multimodal
        agent_info = agent_registry.get_agent_info(request.agent_id)
        if not agent_info or not agent_info.get("supports_multimodal", False):
            raise HTTPException(
                status_code=400,
                detail=f"Agent '{request.agent_id}' does not support multimodal input"
            )
        
        # Get agent
        agent = agent_registry.get_agent(request.agent_id)
        if not agent:
            raise AgentNotFoundException(request.agent_id)
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid4())
        
        # Read file content
        file_content = await file.read()
        
        # Process multimodal message
        context = {
            "file_content": file_content,
            "file_name": file.filename,
            "file_type": file.content_type
        }
        
        response = await agent.process_message(
            message=request.message,
            session_id=session_id,
            context=context
        )
        
        return AgentChatResponse(
            response=response.content,
            agent_id=request.agent_id,
            session_id=session_id,
            metadata=response.metadata
        )
        
    except AgentNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Multimodal chat failed: {str(e)}")
        raise AgentExecutionException(request.agent_id, str(e))


@router.post("/{agent_id}/reload")
async def reload_agent(
    agent_id: str,
    agent_registry: AgentManager = Depends(get_agent_registry)
):
    """
    Reload a specific agent
    
    Useful for development or when agent configuration has changed.
    
    Example usage:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/agents/summarizer_agent/reload"
    ```
    """
    try:
        success = await agent_registry.reload_agent(agent_id)
        if not success:
            raise AgentNotFoundException(agent_id)
        
        return {"message": f"Agent '{agent_id}' reloaded successfully"}
    except AgentNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to reload agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reload agent")