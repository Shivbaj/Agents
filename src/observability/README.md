# Observability and Monitoring

This directory provides comprehensive observability and monitoring capabilities for the multi-agent system using LangSmith integration and other monitoring tools.

## Features

### LangSmith Integration
- **Distributed Tracing**: Complete trace visibility across agent executions
- **Performance Analytics**: Detailed metrics on agent and tool performance  
- **Error Tracking**: Comprehensive error logging and debugging capabilities
- **Real-time Monitoring**: Live dashboards and alerting

### Key Components

1. **LangSmith Tracer** (`langsmith.py`)
   - Agent execution tracing
   - Tool usage monitoring
   - Performance metrics collection
   - Error tracking and reporting

2. **Observability Manager** (`__init__.py`)
   - Centralized initialization
   - Configuration management
   - Easy access to tracing capabilities

## Quick Start

### 1. Installation

```bash
# Install LangSmith SDK (optional - mock client used if not available)
pip install langsmith
```

### 2. Configuration

Set up environment variables:

```bash
export LANGSMITH_API_KEY="your-api-key-here"
export ENVIRONMENT="development"  # or "staging", "production"
```

### 3. Initialize Observability

```python
from src.observability import initialize_observability

# Initialize in your application startup
await initialize_observability(
    project_name="my-agent-system",
    environment="development"
)
```

### 4. Use in Agents

```python
from src.observability import get_tracer

class MyAgent:
    def __init__(self):
        self.tracer = get_tracer()
    
    async def process_request(self, request: str) -> str:
        # Trace the entire agent execution
        async with self.tracer.trace_agent("my_agent", {"request": request}) as trace:
            
            # Add metadata
            trace.add_metadata({
                "model": "gpt-4",
                "temperature": 0.7
            })
            
            # Process request
            result = await self._process(request)
            
            # Log result
            trace.log_result(result)
            
            return result
    
    async def _process(self, request: str) -> str:
        # Trace tool usage
        async with self.tracer.trace_tool("web_search", "search_server", {"query": request}) as tool_trace:
            # Simulate tool execution
            result = {"results": ["example result"]}
            tool_trace.log_result(result)
            return str(result)
```

## Advanced Usage

### Custom Events

```python
from src.observability import get_tracer, TraceLevel

tracer = get_tracer()

# Log custom events
await tracer.log_event(
    "user_interaction",
    {"user_id": "123", "action": "query", "query": "Python tutorials"},
    level=TraceLevel.INFO
)
```

### Metrics Collection

```python
# Get current metrics
metrics = await tracer.get_metrics()
print(f"Total agent executions: {metrics['total_agent_executions']}")
print(f"Average duration: {metrics['avg_agent_duration']:.3f}s")
print(f"Error rate: {metrics['error_count'] / (metrics['success_count'] + metrics['error_count']):.2%}")
```

### Export Traces

```python
from datetime import datetime, timedelta

# Export traces for analysis
start_date = datetime.now() - timedelta(days=1)
end_date = datetime.now()

traces = await tracer.export_traces(start_date, end_date)
```

## Integration with MCP Tools

The observability system automatically integrates with MCP (Model Context Protocol) tools:

```python
from src.mcp.manager import get_mcp_manager
from src.observability import get_tracer

async def execute_with_tracing():
    tracer = get_tracer()
    mcp_manager = get_mcp_manager()
    
    # Agent execution is automatically traced
    async with tracer.trace_agent("research_agent") as agent_trace:
        
        # Tool executions are automatically traced as child spans
        async with tracer.trace_tool("web_search", "web_server") as tool_trace:
            response = await mcp_manager.execute_tool("web_search", {"query": "AI research"})
            tool_trace.log_result(response.result if response.success else {})
            
        agent_trace.log_result({"status": "completed"})
```

## Monitoring and Alerting

### Health Monitoring

```python
async def check_system_health():
    tracer = get_tracer()
    
    # Get comprehensive metrics
    metrics = await tracer.get_metrics()
    
    # Check for issues
    error_rate = metrics['error_count'] / (metrics['success_count'] + metrics['error_count']) if (metrics['success_count'] + metrics['error_count']) > 0 else 0
    
    if error_rate > 0.1:  # 10% error rate threshold
        await tracer.log_event(
            "high_error_rate",
            {"error_rate": error_rate, "threshold": 0.1},
            level=TraceLevel.WARNING
        )
```

### Performance Monitoring

```python
async def monitor_performance():
    tracer = get_tracer()
    metrics = await tracer.get_metrics()
    
    # Check average response times
    if metrics['avg_agent_duration'] > 5.0:  # 5 second threshold
        await tracer.log_event(
            "slow_agent_performance",
            {"avg_duration": metrics['avg_agent_duration'], "threshold": 5.0},
            level=TraceLevel.WARNING
        )
```

## Dashboard and Visualization

When using LangSmith with a valid API key, you can access:

1. **Real-time Dashboards**: View live agent performance and usage
2. **Trace Visualization**: Detailed trace flamegraphs and timelines  
3. **Error Analysis**: Comprehensive error tracking and debugging
4. **Performance Analytics**: Historical performance trends and bottlenecks

Visit the LangSmith dashboard at: https://smith.langchain.com/

## Best Practices

### 1. Trace Naming
- Use descriptive agent names: `research_agent`, `summarization_agent`
- Include version info in metadata: `{"version": "1.2.0"}`
- Use consistent naming conventions

### 2. Metadata Usage
```python
trace.add_metadata({
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000,
    "user_id": "user_123",
    "session_id": "session_456"
})
```

### 3. Error Handling
```python
async with tracer.trace_agent("my_agent") as trace:
    try:
        result = await process_request()
        trace.log_result(result)
    except Exception as e:
        trace.log_error(str(e))
        raise  # Re-raise to maintain error propagation
```

### 4. Performance Optimization
- Avoid tracing very fine-grained operations
- Use sampling for high-volume operations
- Include relevant context in metadata

### 5. Privacy Considerations
- Sanitize sensitive data before logging
- Use trace context for user consent tracking
- Implement data retention policies

## Configuration

### Environment Variables

```bash
# Required for full LangSmith integration
LANGSMITH_API_KEY=your-api-key

# Optional configuration
ENVIRONMENT=development|staging|production
PROJECT_NAME=multi-agent-system
LANGSMITH_PROJECT=custom-project-name
```

### Programmatic Configuration

```python
from src.observability import initialize_observability

config = await initialize_observability(
    langsmith_api_key="your-api-key",
    project_name="custom-project", 
    environment="production"
)
```

## Troubleshooting

### Common Issues

1. **Mock Client Warning**: If you see "Using mock LangSmith client", install the LangSmith package:
   ```bash
   pip install langsmith
   ```

2. **Authentication Errors**: Verify your LANGSMITH_API_KEY is correctly set

3. **Missing Traces**: Ensure `initialize_observability()` is called before using tracers

4. **Performance Impact**: If tracing impacts performance, consider:
   - Using sampling for high-frequency operations
   - Reducing metadata size
   - Implementing async logging

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.getLogger("langsmith").setLevel(logging.DEBUG)
```

## Future Enhancements

- **Distributed Tracing**: Cross-service tracing for distributed agents
- **Custom Metrics**: User-defined performance metrics
- **Anomaly Detection**: Automatic detection of performance anomalies
- **Integration APIs**: REST APIs for external monitoring tools
- **Alert Management**: Configurable alerting rules and notifications

For detailed API documentation and examples, see the source code and inline documentation.