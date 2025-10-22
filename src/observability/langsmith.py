"""
LangSmith Observability Integration

This module provides comprehensive observability and monitoring capabilities
using LangSmith for the multi-agent system. It includes tracing, metrics
collection, logging, and performance monitoring.

LangSmith provides:
- Distributed tracing for agent conversations
- Performance metrics and analytics
- Error tracking and debugging
- A/B testing capabilities
- Real-time monitoring dashboards

Usage:
    ```python
    from src.observability.langsmith import LangSmithTracer
    
    # Initialize tracer
    tracer = LangSmithTracer()
    
    # Trace agent execution
    with tracer.trace_agent("research_agent") as trace:
        result = await agent.process_request(request)
        trace.add_metadata({"model": "gpt-4", "tokens": 150})
        trace.log_result(result)
    ```
"""
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
import json
import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from enum import Enum

try:
    # LangSmith SDK - install with: pip install langsmith
    from langsmith import Client
    from langsmith.schemas import Run, RunType
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    Client = None
    Run = None
    RunType = None


class TraceLevel(Enum):
    """Trace level enumeration"""
    DEBUG = "debug"
    INFO = "info" 
    WARNING = "warning"
    ERROR = "error"


@dataclass
class AgentTrace:
    """Agent execution trace data"""
    trace_id: str
    agent_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    status: str = "running"
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    parent_trace_id: Optional[str] = None
    child_traces: Optional[List[str]] = None


@dataclass
class ToolTrace:
    """Tool execution trace data"""
    trace_id: str
    tool_name: str
    server_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    status: str = "running"
    parameters: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    parent_trace_id: Optional[str] = None


class MockLangSmithClient:
    """Mock client for when LangSmith is not available"""
    
    def __init__(self, api_key: str = None):
        self.traces = []
        print("Using mock LangSmith client - install 'langsmith' package for full functionality")
    
    def create_run(self, **kwargs) -> str:
        """Mock run creation"""
        run_id = str(uuid.uuid4())
        self.traces.append({"id": run_id, **kwargs})
        return run_id
    
    def update_run(self, run_id: str, **kwargs):
        """Mock run update"""
        for trace in self.traces:
            if trace["id"] == run_id:
                trace.update(kwargs)
                break
    
    def end_run(self, run_id: str, **kwargs):
        """Mock run end"""
        self.update_run(run_id, end_time=datetime.now(timezone.utc), **kwargs)


