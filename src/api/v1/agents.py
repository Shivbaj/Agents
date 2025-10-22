"""
Agent-related API endpoints
"""
from typing import List, Optional, Dict, Any
from uuid import uuid4

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


@router.post("/multimodal", response_model=AgentChatResponse)
async def multimodal_interaction(
    message: str = Form(...),
    agent_id: str = Form(...),
    session_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    agent_registry: AgentManager = Depends(get_agent_registry)
):
    """
    Interact with an agent using multimodal input (text + files)
    
    Send text along with files (images, audio, documents) to an agent
    that supports multimodal processing.
    
    Example usage:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/agents/multimodal" \
      -H "Content-Type: multipart/form-data" \
      -F "message=Describe this image and the document" \
      -F "agent_id=vision_agent" \
      -F "files=@image.jpg" \
      -F "files=@document.pdf"
    ```
    """
    try:
        # Get agent
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            raise AgentNotFoundException(agent_id)
        
        # Check if agent supports multimodal
        if not getattr(agent, 'supports_multimodal', False):
            raise HTTPException(
                status_code=400,
                detail=f"Agent '{agent_id}' does not support multimodal input"
            )
        
        # Generate session ID if not provided
        session_id = session_id or str(uuid4())
        
        # Process files
        file_data = []
        for file in files:
            content = await file.read()
            file_data.append({
                'filename': file.filename,
                'content_type': file.content_type,
                'content': content
            })
        
        # Process multimodal message
        response = await agent.process_multimodal_message(
            message=message,
            files=file_data,
            session_id=session_id
        )
        
        return AgentChatResponse(
            response=response.content,
            agent_id=agent_id,
            session_id=session_id,
            metadata=response.metadata
        )
        
    except AgentNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Multimodal interaction failed: {str(e)}")
        raise AgentExecutionException(agent_id, str(e))


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