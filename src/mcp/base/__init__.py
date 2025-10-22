"""
MCP base classes and interfaces

This module provides the core base classes for implementing MCP tools and servers.
"""

from .tool import (
    BaseMCPTool,
    BaseMCPServer,
    MCPToolRequest,
    MCPToolResponse,
    MCPServerInfo,
    MCPToolExecutionError,
    MCPServerError
)

__all__ = [
    "BaseMCPTool",
    "BaseMCPServer", 
    "MCPToolRequest",
    "MCPToolResponse",
    "MCPServerInfo",
    "MCPToolExecutionError",
    "MCPServerError"
]