class LangSmithTracer:
    """
    LangSmith-based tracer for multi-agent system observability
    
    Provides comprehensive tracing, metrics, and monitoring capabilities
    for agent executions, tool usage, and system performance.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        project_name: str = "multi-agent-system",
        environment: str = "development"
    ):
        self.api_key = api_key
        self.project_name = project_name
        self.environment = environment
        
        # Initialize client
        if LANGSMITH_AVAILABLE and api_key:
            self.client = Client(api_key=api_key)
        else:
            self.client = MockLangSmithClient(api_key)
        
        # Active traces tracking
        self.active_traces: Dict[str, AgentTrace] = {}
        self.active_tool_traces: Dict[str, ToolTrace] = {}
        
        # Metrics
        self.metrics = {
            "total_agent_executions": 0,
            "total_tool_executions": 0,
            "avg_agent_duration": 0.0,
            "avg_tool_duration": 0.0,
            "error_count": 0,
            "success_count": 0
        }
    
    def generate_trace_id(self) -> str:
        """Generate unique trace ID"""
        return str(uuid.uuid4())
    
    @asynccontextmanager
    async def trace_agent(
        self,
        agent_name: str,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_trace_id: Optional[str] = None
    ):
        """
        Context manager for tracing agent execution
        
        Args:
            agent_name: Name of the agent being traced
            input_data: Input data for the agent
            metadata: Additional metadata for the trace
            parent_trace_id: ID of parent trace if this is a child execution
        
        Usage:
            ```python
            async with tracer.trace_agent("research_agent", {"query": "Python"}) as trace:
                result = await agent.process_query("Python tutorials")
                trace.add_metadata({"model": "gpt-4", "tokens": 150})
                trace.log_result(result)
            ```
        """
        trace_id = self.generate_trace_id()
        start_time = datetime.now(timezone.utc)
        
        # Create trace object
        trace = AgentTrace(
            trace_id=trace_id,
            agent_name=agent_name,
            start_time=start_time,
            input_data=input_data,
            metadata=metadata or {},
            parent_trace_id=parent_trace_id,
            child_traces=[]
        )
        
        # Create LangSmith run
        run_id = self.client.create_run(
            name=f"agent_{agent_name}",
            run_type="chain" if LANGSMITH_AVAILABLE else "agent",
            inputs=input_data or {},
            project_name=self.project_name,
            tags=[agent_name, self.environment],
            extra=metadata or {}
        )
        
        trace.metadata["langsmith_run_id"] = run_id
        self.active_traces[trace_id] = trace
        
        # Create trace context
        trace_context = AgentTraceContext(self, trace)
        
        try:
            yield trace_context
            
            # Mark as successful if no errors
            trace.status = "completed"
            self.metrics["success_count"] += 1
            
        except Exception as e:
            trace.status = "error"
            trace.error = str(e)
            self.metrics["error_count"] += 1
            
            # Update LangSmith run with error
            self.client.update_run(
                run_id,
                error=str(e),
                status="error"
            )
            raise
            
        finally:
            # Finalize trace
            end_time = datetime.now(timezone.utc)
            trace.end_time = end_time
            trace.duration = (end_time - start_time).total_seconds()
            
            # Update metrics
            self.metrics["total_agent_executions"] += 1
            self._update_avg_duration("agent", trace.duration)
            
            # End LangSmith run
            self.client.end_run(
                run_id,
                outputs=trace.output_data or {},
                end_time=end_time
            )
            
            # Remove from active traces
            self.active_traces.pop(trace_id, None)
            
            print(f"Agent trace completed: {agent_name} ({trace.duration:.3f}s)")
    
    @asynccontextmanager
    async def trace_tool(
        self,
        tool_name: str,
        server_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        parent_trace_id: Optional[str] = None
    ):
        """
        Context manager for tracing tool execution
        
        Args:
            tool_name: Name of the tool being executed
            server_name: Name of the MCP server providing the tool
            parameters: Tool parameters
            parent_trace_id: ID of parent agent trace
        """
        trace_id = self.generate_trace_id()
        start_time = datetime.now(timezone.utc)
        
        # Create tool trace
        trace = ToolTrace(
            trace_id=trace_id,
            tool_name=tool_name,
            server_name=server_name,
            start_time=start_time,
            parameters=parameters,
            parent_trace_id=parent_trace_id
        )
        
        # Create LangSmith run
        run_id = self.client.create_run(
            name=f"tool_{tool_name}",
            run_type="tool" if LANGSMITH_AVAILABLE else "function",
            inputs=parameters or {},
            project_name=self.project_name,
            tags=[tool_name, server_name, "mcp_tool"],
            parent_run_id=self._get_langsmith_parent_id(parent_trace_id)
        )
        
        self.active_tool_traces[trace_id] = trace
        
        # Create trace context
        trace_context = ToolTraceContext(self, trace)
        
        try:
            yield trace_context
            
            trace.status = "completed"
            
        except Exception as e:
            trace.status = "error"
            trace.error = str(e)
            
            self.client.update_run(run_id, error=str(e), status="error")
            raise
            
        finally:
            end_time = datetime.now(timezone.utc)
            trace.end_time = end_time
            trace.duration = (end_time - start_time).total_seconds()
            
            # Update metrics
            self.metrics["total_tool_executions"] += 1
            self._update_avg_duration("tool", trace.duration)
            
            # End LangSmith run
            self.client.end_run(
                run_id,
                outputs=trace.result or {},
                end_time=end_time
            )
            
            self.active_tool_traces.pop(trace_id, None)
    
    def _get_langsmith_parent_id(self, parent_trace_id: Optional[str]) -> Optional[str]:
        """Get LangSmith run ID for parent trace"""
        if not parent_trace_id:
            return None
        
        if parent_trace_id in self.active_traces:
            return self.active_traces[parent_trace_id].metadata.get("langsmith_run_id")
        
        return None
    
    def _update_avg_duration(self, trace_type: str, duration: float):
        """Update average duration metrics"""
        if trace_type == "agent":
            count = self.metrics["total_agent_executions"]
            current_avg = self.metrics["avg_agent_duration"]
            self.metrics["avg_agent_duration"] = (current_avg * (count - 1) + duration) / count
        elif trace_type == "tool":
            count = self.metrics["total_tool_executions"]
            current_avg = self.metrics["avg_tool_duration"]
            self.metrics["avg_tool_duration"] = (current_avg * (count - 1) + duration) / count
    
    async def log_event(
        self,
        event_name: str,
        data: Dict[str, Any],
        level: TraceLevel = TraceLevel.INFO,
        trace_id: Optional[str] = None
    ):
        """Log a custom event"""
        event_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_name": event_name,
            "level": level.value,
            "data": data,
            "trace_id": trace_id
        }
        
        print(f"Event [{level.value.upper()}]: {event_name} - {json.dumps(data, indent=2)}")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            **self.metrics,
            "active_agent_traces": len(self.active_traces),
            "active_tool_traces": len(self.active_tool_traces),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def export_traces(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Export traces for a given time period"""
        # In a real implementation, this would query LangSmith API
        # For now, return mock data structure
        return [
            {
                "trace_id": "example-trace-id",
                "agent_name": "research_agent",
                "start_time": start_date.isoformat(),
                "end_time": end_date.isoformat(),
                "duration": 2.5,
                "status": "completed",
                "tools_used": ["web_search", "url_extract"]
            }
        ]


