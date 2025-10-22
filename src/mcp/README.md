# MCP (Model Context Protocol) Integration

This directory contains the MCP (Model Context Protocol) framework implementation for the multi-agent system. The MCP framework allows agents to dynamically discover and use tools provided by external servers.

## Directory Structure

```
src/mcp/
├── base/
│   └── tool.py           # Base classes for MCP servers and tools
├── servers/              # MCP server implementations
│   └── web_search.py     # Example web search server
├── manager.py           # MCP server and tool manager
└── README.md           # This file
```

## Architecture Overview

### Core Components

1. **BaseMCPTool**: Abstract base class for creating MCP tools
2. **BaseMCPServer**: Abstract base class for creating MCP servers
3. **MCPManager**: Central manager for server registration and tool routing
4. **MCPToolRequest/Response**: Data structures for tool communication

### Key Concepts

- **MCP Server**: A service that provides a collection of related tools
- **MCP Tool**: A specific capability that can be executed by agents
- **Tool Discovery**: Automatic registration and discovery of available tools
- **Tool Routing**: Directing tool execution requests to the appropriate server

## Creating Custom MCP Tools

### 1. Basic Tool Implementation

```python
from src.mcp.base.tool import BaseMCPTool, MCPToolRequest, MCPToolResponse

class CalculatorTool(BaseMCPTool):
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Perform basic mathematical calculations",
            parameters_schema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            },
            capabilities=["math", "calculation"]
        )
    
    async def execute(self, request: MCPToolRequest) -> MCPToolResponse:
        try:
            expression = request.parameters.get("expression")
            # Safe evaluation logic here
            result = eval(expression)  # Note: Use safe evaluation in production
            
            return MCPToolResponse(
                success=True,
                result={"expression": expression, "result": result}
            )
        except Exception as e:
            return MCPToolResponse(
                success=False,
                error=f"Calculation failed: {str(e)}"
            )
```

### 2. Parameter Validation

Tools automatically validate parameters against their schema. For custom validation:

```python
async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
    # Call parent validation first
    if not await super().validate_parameters(parameters):
        return False
    
    # Add custom validation
    expression = parameters.get("expression", "")
    if not expression or len(expression) > 100:
        return False
    
    return True
```

## Creating MCP Servers

### 1. Basic Server Implementation

```python
from src.mcp.base.tool import BaseMCPServer, BaseMCPTool

class MathServer(BaseMCPServer):
    def __init__(self):
        super().__init__(
            name="math_server",
            version="1.0.0",
            description="Provides mathematical calculation tools",
            capabilities=["math", "statistics", "geometry"]
        )
    
    async def initialize(self):
        """Initialize server resources"""
        if self.is_initialized:
            return
        
        # Perform initialization tasks
        # e.g., load configurations, validate API keys, etc.
        
        self.is_initialized = True
        print(f"{self.name} initialized successfully")
    
    async def register_tools(self) -> List[BaseMCPTool]:
        """Register tools provided by this server"""
        return [
            CalculatorTool(),
            StatisticsTool(),
            GeometryTool()
        ]
```

### 2. Server Registration

```python
from src.mcp.manager import get_mcp_manager

async def setup_servers():
    manager = get_mcp_manager()
    await manager.initialize()
    
    # Register your server
    math_server = MathServer()
    await manager.register_server(math_server)
    
    # Register other servers
    web_server = WebSearchServer()
    await manager.register_server(web_server)
```

## Using MCP Tools in Agents

### 1. Tool Discovery

```python
from src.mcp.manager import get_mcp_manager

async def discover_tools():
    manager = get_mcp_manager()
    
    # Get all available tools
    tools = await manager.get_available_tools()
    
    # Get specific tool info
    tool_info = await manager.get_tool_info("calculator")
    
    return tools, tool_info
```

### 2. Tool Execution

```python
async def execute_calculation(expression: str):
    manager = get_mcp_manager()
    
    response = await manager.execute_tool(
        "calculator",
        {"expression": expression}
    )
    
    if response.success:
        return response.result
    else:
        print(f"Calculation failed: {response.error}")
        return None
```

### 3. Agent Integration

```python
class MathAgent:
    def __init__(self):
        self.mcp_manager = get_mcp_manager()
    
    async def solve_problem(self, problem: str) -> str:
        # Analyze problem and determine needed tools
        if "calculate" in problem.lower():
            # Extract expression from problem
            expression = self.extract_expression(problem)
            
            # Use MCP tool
            response = await self.mcp_manager.execute_tool(
                "calculator",
                {"expression": expression}
            )
            
            if response.success:
                return f"The result is: {response.result['result']}"
            else:
                return f"Calculation failed: {response.error}"
        
        return "I don't know how to solve this problem"
```

