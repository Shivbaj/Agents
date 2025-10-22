"""
Pydantic schemas for API requests and responses
"""
from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class AgentInfo(BaseModel):
    """Agent information schema"""
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Human-readable agent name")
    description: str = Field(..., description="Agent description")
    agent_type: str = Field(..., description="Type of agent (text, vision, audio, etc.)")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    model_provider: str = Field(..., description="LLM provider (openai, anthropic, etc.)")
    model_name: str = Field(..., description="Specific model name")
    status: str = Field(default="active", description="Agent status (active, inactive, error)")
    supports_streaming: bool = Field(default=False, description="Whether agent supports streaming")
    supports_multimodal: bool = Field(default=False, description="Whether agent supports multimodal input")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


class AgentChatRequest(BaseModel):
    """Request schema for agent chat"""
    message: str = Field(..., description="Message to send to the agent")
    agent_id: str = Field(..., description="ID of the agent to chat with")
    session_id: Optional[str] = Field(default=None, description="Session identifier for context")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    stream: bool = Field(default=False, description="Whether to stream the response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Hello, can you help me summarize this document?",
                "agent_id": "summarizer_agent",
                "session_id": "session_123",
                "context": {"document_type": "pdf"},
                "stream": False
            }
        }


class AgentChatResponse(BaseModel):
    """Response schema for agent chat"""
    response: str = Field(..., description="Agent's response")
    agent_id: str = Field(..., description="ID of the responding agent")
    session_id: str = Field(..., description="Session identifier")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Response metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "I'd be happy to help you summarize the document. Please provide the document content or upload the file.",
                "agent_id": "summarizer_agent",
                "session_id": "session_123",
                "metadata": {
                    "model_used": "gpt-4-turbo-preview",
                    "tokens_used": 150,
                    "processing_time": 2.5
                }
            }
        }


class AgentDiscoveryRequest(BaseModel):
    """Request schema for agent discovery"""
    query: str = Field(..., description="Query to discover relevant agents")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of agents to return")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")


class AgentDiscoveryResponse(BaseModel):
    """Response schema for agent discovery"""
    query: str = Field(..., description="Original query")
    agents: List[AgentInfo] = Field(..., description="List of discovered agents")
    total: int = Field(..., description="Total number of agents found")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "summarize document",
                "agents": [
                    {
                        "id": "summarizer_agent",
                        "name": "Document Summarizer",
                        "description": "Specializes in summarizing various document types",
                        "agent_type": "text",
                        "capabilities": ["summarization", "text_analysis"],
                        "model_provider": "openai",
                        "model_name": "gpt-4-turbo-preview",
                        "status": "active"
                    }
                ],
                "total": 1
            }
        }


class AgentListResponse(BaseModel):
    """Response schema for agent listing"""
    agents: List[AgentInfo] = Field(..., description="List of agents")
    total: int = Field(..., description="Total number of agents")


class AgentDetailsResponse(AgentInfo):
    """Detailed agent information response"""
    performance_stats: Optional[Dict[str, Any]] = Field(default=None, description="Performance statistics")
    recent_interactions: Optional[int] = Field(default=None, description="Number of recent interactions")


class MultimodalRequest(BaseModel):
    """Request schema for multimodal interactions"""
    message: str = Field(..., description="Text message")
    agent_id: str = Field(..., description="ID of the agent")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    file_types: Optional[List[str]] = Field(default=None, description="Expected file types")


# Model-related schemas
class ModelInfo(BaseModel):
    """Model information schema"""
    provider: str = Field(..., description="Model provider (openai, anthropic, etc.)")
    name: str = Field(..., description="Model name")
    model_type: str = Field(..., description="Type of model (text, vision, audio, embedding)")
    description: str = Field(..., description="Model description")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens supported")
    supports_streaming: bool = Field(default=False, description="Whether model supports streaming")
    supports_vision: bool = Field(default=False, description="Whether model supports vision")
    supports_audio: bool = Field(default=False, description="Whether model supports audio")
    cost_per_token: Optional[float] = Field(default=None, description="Cost per token")
    status: str = Field(default="available", description="Model status")