class AgentTraceContext:
    """Context object for agent trace management"""
    
    def __init__(self, tracer: LangSmithTracer, trace: AgentTrace):
        self.tracer = tracer
        self.trace = trace
    
    def add_metadata(self, metadata: Dict[str, Any]):
        """Add metadata to the trace"""
        if self.trace.metadata is None:
            self.trace.metadata = {}
        self.trace.metadata.update(metadata)
    
    def log_result(self, result: Any):
        """Log execution result"""
        self.trace.output_data = {"result": result}
    
    def log_error(self, error: str):
        """Log execution error"""
        self.trace.error = error
        self.trace.status = "error"
    
    def add_child_trace(self, child_trace_id: str):
        """Add child trace ID"""
        if self.trace.child_traces is None:
            self.trace.child_traces = []
        self.trace.child_traces.append(child_trace_id)


class ToolTraceContext:
    """Context object for tool trace management"""
    
    def __init__(self, tracer: LangSmithTracer, trace: ToolTrace):
        self.tracer = tracer
        self.trace = trace
    
    def log_result(self, result: Dict[str, Any]):
        """Log tool execution result"""
        self.trace.result = result
    
    def log_error(self, error: str):
        """Log tool execution error"""
        self.trace.error = error
        self.trace.status = "error"


# Global tracer instance
_langsmith_tracer: Optional[LangSmithTracer] = None


def get_tracer() -> LangSmithTracer:
    """Get the global LangSmith tracer instance"""
    global _langsmith_tracer
    if _langsmith_tracer is None:
        _langsmith_tracer = LangSmithTracer()
    return _langsmith_tracer


def initialize_tracer(
    api_key: Optional[str] = None,
    project_name: str = "multi-agent-system",
    environment: str = "development"
) -> LangSmithTracer:
    """Initialize the global LangSmith tracer"""
    global _langsmith_tracer
    _langsmith_tracer = LangSmithTracer(
        api_key=api_key,
        project_name=project_name,
        environment=environment
    )
    return _langsmith_tracer