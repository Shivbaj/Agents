"""
MCP Server Manager

This module provides the management layer for MCP (Model Context Protocol) servers.
It handles server registration, discovery, tool routing, and lifecycle management.

The MCP Manager acts as a central registry for all MCP servers and provides
a unified interface for agents to interact with various tools and resources.

Usage:
    ```python
    from src.mcp.manager import MCPManager
    
    # Initialize manager
    manager = MCPManager()
    
    # Register a server
    await manager.register_server(my_server)
    
    # Execute a tool
    response = await manager.execute_tool("web_search", {"query": "Python tutorials"})
    ```
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

from .base.tool import BaseMCPServer, BaseMCPTool, MCPToolResponse, MCPServerInfo, MCPServerError


class MCPManager:
    """
    Central manager for MCP servers and tools
    
    The MCPManager provides:
    - Server registration and lifecycle management
    - Tool discovery and routing
    - Health monitoring and error handling
    - Metrics collection and reporting
    """
    
    def __init__(self):
        self.servers: Dict[str, BaseMCPServer] = {}
        self.tool_registry: Dict[str, str] = {}  # tool_name -> server_name mapping
        self.is_initialized = False
        self.created_at = datetime.now()
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the MCP manager"""
        if self.is_initialized:
            return
        
        print("Initializing MCP Manager...")
        self.is_initialized = True
        print("MCP Manager initialized successfully")
    
    async def register_server(self, server: BaseMCPServer) -> bool:
        """
        Register an MCP server
        
        Args:
            server: MCP server instance to register
            
        Returns:
            True if registration successful, False otherwise
        """
        async with self._lock:
            try:
                if server.name in self.servers:
                    print(f"Server '{server.name}' already registered")
                    return False
                
                # Initialize server
                if not server.is_initialized:
                    await server.initialize()
                
                # Register server
                self.servers[server.name] = server
                
                # Register tools
                tools = await server.register_tools()
                for tool in tools:
                    if tool.name in self.tool_registry:
                        print(f"Tool '{tool.name}' already registered by server '{self.tool_registry[tool.name]}'")
                        continue
                    
                    self.tool_registry[tool.name] = server.name
                    server.tools[tool.name] = tool
                
                print(f"Successfully registered MCP server '{server.name}' with {len(tools)} tools")
                return True
                
            except Exception as e:
                print(f"Failed to register server '{server.name}': {str(e)}")
                return False
    
    async def unregister_server(self, server_name: str) -> bool:
        """
        Unregister an MCP server
        
        Args:
            server_name: Name of server to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        async with self._lock:
            try:
                if server_name not in self.servers:
                    print(f"Server '{server_name}' not found")
                    return False
                
                server = self.servers[server_name]
                
                # Remove tools from registry
                tools_to_remove = [
                    tool_name for tool_name, srv_name in self.tool_registry.items()
                    if srv_name == server_name
                ]
                
                for tool_name in tools_to_remove:
                    del self.tool_registry[tool_name]
                
                # Cleanup server
                await server.cleanup()
                
                # Remove server
                del self.servers[server_name]
                
                print(f"Successfully unregistered server '{server_name}'")
                return True
                
            except Exception as e:
                print(f"Failed to unregister server '{server_name}': {str(e)}")
                return False
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> MCPToolResponse:
        """
        Execute a tool by name
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            context: Optional execution context
            
        Returns:
            MCPToolResponse with execution results
        """
        try:
            if tool_name not in self.tool_registry:
                return MCPToolResponse(
                    success=False,
                    error=f"Tool '{tool_name}' not found"
                )
            
            server_name = self.tool_registry[tool_name]
            
            if server_name not in self.servers:
                return MCPToolResponse(
                    success=False,
                    error=f"Server '{server_name}' for tool '{tool_name}' not available"
                )
            
            server = self.servers[server_name]
            return await server.execute_tool(tool_name, parameters, context)
            
        except Exception as e:
            print(f"Tool execution failed: {tool_name}: {str(e)}")
            return MCPToolResponse(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get information about all available tools
        
        Returns:
            List of tool information dictionaries
        """
        tools = []
        
        for tool_name, server_name in self.tool_registry.items():
            if server_name in self.servers:
                server = self.servers[server_name]
                tool_info = await server.get_tool_info(tool_name)
                if tool_info:
                    tool_info["server_name"] = server_name
                    tools.append(tool_info)
        
        return tools
    
    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific tool
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool information dictionary or None if not found
        """
        if tool_name not in self.tool_registry:
            return None
        
        server_name = self.tool_registry[tool_name]
        if server_name not in self.servers:
            return None
        
        server = self.servers[server_name]
        tool_info = await server.get_tool_info(tool_name)
        
        if tool_info:
            tool_info["server_name"] = server_name
        
        return tool_info
    
    async def get_servers_info(self) -> List[MCPServerInfo]:
        """
        Get information about all registered servers
        
        Returns:
            List of server information objects
        """
        return [server.get_server_info() for server in self.servers.values()]
    
    async def get_server_info(self, server_name: str) -> Optional[MCPServerInfo]:
        """
        Get information about a specific server
        
        Args:
            server_name: Name of the server
            
        Returns:
            Server information object or None if not found
        """
        if server_name in self.servers:
            return self.servers[server_name].get_server_info()
        return None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all servers
        
        Returns:
            Health status dictionary
        """
        health_status = {
            "manager_status": "healthy" if self.is_initialized else "unhealthy",
            "total_servers": len(self.servers),
            "total_tools": len(self.tool_registry),
            "servers": {}
        }
        
        for server_name, server in self.servers.items():
            try:
                server_info = server.get_server_info()
                health_status["servers"][server_name] = {
                    "status": server_info.status,
                    "tools_count": len(server_info.tools),
                    "capabilities": server_info.capabilities
                }
            except Exception as e:
                health_status["servers"][server_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return health_status
    
    async def get_servers_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered servers"""
        servers_info = {}
        
        for server_name, server in self.servers.items():
            try:
                tools = await server.get_tools() if hasattr(server, 'get_tools') else server.tools
                servers_info[server_name] = {
                    "server_id": server_name,
                    "name": getattr(server, 'name', server_name),
                    "description": getattr(server, 'description', ''),
                    "status": "active" if server.is_initialized else "inactive",
                    "tools": tools,
                    "last_health_check": datetime.now().isoformat()
                }
            except Exception as e:
                servers_info[server_name] = {
                    "server_id": server_name,
                    "name": server_name,
                    "description": "",
                    "status": "error",
                    "tools": {},
                    "error": str(e)
                }
        
        return servers_info
    
    async def get_server_tools(self, server_id: str) -> Dict[str, Any]:
        """Get tools for a specific server"""
        if server_id not in self.servers:
            raise ValueError(f"Server '{server_id}' not found")
        
        server = self.servers[server_id]
        if hasattr(server, 'get_tools'):
            return await server.get_tools()
        else:
            return server.tools
    
    async def get_tool_server(self, tool_name: str) -> Optional[str]:
        """Get the server ID that provides a specific tool"""
        return self.tool_registry.get(tool_name)

    async def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """List all available tools across all servers"""
        all_tools = {}
        
        for server_id, server in self.servers.items():
            try:
                # Get tools from server
                if hasattr(server, 'get_tools'):
                    tools = await server.get_tools()
                else:
                    tools = getattr(server, 'tools', {})
                
                # Add server info to each tool
                for tool_name, tool_info in tools.items():
                    if isinstance(tool_info, dict):
                        all_tools[tool_name] = {
                            **tool_info,
                            "server_id": server_id,
                            "status": "available"
                        }
                    else:
                        # Handle case where tool_info is not a dict
                        all_tools[tool_name] = {
                            "description": getattr(tool_info, 'description', f'Tool from {server_id}'),
                            "server_id": server_id,
                            "status": "available",
                            "parameters": getattr(tool_info, 'parameters_schema', {})
                        }
            except Exception as e:
                # Add error info for tools from failed servers
                print(f"Error getting tools from server {server_id}: {e}")
        
        return all_tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name with given arguments"""
        # Find which server provides this tool
        server_id = self.tool_registry.get(tool_name)
        if not server_id:
            raise ValueError(f"Tool '{tool_name}' not found in any registered server")
        
        # Get the server
        server = self.servers.get(server_id)
        if not server:
            raise ValueError(f"Server '{server_id}' not found")
        
        # Call the tool on the server
        try:
            if hasattr(server, 'call_tool'):
                result = await server.call_tool(tool_name, arguments)
            else:
                # Fallback: try to get tool directly and execute
                tools = await server.get_tools() if hasattr(server, 'get_tools') else getattr(server, 'tools', {})
                if tool_name not in tools:
                    raise ValueError(f"Tool '{tool_name}' not found in server '{server_id}'")
                
                tool = tools[tool_name]
                if hasattr(tool, 'execute'):
                    result = await tool.execute(arguments)
                else:
                    raise ValueError(f"Tool '{tool_name}' does not have execute method")
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Error executing tool '{tool_name}': {str(e)}")

    async def cleanup(self):
        """Cleanup all resources"""
        print("Cleaning up MCP Manager...")
        
        # Cleanup all servers
        for server_name in list(self.servers.keys()):
            await self.unregister_server(server_name)
        
        self.tool_registry.clear()
        self.is_initialized = False
        print("MCP Manager cleanup completed")
    
    @asynccontextmanager
    async def lifespan(self):
        """Async context manager for MCP manager lifecycle"""
        await self.initialize()
        try:
            yield self
        finally:
            await self.cleanup()


# Global MCP manager instance
_mcp_manager: Optional[MCPManager] = None


def get_mcp_manager() -> MCPManager:
    """Get the global MCP manager instance"""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPManager()
    return _mcp_manager


async def initialize_mcp_manager() -> MCPManager:
    """Initialize and return the global MCP manager"""
    manager = get_mcp_manager()
    if not manager.is_initialized:
        await manager.initialize()
    return manager