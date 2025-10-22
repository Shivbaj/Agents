"""
Base classes for MCP (Model Context Protocol) integration

This module provides the foundation for implementing MCP servers and tools
that can be used by agents to extend their capabilities dynamically.

The MCP protocol allows agents to:
- Discover available tools and resources
- Execute tools with parameters
- Access external data sources
- Integrate with third-party services

Example:
    ```python
    from src.mcp.base.tool import BaseMCPTool
    
    class WebSearchTool(BaseMCPTool):
        def __init__(self):
            super().__init__(
                name="web_search",
                description="Search the web for information",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            )
        
        async def execute(self, parameters: dict) -> dict:
            # Implement web search logic
            return {"results": [...]}
    ```
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from loguru import logger


@dataclass
class MCPToolRequest:
    """Request for MCP tool execution"""
    tool_name: str
    parameters: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


@dataclass 
class MCPToolResponse:
    """Response from MCP tool execution"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None


@dataclass
class MCPServerInfo:
    """Information about an MCP server"""
    name: str
    version: str
    description: str
    capabilities: List[str]
    tools: List[str]
    status: str = "active"


class BaseMCPTool(ABC):
    """
    Base class for MCP tools
    
    MCP tools are reusable components that can be executed by agents
    to perform specific tasks or access external resources.
    
    Attributes:
        name: Unique tool identifier
        description: Human-readable tool description
        parameters_schema: JSON schema for tool parameters
        capabilities: List of capabilities this tool provides
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters_schema: Dict[str, Any],
        capabilities: Optional[List[str]] = None
    ):
        self.name = name
        self.description = description
        self.parameters_schema = parameters_schema
        self.capabilities = capabilities or []
        self.created_at = datetime.now()
        self.execution_count = 0
        self.total_execution_time = 0.0
    
    @abstractmethod
    async def execute(self, request: MCPToolRequest) -> MCPToolResponse:
        """
        Execute the tool with given parameters
        
        Args:
            request: Tool execution request with parameters and context
            
        Returns:
            MCPToolResponse with execution results
            
        Raises:
            MCPToolExecutionError: If tool execution fails
        """
        pass
    
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate tool parameters against schema
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic validation - can be enhanced with jsonschema
            required_params = self.parameters_schema.get("required", [])
            for param in required_params:
                if param not in parameters:
                    return False
            return True
        except Exception as e:
            logger.error(f"Parameter validation failed for {self.name}: {str(e)}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get tool information for discovery"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters_schema": self.parameters_schema,
            "capabilities": self.capabilities,
            "execution_count": self.execution_count,
            "average_execution_time": (
                self.total_execution_time / self.execution_count
                if self.execution_count > 0 else 0
            )
        }
    
    async def _update_metrics(self, execution_time: float):
        """Update tool execution metrics"""
        self.execution_count += 1
        self.total_execution_time += execution_time


class BaseMCPServer(ABC):
    """
    Base class for MCP servers
    
    MCP servers provide collections of tools and resources that can be
    used by agents. Servers handle tool registration, discovery, and execution.
    
    Attributes:
        name: Unique server identifier
        version: Server version
        description: Human-readable server description
        tools: Dictionary of tools provided by this server
    """
    
    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        capabilities: Optional[List[str]] = None
    ):
        self.name = name
        self.version = version
        self.description = description
        self.capabilities = capabilities or []
        self.tools: Dict[str, BaseMCPTool] = {}
        self.is_initialized = False
        self.created_at = datetime.now()
    
    @abstractmethod
    async def initialize(self):
        """Initialize the server and register tools"""
        pass
    
    @abstractmethod
    async def register_tools(self) -> List[BaseMCPTool]:
        """
        Register tools provided by this server
        
        Returns:
            List of MCP tools provided by this server
        """
        pass
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> MCPToolResponse:
        """
        Execute a tool provided by this server
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            context: Optional execution context
            
        Returns:
            MCPToolResponse with execution results
        """
        if tool_name not in self.tools:
            return MCPToolResponse(
                success=False,
                error=f"Tool '{tool_name}' not found in server '{self.name}'"
            )
        
        tool = self.tools[tool_name]
        
        # Validate parameters
        if not await tool.validate_parameters(parameters):
            return MCPToolResponse(
                success=False,
                error=f"Invalid parameters for tool '{tool_name}'"
            )
        
        # Execute tool
        request = MCPToolRequest(
            tool_name=tool_name,
            parameters=parameters,
            context=context
        )
        
        try:
            start_time = datetime.now()
            response = await tool.execute(request)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Update metrics
            await tool._update_metrics(execution_time)
            
            # Add execution time to response
            if response.metadata is None:
                response.metadata = {}
            response.metadata["execution_time"] = execution_time
            response.metadata["server_name"] = self.name
            
            return response
            
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} in server {self.name}: {str(e)}")
            return MCPToolResponse(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )
    
    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool"""
        if tool_name in self.tools:
            return self.tools[tool_name].get_info()
        return None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all tools provided by this server"""
        return [tool.get_info() for tool in self.tools.values()]
    
    def get_server_info(self) -> MCPServerInfo:
        """Get server information"""
        return MCPServerInfo(
            name=self.name,
            version=self.version,
            description=self.description,
            capabilities=self.capabilities,
            tools=list(self.tools.keys()),
            status="active" if self.is_initialized else "inactive"
        )
    
    async def cleanup(self):
        """Cleanup server resources"""
        logger.info(f"Cleaning up MCP server: {self.name}")
        self.tools.clear()
        self.is_initialized = False


class MCPToolExecutionError(Exception):
    """Exception raised when MCP tool execution fails"""
    
    def __init__(self, tool_name: str, message: str, original_error: Optional[Exception] = None):
        self.tool_name = tool_name
        self.original_error = original_error
        super().__init__(f"Tool '{tool_name}' execution failed: {message}")


class MCPServerError(Exception):
    """Exception raised for MCP server errors"""
    
    def __init__(self, server_name: str, message: str, original_error: Optional[Exception] = None):
        self.server_name = server_name
        self.original_error = original_error
        super().__init__(f"MCP server '{server_name}' error: {message}")