"""
MCP Tools API endpoints
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger

from src.api.v1.schemas import MCPToolsResponse, MCPServerResponse, MCPToolExecuteRequest, MCPToolExecuteResponse
from src.mcp.manager import get_mcp_manager, MCPManager

router = APIRouter()


def get_mcp_manager_dependency(request: Request) -> MCPManager:
    """Get MCP manager from app state"""
    if hasattr(request.app.state, 'mcp_manager'):
        return request.app.state.mcp_manager
    else:
        # Fallback to singleton
        return get_mcp_manager()


@router.get("/servers", response_model=List[MCPServerResponse])
async def list_mcp_servers(
    mcp_manager: MCPManager = Depends(get_mcp_manager_dependency)
):
    """
    List all registered MCP servers
    
    Returns information about all registered MCP servers including
    their status, capabilities, and available tools.
    
    Example usage:
    ```bash
    curl http://localhost:8000/api/v1/mcp/servers
    ```
    """
    try:
        servers_info = await mcp_manager.get_servers_info()
        return [
            MCPServerResponse(
                server_id=info["server_id"],
                name=info["name"], 
                description=info.get("description", ""),
                status=info.get("status", "unknown"),
                tools_count=len(info.get("tools", [])),
                tools=list(info.get("tools", {}).keys())
            )
            for info in servers_info.values()
        ]
    except Exception as e:
        logger.error(f"Failed to list MCP servers: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list MCP servers")


@router.get("/tools", response_model=MCPToolsResponse)
async def list_mcp_tools(
    server_id: Optional[str] = None,
    mcp_manager: MCPManager = Depends(get_mcp_manager_dependency)
):
    """
    List all available MCP tools across all servers
    
    Optionally filter by server_id to get tools from a specific server.
    
    Example usage:
    ```bash
    curl http://localhost:8000/api/v1/mcp/tools
    curl "http://localhost:8000/api/v1/mcp/tools?server_id=web_search_server"
    ```
    """
    try:
        tools_info = await mcp_manager.list_tools()
        
        # Filter by server if specified
        if server_id:
            tools_info = {
                tool_name: tool_info 
                for tool_name, tool_info in tools_info.items()
                if tool_info.get("server_id") == server_id
            }
        
        # Transform to response format
        tools = [
            {
                "tool_name": tool_name,
                "server_id": tool_info.get("server_id", "unknown"),
                "description": tool_info.get("description", ""),
                "parameters": tool_info.get("parameters", {}),
                "availability": tool_info.get("status", "available")
            }
            for tool_name, tool_info in tools_info.items()
        ]
        
        return MCPToolsResponse(
            tools=tools,
            total=len(tools),
            servers_count=len(set(tool["server_id"] for tool in tools))
        )
        
    except Exception as e:
        logger.error(f"Failed to list MCP tools: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list MCP tools")


@router.post("/tools/execute", response_model=MCPToolExecuteResponse)
async def execute_mcp_tool(
    request: MCPToolExecuteRequest,
    mcp_manager: MCPManager = Depends(get_mcp_manager_dependency)
):
    """
    Execute an MCP tool with given parameters
    
    Execute a specific MCP tool by name with the provided arguments.
    
    Example usage:
    ```bash
    curl -X POST http://localhost:8000/api/v1/mcp/tools/execute \
      -H "Content-Type: application/json" \
      -d '{
        "tool_name": "web_search",
        "arguments": {
          "query": "Python programming tutorials",
          "max_results": 5
        }
      }'
    ```
    """
    try:
        result = await mcp_manager.call_tool(request.tool_name, request.arguments)
        
        # Handle MCPToolResponse object
        if hasattr(result, 'success'):
            return MCPToolExecuteResponse(
                tool_name=request.tool_name,
                success=result.success,
                result=result,
                execution_time=getattr(result, 'execution_time', None),
                metadata={
                    "timestamp": getattr(result.metadata, 'get', lambda x: None)("timestamp") if result.metadata else None,
                    "server_id": await mcp_manager.get_tool_server(request.tool_name)
                }
            )
        else:
            # Handle dict result (backward compatibility)
            return MCPToolExecuteResponse(
                tool_name=request.tool_name,
                success=True,
                result=result,
                execution_time=getattr(result, 'execution_time', None),
                metadata={
                    "timestamp": result.get("timestamp") if isinstance(result, dict) else None,
                    "server_id": await mcp_manager.get_tool_server(request.tool_name)
                }
            )
        
    except Exception as e:
        logger.error(f"Failed to execute MCP tool '{request.tool_name}': {str(e)}")
        return MCPToolExecuteResponse(
            tool_name=request.tool_name,
            success=False,
            error=str(e),
            result=None
        )


@router.get("/health")
async def mcp_health_check(
    mcp_manager: MCPManager = Depends(get_mcp_manager_dependency)
):
    """
    Check health of all MCP servers
    
    Returns health status of all registered MCP servers.
    
    Example usage:
    ```bash
    curl http://localhost:8000/api/v1/mcp/health
    ```
    """
    try:
        servers_info = await mcp_manager.get_servers_info()
        
        health_status = {}
        for server_id, info in servers_info.items():
            try:
                # Try to get tools to test server health
                tools = await mcp_manager.get_server_tools(server_id)
                health_status[server_id] = {
                    "status": "healthy",
                    "tools_count": len(tools),
                    "last_checked": info.get("last_health_check")
                }
            except Exception as e:
                health_status[server_id] = {
                    "status": "unhealthy", 
                    "error": str(e),
                    "tools_count": 0
                }
        
        overall_healthy = all(
            server["status"] == "healthy" 
            for server in health_status.values()
        )
        
        return {
            "overall_status": "healthy" if overall_healthy else "degraded",
            "servers": health_status,
            "total_servers": len(health_status),
            "healthy_servers": sum(1 for s in health_status.values() if s["status"] == "healthy")
        }
        
    except Exception as e:
        logger.error(f"MCP health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="MCP health check failed")


@router.get("/servers/{server_id}/tools")
async def get_server_tools(
    server_id: str,
    mcp_manager: MCPManager = Depends(get_mcp_manager_dependency)
):
    """
    Get all tools for a specific MCP server
    
    Example usage:
    ```bash
    curl http://localhost:8000/api/v1/mcp/servers/web_search_server/tools
    ```
    """
    try:
        tools = await mcp_manager.get_server_tools(server_id)
        return {
            "server_id": server_id,
            "tools": tools,
            "tools_count": len(tools)
        }
    except Exception as e:
        logger.error(f"Failed to get tools for server '{server_id}': {str(e)}")
        raise HTTPException(status_code=404, detail=f"Server '{server_id}' not found or error getting tools")