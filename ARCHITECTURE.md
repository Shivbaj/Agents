#  Multi-Agent System Architecture Guide

This document explains the system architecture, design patterns, and guidelines for extending the codebase.

## 📋 Table of Contents
- [System Overview](#system-overview)
- [Directory Structure](#directory-structure)
- [Core Components](#core-components)
- [Adding New Components](#adding-new-components)
- [MCP Server Integration](#mcp-server-integration)
- [Observability with LangSmith](#observability-with-langsmith)
- [Best Practices](#best-practices)

##  System Overview

The Multi-Agent System is built using a modular, event-driven architecture that supports:
- **Multiple LLM Providers**: OpenAI, Anthropic, Ollama, and custom providers
- **Dynamic Agent Discovery**: Query-based agent selection and routing
- **MCP (Model Context Protocol) Integration**: Extensible tool and server framework
- **Observability**: LangSmith integration for monitoring and debugging
- **Async Processing**: Full async/await support for high concurrency
- **Type Safety**: Comprehensive Pydantic models and type hints

### Key Design Principles
1. **Modularity**: Each component is self-contained and loosely coupled
2. **Extensibility**: Easy to add new agents, models, tools, and servers
3. **Observability**: Full tracing and monitoring capabilities
4. **Testability**: Comprehensive test coverage with mocking
5. **Configuration-Driven**: Environment-based configuration
6. **Generic Naming**: Avoid business-specific terminology

##  Directory Structure

```
src/
├── agents/                 # Agent implementations
│   ├── base/              # Base classes and interfaces
│   ├── registry/          # Agent discovery and management
│   └── implementations/   # Concrete agent implementations
├── api/                   # REST API endpoints
│   └── v1/               # API version 1
├── config/               # Configuration management
├── core/                 # Core system components
│   ├── exceptions.py     # Custom exceptions
│   ├── logging.py        # Logging configuration
│   └── middleware.py     # FastAPI middleware
├── mcp/                  # Model Context Protocol integration
│   ├── servers/          # MCP server implementations
│   └── tools/           # MCP tools and resources
├── memory/              # Conversation and context management
├── models/              # LLM provider integrations
│   └── providers/       # Model provider implementations
├── observability/       # Monitoring and tracing
│   ├── langsmith.py     # LangSmith integration
│   └── metrics.py       # Performance metrics
├── orchestrator/        # Multi-agent orchestration
├── prompts/            # Prompt templates and management
├── services/           # Business logic services
├── tools/              # Shared tools and utilities
└── utils/              # Common utilities
```

## 🔧 Core Components

### Agent System
```python
# Base Agent Interface
class BaseAgent(ABC):
    \"\"\"Base class for all agents\"\"\"
    
    @abstractmethod
    async def process_message(self, message: str, context: AgentContext) -> AgentResponse:
        \"\"\"Process a message and return response\"\"\"
        
    @abstractmethod
    async def get_capabilities(self) -> List[AgentCapability]:
        \"\"\"Return agent capabilities for discovery\"\"\"
```

### Model Provider Interface
```python
# Model Provider Interface
class BaseModelProvider(ABC):
    \"\"\"Base class for all model providers\"\"\"
    
    @abstractmethod
    async def generate_response(self, request: ModelRequest) -> ModelResponse:
        \"\"\"Generate response using the model\"\"\"
        
    @abstractmethod
    async def get_model_info(self) -> ModelInfo:
        \"\"\"Get model information and capabilities\"\"\"
```

### MCP Integration
```python
# MCP Server Interface
class BaseMCPServer(ABC):
    \"\"\"Base class for MCP servers\"\"\"
    
    @abstractmethod
    async def register_tools(self) -> List[MCPTool]:
        \"\"\"Register tools provided by this server\"\"\"
        
    @abstractmethod
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        \"\"\"Handle MCP protocol requests\"\"\"
```

## ➕ Adding New Components

### 1. Adding a New Agent

Create a new agent by extending the base agent class:

```python
# src/agents/implementations/your_agent.py
from src.agents.base.agent import BaseAgent
from src.core.types import AgentContext, AgentResponse

class YourCustomAgent(BaseAgent):
    \"\"\"
    Custom agent for [specific task]
    
    Capabilities:
    - [capability 1]
    - [capability 2]
    \"\"\"
    
    def __init__(self):
        super().__init__(
            agent_id="your_custom_agent",
            name="Your Custom Agent",
            description="Agent that performs [specific task]",
            capabilities=["capability1", "capability2"],
            agent_type="custom"
        )
    
    async def _initialize_agent(self):
        \"\"\"Initialize agent-specific resources\"\"\"
        # Your initialization logic here
        pass
    
    async def _process_message(self, message: str, session_id: str, context: dict) -> AgentResponse:
        \"\"\"Process message with your custom logic\"\"\"
        # Your processing logic here
        return AgentResponse(
            content="Your response",
            metadata={"agent_type": "custom"}
        )
```

### 2. Adding a New Model Provider

```python
# src/models/providers/your_provider.py
from src.models.providers.base_provider import BaseModelProvider
from src.core.types import ModelRequest, ModelResponse

class YourModelProvider(BaseModelProvider):
    \"\"\"Custom model provider for [provider name]\"\"\"
    
    def __init__(self, api_key: str, base_url: str = None):
        super().__init__(provider_name="your_provider")
        self.api_key = api_key
        self.base_url = base_url
    
    async def generate_response(self, request: ModelRequest) -> ModelResponse:
        \"\"\"Generate response using your model\"\"\"
        # Your model integration logic
        pass
    
    async def list_models(self) -> List[ModelInfo]:
        \"\"\"List available models\"\"\"
        # Return list of available models
        pass
```

### 3. Adding MCP Tools

```python
# src/tools/your_tool.py
from src.mcp.base.tool import BaseMCPTool
from src.core.types import MCPToolRequest, MCPToolResponse

class YourMCPTool(BaseMCPTool):
    \"\"\"Custom MCP tool for [specific functionality]\"\"\"
    
    def __init__(self):
        super().__init__(
            name="your_tool",
            description="Tool that performs [specific task]",
            parameters_schema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "Parameter 1"},
                    "param2": {"type": "integer", "description": "Parameter 2"}
                },
                "required": ["param1"]
            }
        )
    
    async def execute(self, request: MCPToolRequest) -> MCPToolResponse:
        \"\"\"Execute the tool with given parameters\"\"\"
        # Your tool logic here
        return MCPToolResponse(
            success=True,
            result={"output": "Tool result"},
            metadata={"execution_time": 0.5}
        )
```

## 🔌 MCP Server Integration

### MCP Server Architecture

The MCP (Model Context Protocol) integration provides a standardized way to extend the system with external tools and services.

#### 1. Server Registration

```python
# src/mcp/servers/registry.py
class MCPServerRegistry:
    \"\"\"Registry for MCP servers and tools\"\"\"
    
    def __init__(self):
        self.servers: Dict[str, BaseMCPServer] = {}
        self.tools: Dict[str, BaseMCPTool] = {}
    
    async def register_server(self, server: BaseMCPServer):
        \"\"\"Register an MCP server\"\"\"
        self.servers[server.name] = server
        
        # Register all tools provided by the server
        tools = await server.register_tools()
        for tool in tools:
            self.tools[tool.name] = tool
```

#### 2. Creating a New MCP Server

```python
# src/mcp/servers/your_server.py
from src.mcp.base.server import BaseMCPServer
from src.tools.your_tool import YourMCPTool

class YourMCPServer(BaseMCPServer):
    \"\"\"Custom MCP server providing [functionality]\"\"\"
    
    def __init__(self):
        super().__init__(
            name="your_server",
            version="1.0.0",
            description="Server providing [functionality]"
        )
    
    async def register_tools(self) -> List[BaseMCPTool]:
        \"\"\"Register tools provided by this server\"\"\"
        return [
            YourMCPTool(),
            # Add more tools here
        ]
    
    async def initialize(self):
        \"\"\"Initialize server resources\"\"\"
        # Server initialization logic
        pass
    
    async def cleanup(self):
        \"\"\"Cleanup server resources\"\"\"
        # Cleanup logic
        pass
```

#### 3. Tool Discovery and Usage

```python
# Agents can discover and use MCP tools
class EnhancedAgent(BaseAgent):
    
    async def _process_message(self, message: str, session_id: str, context: dict):
        # Discover available tools
        available_tools = await self.mcp_registry.get_tools_for_capability("web_search")
        
        # Use tool if available
        if available_tools:
            tool = available_tools[0]
            result = await tool.execute(MCPToolRequest(
                parameters={"query": "search term"}
            ))
            # Process tool result
```

## 📊 Observability with LangSmith

### LangSmith Integration Architecture

```python
# src/observability/langsmith.py
class LangSmithObserver:
    \"\"\"LangSmith integration for observability\"\"\"
    
    def __init__(self, api_key: str, project_name: str):
        self.client = LangSmithClient(api_key=api_key)
        self.project_name = project_name
    
    async def trace_agent_interaction(self, agent_id: str, message: str, response: str):
        \"\"\"Trace agent interactions\"\"\"
        # Create trace for agent interaction
        pass
    
    async def trace_model_call(self, provider: str, model: str, input_data: dict, output_data: dict):
        \"\"\"Trace model API calls\"\"\"
        # Create trace for model calls
        pass
```

### Adding Observability to Agents

```python
# Enhanced base agent with observability
class ObservableAgent(BaseAgent):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.observer = get_langsmith_observer()
    
    async def process_message(self, message: str, session_id: str, context: dict):
        # Start trace
        trace_id = await self.observer.start_trace(
            name=f"agent_{self.agent_id}",
            inputs={"message": message, "context": context}
        )
        
        try:
            # Process message
            response = await super().process_message(message, session_id, context)
            
            # End trace with success
            await self.observer.end_trace(trace_id, outputs={"response": response})
            return response
            
        except Exception as e:
            # End trace with error
            await self.observer.end_trace(trace_id, error=str(e))
            raise
```

## 📝 Best Practices

### 1. Naming Conventions
- Use generic, descriptive names (avoid business-specific terms)
- Classes: `PascalCase` (e.g., `BaseAgent`, `ModelProvider`)
- Functions/Methods: `snake_case` (e.g., `process_message`, `get_capabilities`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_ATTEMPTS`)
- Files/Modules: `snake_case` (e.g., `agent_registry.py`, `model_manager.py`)

### 2. Code Organization
- Each module should have a single responsibility
- Use dependency injection for external dependencies
- Implement proper error handling and logging
- Include comprehensive docstrings and type hints

### 3. Configuration Management
```python
# Use environment-specific configuration
class AgentConfig(BaseSettings):
    agent_timeout: int = Field(default=30, description="Agent timeout in seconds")
    max_concurrent_agents: int = Field(default=10, description="Maximum concurrent agents")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AGENT_"
    )
```

### 4. Error Handling
```python
# Use custom exceptions with proper error context
class AgentProcessingError(BaseException):
    def __init__(self, agent_id: str, message: str, original_error: Exception = None):
        self.agent_id = agent_id
        self.message = message
        self.original_error = original_error
        super().__init__(f"Agent {agent_id}: {message}")
```

### 5. Testing Strategy
- Unit tests for individual components
- Integration tests for service interactions
- End-to-end tests for complete workflows
- Mock external dependencies (LLM APIs, databases)

### 6. Documentation Requirements
- All public methods must have docstrings
- Include examples in docstrings
- Maintain up-to-date README files
- Document configuration options
- Provide architectural decision records (ADRs) for major changes

This architecture provides a solid foundation for building scalable, observable, and maintainable multi-agent systems with proper separation of concerns and extensibility points.