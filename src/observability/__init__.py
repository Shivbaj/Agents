"""
Observability Module Initialization

This module provides comprehensive observability and monitoring capabilities
for the multi-agent system, including:

- LangSmith integration for tracing and analytics
- Metrics collection and aggregation
- Performance monitoring
- Error tracking and alerting
- Real-time dashboards and reporting

Usage:
    ```python
    from src.observability import initialize_observability, get_tracer
    
    # Initialize observability
    await initialize_observability()
    
    # Use tracer in agents
    tracer = get_tracer()
    async with tracer.trace_agent("my_agent") as trace:
        # Agent logic here
        trace.log_result(result)
    ```
"""
from typing import Optional, Dict, Any
import os

from .langsmith import LangSmithTracer, initialize_tracer as init_langsmith_tracer


async def initialize_observability(
    langsmith_api_key: Optional[str] = None,
    project_name: str = "multi-agent-system",
    environment: Optional[str] = None
) -> Dict[str, Any]:
    """
    Initialize the observability stack
    
    Args:
        langsmith_api_key: LangSmith API key (optional, can use env var)
        project_name: Project name for tracing
        environment: Environment name (development, staging, production)
    
    Returns:
        Initialization status and configuration
    """
    # Get configuration from environment if not provided
    if langsmith_api_key is None:
        langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")
    
    # Initialize LangSmith tracer
    tracer = init_langsmith_tracer(
        api_key=langsmith_api_key,
        project_name=project_name,
        environment=environment
    )
    
    print(f"Observability initialized for project: {project_name}")
    print(f"Environment: {environment}")
    print(f"LangSmith: {'Enabled' if langsmith_api_key else 'Mock Mode'}")
    
    return {
        "status": "initialized",
        "project_name": project_name,
        "environment": environment,
        "langsmith_enabled": bool(langsmith_api_key),
        "tracer": tracer
    }


def get_tracer() -> LangSmithTracer:
    """Get the global tracer instance"""
    from .langsmith import get_tracer
    return get_tracer()


# Convenience re-exports
from .langsmith import (
    LangSmithTracer,
    AgentTrace,
    ToolTrace,
    TraceLevel,
    AgentTraceContext,
    ToolTraceContext
)

__all__ = [
    "initialize_observability",
    "get_tracer",
    "LangSmithTracer",
    "AgentTrace", 
    "ToolTrace",
    "TraceLevel",
    "AgentTraceContext",
    "ToolTraceContext"
]