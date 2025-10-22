# Multi-Agent System - Development Guide

This guide provides comprehensive instructions for developing with the multi-agent system, including how to add new agents, integrate MCP servers and tools, set up observability, and extend the system capabilities.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Adding New Agents](#adding-new-agents)
3. [Creating MCP Tools and Servers](#creating-mcp-tools-and-servers)
4. [Integrating Observability](#integrating-observability)
5. [API Development](#api-development)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [Best Practices](#best-practices)

## Architecture Overview

The system follows a modular architecture with clear separation of concerns:

```
src/
├── agents/                 # Agent implementations
│   ├── base/              # Base agent classes
│   ├── implementations/   # Specific agent implementations
│   └── registry/          # Agent management and discovery
├── mcp/                   # Model Context Protocol integration
│   ├── base/             # Base MCP classes
│   ├── servers/          # MCP server implementations
│   ├── tools/            # Individual tool implementations
│   └── manager.py        # MCP server and tool management
├── observability/         # Monitoring and tracing
├── api/                  # REST API endpoints
├── models/               # LLM provider integrations
├── config/               # Configuration management
└── utils/                # Utility functions
```

### Key Design Principles

1. **Modularity**: Each component is self-contained and replaceable
2. **Extensibility**: Easy to add new agents, tools, and capabilities
3. **Observability**: Comprehensive tracing and monitoring built-in
4. **Type Safety**: Full type hints and Pydantic validation
5. **Async First**: Built for high-performance async operations

## Adding New Agents

### 1. Create Agent Implementation

Create a new agent in `src/agents/implementations/`:

```python
# src/agents/implementations/my_agent.py
from typing import Dict, Any, Optional, List
from src.agents.base.agent import BaseAgent
from src.models.schemas import ChatMessage, AgentResponse

class MyAgent(BaseAgent):
    """
    Custom agent for specific domain tasks
    
    Capabilities:
    - Domain-specific reasoning
    - Tool integration
    - Custom processing logic
    """
    
    def __init__(self, model_provider: str = "openai", model_name: str = "gpt-4"):
        super().__init__(
            agent_id="my_agent",
            name="My Custom Agent", 
            description="Agent for domain-specific tasks",
            capabilities=["reasoning", "analysis", "tool_usage"],
            model_provider=model_provider,
            model_name=model_name
        )
    
    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[ChatMessage]] = None
    ) -> AgentResponse:
        """Process user message and return response"""
        
        # Use observability
        from src.observability import get_tracer
        tracer = get_tracer()
        
        async with tracer.trace_agent(self.agent_id, {"message": message}) as trace:
            try:
                # Add context metadata
                trace.add_metadata({
                    "model": self.model_name,
                    "capabilities": self.capabilities,
                    "context_size": len(context) if context else 0
                })
                
                # Process the message
                processed_response = await self._process_with_tools(message, context)
                
                response = AgentResponse(
                    agent_id=self.agent_id,
                    response=processed_response,
                    metadata={
                        "model_used": self.model_name,
                        "processing_time": trace.trace.duration or 0
                    }
                )
                
                trace.log_result({"response": processed_response})
                return response
                
            except Exception as e:
                trace.log_error(str(e))
                raise
    
    async def _process_with_tools(self, message: str, context: Optional[Dict[str, Any]]) -> str:
        """Process message using available tools"""
        
        # Example: Use MCP tools
        from src.mcp.manager import get_mcp_manager
        
        mcp_manager = get_mcp_manager()
        
        # Determine if we need to use tools
        if "search" in message.lower():
            # Use web search tool
            search_response = await mcp_manager.execute_tool(
                "web_search",
                {"query": message, "max_results": 5}
            )
            
            if search_response.success:
                # Process search results
                results = search_response.result.get("results", [])
                return f"Found {len(results)} results: {results[0]['title'] if results else 'No results'}"
        
        # Default processing
        return f"Processed message: {message}"
    
    def get_system_prompt(self) -> str:
        """Return system prompt for the agent"""
        return """
        You are a helpful assistant specialized in domain-specific tasks.
        You have access to various tools and can provide detailed analysis.
        
        Guidelines:
        - Be precise and helpful in your responses
        - Use tools when appropriate
        - Provide clear explanations
        - Ask clarifying questions when needed
        """
```

### 2. Register Agent

The agent will be automatically discovered by the AgentManager. Ensure your agent class:

1. Inherits from `BaseAgent`
2. Has a unique `agent_id`
3. Is placed in the `src/agents/implementations/` directory

### 3. Test Agent

Create tests in `tests/agents/`:

```python
# tests/agents/test_my_agent.py
import pytest
from src.agents.implementations.my_agent import MyAgent
from src.models.schemas import ChatMessage

@pytest.mark.asyncio
async def test_my_agent_basic_functionality():
    agent = MyAgent()
    
    response = await agent.process_message("Hello, world!")
    
    assert response.agent_id == "my_agent"
    assert response.response is not None
    assert isinstance(response.metadata, dict)

@pytest.mark.asyncio
async def test_my_agent_with_context():
    agent = MyAgent()
    
    context = {"user_preferences": {"language": "en"}}
    response = await agent.process_message("Test message", context=context)
    
    assert response.response is not None
```

## Creating MCP Tools and Servers

### 1. Create Custom Tool

```python
# src/tools/custom_tool.py
from src.mcp.base.tool import BaseMCPTool, MCPToolRequest, MCPToolResponse

class CustomTool(BaseMCPTool):
    """Custom tool for specific functionality"""
    
    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="Performs custom operations",
            parameters_schema={
                "type": "object",
                "properties": {
                    "input_text": {
                        "type": "string",
                        "description": "Text to process"
                    },
                    "operation": {
                        "type": "string", 
                        "enum": ["uppercase", "lowercase", "reverse"],
                        "description": "Operation to perform"
                    }
                },
                "required": ["input_text", "operation"]
            },
            capabilities=["text_processing"]
        )
    
    async def execute(self, request: MCPToolRequest) -> MCPToolResponse:
        """Execute the custom tool"""
        try:
            input_text = request.parameters["input_text"]
            operation = request.parameters["operation"]
            
            if operation == "uppercase":
                result = input_text.upper()
            elif operation == "lowercase":  
                result = input_text.lower()
            elif operation == "reverse":
                result = input_text[::-1]
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            return MCPToolResponse(
                success=True,
                result={
                    "input": input_text,
                    "operation": operation,
                    "output": result
                }
            )
            
        except Exception as e:
            return MCPToolResponse(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )
```

### 2. Create Custom Server

```python
# src/mcp/servers/custom_server.py
from typing import List
from src.mcp.base.tool import BaseMCPServer, BaseMCPTool
from src.tools.custom_tool import CustomTool

class CustomServer(BaseMCPServer):
    """Custom MCP server providing domain-specific tools"""
    
    def __init__(self):
        super().__init__(
            name="custom_server",
            version="1.0.0",
            description="Provides custom domain-specific tools",
            capabilities=["text_processing", "analysis"]
        )
    
    async def initialize(self):
        """Initialize the server"""
        if self.is_initialized:
            return
        
        print(f"Initializing {self.name}...")
        
        # Perform any setup here (API keys, connections, etc.)
        
        self.is_initialized = True
        print(f"{self.name} initialized successfully")
    
    async def register_tools(self) -> List[BaseMCPTool]:
        """Register tools provided by this server"""
        return [
            CustomTool(),
            # Add more tools here
        ]
```

### 3. Register Server

```python
# In your application startup (main.py or similar)
from src.mcp.manager import get_mcp_manager
from src.mcp.servers.custom_server import CustomServer

async def setup_mcp_servers():
    manager = get_mcp_manager()
    await manager.initialize()
    
    # Register your custom server
    custom_server = CustomServer()
    await manager.register_server(custom_server)
    
    print("Custom MCP server registered successfully")
```

### 4. Use Tools in Agents

```python
# In your agent implementation
async def use_custom_tool(self, text: str, operation: str) -> str:
    from src.mcp.manager import get_mcp_manager
    
    manager = get_mcp_manager()
    
    response = await manager.execute_tool(
        "custom_tool",
        {"input_text": text, "operation": operation}
    )
    
    if response.success:
        return response.result["output"]
    else:
        raise Exception(f"Tool failed: {response.error}")
```

## Integrating Observability

### 1. Initialize Observability

```python
# In main.py
from src.observability import initialize_observability

async def startup():
    # Initialize observability
    await initialize_observability(
        project_name="my-agent-system",
        environment="production"  # or get from env var
    )
```

### 2. Use in Agents

```python
from src.observability import get_tracer

class TracedAgent(BaseAgent):
    def __init__(self):
        super().__init__(...)
        self.tracer = get_tracer()
    
    async def process_message(self, message: str) -> AgentResponse:
        async with self.tracer.trace_agent(self.agent_id, {"message": message}) as trace:
            # Add metadata
            trace.add_metadata({
                "model": self.model_name,
                "user_id": "user_123"
            })
            
            # Process message
            result = await self._process(message)
            
            # Log result
            trace.log_result({"response": result})
            
            return AgentResponse(...)
```

### 3. Tool Tracing

```python
# Tools are automatically traced when using MCP manager
# For manual tracing:

async with self.tracer.trace_tool("my_tool", "my_server", parameters) as tool_trace:
    result = await execute_tool_logic(parameters)
    tool_trace.log_result(result)
```

### 4. Custom Events

```python
from src.observability import get_tracer, TraceLevel

tracer = get_tracer()

# Log custom events
await tracer.log_event(
    "user_login",
    {"user_id": "123", "method": "oauth"},
    level=TraceLevel.INFO
)
```

## API Development

### 1. Add New Endpoint

```python
# src/api/v1/custom.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/custom", tags=["custom"])

class CustomRequest(BaseModel):
    data: str
    options: Optional[dict] = None

class CustomResponse(BaseModel):
    result: str
    metadata: dict

@router.post("/process", response_model=CustomResponse)
async def process_custom_data(
    request: CustomRequest
) -> CustomResponse:
    """Process custom data with specialized logic"""
    
    try:
        # Process the data
        result = f"Processed: {request.data}"
        
        return CustomResponse(
            result=result,
            metadata={"processing_time": 0.1, "status": "success"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. Register Router

```python
# In main.py
from src.api.v1.custom import router as custom_router

app.include_router(custom_router, prefix="/api/v1")
```

### 3. Add Validation and Documentation

```python
from pydantic import BaseModel, Field, validator

class CustomRequest(BaseModel):
    data: str = Field(..., description="Input data to process", min_length=1)
    options: Optional[dict] = Field(None, description="Processing options")
    
    @validator('data')
    def validate_data(cls, v):
        if not v.strip():
            raise ValueError('Data cannot be empty')
        return v

    class Config:
        schema_extra = {
            "example": {
                "data": "Sample input text",
                "options": {"format": "json", "verbose": True}
            }
        }
```

## Testing

### 1. Unit Tests

```python
# tests/test_custom_functionality.py
import pytest
from src.agents.implementations.my_agent import MyAgent

@pytest.mark.asyncio
async def test_agent_functionality():
    agent = MyAgent()
    response = await agent.process_message("test message")
    
    assert response.agent_id == "my_agent"
    assert response.response is not None
```

### 2. Integration Tests

```python
# tests/integration/test_mcp_integration.py
import pytest
from src.mcp.manager import MCPManager
from src.mcp.servers.custom_server import CustomServer

@pytest.mark.asyncio
async def test_mcp_server_integration():
    manager = MCPManager()
    await manager.initialize()
    
    server = CustomServer()
    success = await manager.register_server(server)
    
    assert success
    assert "custom_tool" in manager.tool_registry
    
    # Test tool execution
    response = await manager.execute_tool(
        "custom_tool",
        {"input_text": "hello", "operation": "uppercase"}
    )
    
    assert response.success
    assert response.result["output"] == "HELLO"
```

### 3. API Tests

```python
# tests/api/test_endpoints.py
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_custom_endpoint():
    response = client.post(
        "/api/v1/custom/process",
        json={"data": "test input", "options": {}}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "metadata" in data
```

### 4. Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/agents/
pytest tests/mcp/
pytest tests/api/

# Run with coverage
pytest --cov=src tests/

# Run integration tests
pytest tests/integration/
```

## Deployment

### 1. Environment Configuration

```bash
# .env.production
ENVIRONMENT=production
LANGSMITH_API_KEY=your-production-key
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Database settings
REDIS_URL=redis://production-redis:6379

# Performance settings
MAX_WORKERS=4
TIMEOUT_SECONDS=30
```

### 2. Docker Deployment

```yaml
# docker-compose.production.yml
version: '3.8'
services:
  agent-system:
    build: .
    environment:
      - ENVIRONMENT=production
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - monitoring
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    
  monitoring:
    image: prom/prometheus
    restart: unless-stopped
```

### 3. Health Checks

```python
# src/api/health.py
from fastapi import APIRouter
from src.mcp.manager import get_mcp_manager
from src.observability import get_tracer

router = APIRouter()

@router.get("/health")
async def health_check():
    """Comprehensive health check"""
    
    # Check MCP manager
    manager = get_mcp_manager()
    mcp_health = await manager.health_check()
    
    # Check observability
    tracer = get_tracer()
    metrics = await tracer.get_metrics()
    
    return {
        "status": "healthy",
        "mcp": mcp_health,
        "observability": {
            "active_traces": len(tracer.active_traces),
            "total_executions": metrics["total_agent_executions"]
        }
    }
```

## Best Practices

### 1. Code Organization

- **Single Responsibility**: Each class/module has one clear purpose
- **Dependency Injection**: Use FastAPI's dependency system
- **Type Hints**: Always include comprehensive type hints
- **Documentation**: Include docstrings and comments

### 2. Error Handling

```python
from src.core.exceptions import AgentExecutionException

async def safe_agent_execution(agent, message):
    try:
        return await agent.process_message(message)
    except AgentExecutionException as e:
        # Handle agent-specific errors
        logger.error(f"Agent execution failed: {e}")
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error: {e}")
        raise AgentExecutionException(f"Unexpected error: {e}")
```

### 3. Performance Optimization

```python
# Use connection pooling
from aiohttp import ClientSession, TCPConnector

connector = TCPConnector(limit=100, limit_per_host=30)
session = ClientSession(connector=connector)

# Use caching for expensive operations
from functools import lru_cache

@lru_cache(maxsize=1000)
def expensive_computation(input_data: str) -> str:
    # Expensive operation
    return result
```

### 4. Security

```python
# Input validation
from pydantic import validator, Field

class SecureRequest(BaseModel):
    data: str = Field(..., max_length=10000)
    
    @validator('data')
    def sanitize_input(cls, v):
        # Remove potentially harmful content
        return sanitize(v)

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/process")
@limiter.limit("10/minute")
async def process_request(request: Request, data: str):
    # Protected endpoint
    pass
```

### 5. Monitoring and Alerting

```python
# Custom metrics
from src.observability import get_tracer

async def monitor_performance():
    tracer = get_tracer()
    metrics = await tracer.get_metrics()
    
    # Alert on high error rates
    error_rate = metrics["error_count"] / (metrics["success_count"] + metrics["error_count"])
    if error_rate > 0.1:  # 10% threshold
        # Send alert
        await send_alert("High error rate detected", {"rate": error_rate})
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Check Python path and module structure
2. **MCP Tool Not Found**: Verify server registration and tool names
3. **Tracing Issues**: Ensure observability is initialized before use
4. **Performance Issues**: Check connection pooling and caching
5. **Memory Issues**: Monitor for memory leaks in long-running agents

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable FastAPI debug mode
app = FastAPI(debug=True)

# Enable detailed error traces
import traceback
traceback.print_exc()
```

### Profiling

```python
# Profile agent performance
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run your code
result = await agent.process_message("test")

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

This development guide provides a comprehensive foundation for extending and maintaining the multi-agent system. Follow these patterns and practices to ensure consistent, maintainable, and scalable code.