"""
MCP (Model Context Protocol) integration module

This module provides the complete MCP framework for the multi-agent system,
including base classes, server implementations, and management utilities.
"""

from .manager import MCPManager, get_mcp_manager, initialize_mcp_manager
from .base.tool import (
    BaseMCPTool,
    BaseMCPServer, 
    MCPToolRequest,
    MCPToolResponse,
    MCPServerInfo,
    MCPToolExecutionError,
    MCPServerError
)

__all__ = [
    "MCPManager",
    "get_mcp_manager", 
    "initialize_mcp_manager",
    "BaseMCPTool",
    "BaseMCPServer",
    "MCPToolRequest", 
    "MCPToolResponse",
    "MCPServerInfo",
    "MCPToolExecutionError",
    "MCPServerError"
]