class ModelListResponse(BaseModel):
    """Response schema for model listing"""
    models: List[ModelInfo] = Field(..., description="List of available models")
    total: int = Field(..., description="Total number of models")


class ModelTestRequest(BaseModel):
    """Request schema for model testing"""
    provider: str = Field(..., description="Model provider")
    model_name: str = Field(..., description="Model name to test")
    test_message: str = Field(default="Hello, world!", description="Test message")


class ModelTestResponse(BaseModel):
    """Response schema for model testing"""
    provider: str = Field(..., description="Model provider")
    model_name: str = Field(..., description="Model name")
    status: str = Field(..., description="Test status (success, failed)")
    response: Optional[str] = Field(default=None, description="Model response")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    latency: float = Field(..., description="Response latency in seconds")


# Health check schemas
class HealthResponse(BaseModel):
    """Health check response schema"""
    status: str = Field(..., description="Overall system health status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(..., description="Health check timestamp")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Component health status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "v1",
                "timestamp": "2024-01-01T00:00:00Z",
                "components": {
                    "database": {"status": "healthy", "response_time": 0.05},
                    "redis": {"status": "healthy", "response_time": 0.01},
                    "ollama": {"status": "healthy", "models_loaded": 1}
                }
            }
        }


# MCP-related schemas
class MCPToolInfo(BaseModel):
    """MCP tool information schema"""
    tool_name: str = Field(..., description="Name of the MCP tool")
    server_id: str = Field(..., description="ID of the server providing this tool")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters schema")
    availability: str = Field(default="available", description="Tool availability status")


class MCPToolsResponse(BaseModel):
    """Response schema for MCP tools listing"""
    tools: List[MCPToolInfo] = Field(..., description="List of available MCP tools")
    total: int = Field(..., description="Total number of tools")
    servers_count: int = Field(..., description="Number of servers providing tools")


class MCPServerResponse(BaseModel):
    """Response schema for MCP server information"""
    server_id: str = Field(..., description="Unique server identifier")
    name: str = Field(..., description="Server name")
    description: str = Field(..., description="Server description")
    status: str = Field(..., description="Server status")
    tools_count: int = Field(..., description="Number of tools provided by server")
    tools: List[str] = Field(default_factory=list, description="List of tool names")


class MCPToolExecuteRequest(BaseModel):
    """Request schema for executing MCP tools"""
    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tool_name": "web_search",
                "arguments": {
                    "query": "Python programming tutorials",
                    "max_results": 5
                }
            }
        }


class MCPToolExecuteResponse(BaseModel):
    """Response schema for MCP tool execution"""
    tool_name: str = Field(..., description="Name of the executed tool")
    success: bool = Field(..., description="Whether execution was successful")
    result: Optional[Any] = Field(default=None, description="Tool execution result")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Execution metadata")


# Agent Registry Enhancement schemas
class AgentStatsResponse(BaseModel):
    """Response schema for agent statistics"""
    total_agents: int = Field(..., description="Total number of registered agents")
    active_agents: int = Field(..., description="Number of active agents")
    agent_types: Dict[str, int] = Field(..., description="Count by agent type")
    model_providers: Dict[str, int] = Field(..., description="Count by model provider")
    capabilities_stats: Dict[str, int] = Field(..., description="Capabilities distribution")


class AgentCardResponse(BaseModel):
    """Response schema for detailed agent card information"""
    agent_info: AgentInfo = Field(..., description="Basic agent information")
    performance_metrics: Dict[str, Any] = Field(..., description="Performance metrics")
    usage_statistics: Dict[str, Any] = Field(..., description="Usage statistics")
    configuration: Dict[str, Any] = Field(..., description="Agent configuration")
    health_status: str = Field(..., description="Current health status")
    last_interaction: Optional[datetime] = Field(default=None, description="Last interaction timestamp")


class CreateAgentRequest(BaseModel):
    """Request schema for creating a new agent"""
    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    agent_type: str = Field(default="general", description="Agent type")
    model_provider: str = Field(default="ollama", description="Model provider")
    model_name: str = Field(default="phi3:mini", description="Model name")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Additional configuration")


# Error schemas
class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")
    type: str = Field(..., description="Error type")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")