## Advanced Features

### 1. Tool Chaining

```python
async def research_and_summarize(topic: str):
    manager = get_mcp_manager()
    
    # Step 1: Search for information
    search_response = await manager.execute_tool(
        "web_search",
        {"query": topic, "max_results": 5}
    )
    
    if not search_response.success:
        return "Search failed"
    
    # Step 2: Extract content from top results
    results = []
    for result in search_response.result["results"][:3]:
        extract_response = await manager.execute_tool(
            "url_extract",
            {"url": result["url"]}
        )
        
        if extract_response.success:
            results.append(extract_response.result)
    
    # Step 3: Summarize (if summarization tool exists)
    summary_response = await manager.execute_tool(
        "summarize",
        {"texts": [r["content"] for r in results]}
    )
    
    return summary_response.result if summary_response.success else results
```

### 2. Context Passing

```python
async def contextual_search(query: str, user_preferences: dict):
    context = {
        "user_id": user_preferences.get("user_id"),
        "language": user_preferences.get("language", "en"),
        "safe_search": user_preferences.get("safe_search", True)
    }
    
    response = await manager.execute_tool(
        "web_search",
        {"query": query},
        context=context
    )
    
    return response
```

### 3. Error Handling and Retry Logic

```python
async def robust_tool_execution(tool_name: str, parameters: dict, max_retries: int = 3):
    manager = get_mcp_manager()
    
    for attempt in range(max_retries):
        try:
            response = await manager.execute_tool(tool_name, parameters)
            
            if response.success:
                return response
            
            # Log error and retry
            print(f"Attempt {attempt + 1} failed: {response.error}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        except Exception as e:
            print(f"Attempt {attempt + 1} exception: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
    
    return MCPToolResponse(success=False, error="All retry attempts failed")
```

## Server Health Monitoring

### 1. Health Checks

```python
async def monitor_mcp_health():
    manager = get_mcp_manager()
    
    health = await manager.health_check()
    
    print(f"Manager Status: {health['manager_status']}")
    print(f"Total Servers: {health['total_servers']}")
    print(f"Total Tools: {health['total_tools']}")
    
    for server_name, server_health in health["servers"].items():
        print(f"Server {server_name}: {server_health['status']}")
```

### 2. Metrics Collection

```python
async def collect_tool_metrics():
    manager = get_mcp_manager()
    
    tools = await manager.get_available_tools()
    
    for tool in tools:
        print(f"Tool: {tool['name']}")
        print(f"  Executions: {tool['execution_count']}")
        print(f"  Avg Time: {tool['average_execution_time']:.3f}s")
```

## Best Practices

### 1. Tool Design

- **Single Responsibility**: Each tool should have one clear purpose
- **Parameter Validation**: Always validate input parameters
- **Error Handling**: Provide clear, actionable error messages
- **Documentation**: Include comprehensive parameter schemas and descriptions

### 2. Server Design

- **Logical Grouping**: Group related tools into servers
- **Resource Management**: Properly initialize and cleanup resources
- **Health Monitoring**: Implement health check capabilities
- **Version Management**: Use semantic versioning for servers

### 3. Integration

- **Async Operations**: Use async/await for all MCP operations
- **Context Passing**: Utilize context for user preferences and session state
- **Tool Discovery**: Dynamically discover available tools rather than hardcoding
- **Graceful Degradation**: Handle tool unavailability gracefully

### 4. Security

- **Input Sanitization**: Sanitize all tool parameters
- **Access Control**: Implement appropriate access controls if needed
- **Rate Limiting**: Consider rate limiting for expensive operations
- **Audit Logging**: Log tool executions for security and debugging

## Future Enhancements

The MCP framework is designed to be extensible. Future enhancements may include:

- **Tool Composition**: Automatically chain tools to accomplish complex tasks
- **Adaptive Routing**: Route requests to the best available tool instance
- **Caching**: Cache tool results for improved performance
- **Authentication**: Add authentication and authorization for tools
- **Distributed Servers**: Support for remote MCP servers
- **Tool Marketplace**: Registry for discovering and installing new tools

For more examples and advanced usage patterns, see the server implementations in the `servers/` directory.