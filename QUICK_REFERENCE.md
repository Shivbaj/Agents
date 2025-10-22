# Multi-Agent System - Quick API Reference

## 🚀 Essential Endpoints (TESTED & WORKING)

### 📊 System Health & Status
```bash
# Main health check
curl http://localhost:8000/health

# Response: {"status":"healthy","version":"v1","environment":"docker"}
```

### 🔌 MCP (Model Context Protocol) Endpoints

#### List All MCP Servers
```bash
curl http://localhost:8000/api/v1/mcp/servers | jq

# Response: Shows available MCP servers with tools count
```

#### List All MCP Tools  
```bash
curl http://localhost:8000/api/v1/mcp/tools | jq

# Response: Shows all available tools across servers with parameters
```

#### MCP System Health
```bash
curl http://localhost:8000/api/v1/mcp/health | jq

# Response: Health status of all MCP servers
```

#### Execute MCP Tool
```bash
curl -X POST http://localhost:8000/api/v1/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "web_search",
    "arguments": {
      "query": "Python programming tutorials",
      "max_results": 3
    }
  }' | jq

# Response: Tool execution result with success/error status
```

#### Get Server-Specific Tools
```bash
curl http://localhost:8000/api/v1/mcp/servers/web_search_server/tools | jq

# Response: Tools available on specific server
```

### 🤖 Agent Management Endpoints

#### List All Agents
```bash
curl http://localhost:8000/api/v1/agents/list | jq

# Response: All registered agents with metadata
```

#### Discover Agents by Query
```bash
curl "http://localhost:8000/api/v1/agents/discover?query=summarization&limit=5" | jq

# Response: Agents suitable for the query
```

#### Get Agent Details
```bash
curl http://localhost:8000/api/v1/agents/general_assistant | jq

# Response: Detailed agent information
```

#### Get Agent Statistics
```bash
curl http://localhost:8000/api/v1/agents/stats | jq

# Response: System-wide agent statistics
```

#### Get Agent Card
```bash
curl http://localhost:8000/api/v1/agents/dummy_agent/card | jq

# Response: Agent card with capabilities and performance
```

#### Chat with Agent
```bash
curl -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello! Can you help me?",
    "agent_id": "dummy_agent",
    "session_id": "test_session_123"
  }' | jq

# Response: Agent response with metadata
```

#### Streaming Chat
```bash
curl -X POST http://localhost:8000/api/v1/agents/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Write a long explanation about AI",
    "agent_id": "dummy_agent",
    "stream": true
  }' --no-buffer

# Response: Streaming response chunks
```

#### Register New Agent
```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "custom_agent",
    "name": "Custom Test Agent",
    "description": "A custom agent for testing",
    "capabilities": ["testing", "validation"]
  }' | jq

# Response: Registered agent details
```

#### Reload Agent
```bash
curl -X POST http://localhost:8000/api/v1/agents/dummy_agent/reload | jq

# Response: Agent reload status
```

### 🤖 Model Management Endpoints

#### List Available Models
```bash
curl http://localhost:8000/api/v1/models/list | jq

# Response: All available models across providers
```

#### List Model Providers
```bash
curl http://localhost:8000/api/v1/models/providers | jq

# Response: Available model providers (OpenAI, Ollama, etc.)
```

#### Test Model Generation
```bash
curl -X POST http://localhost:8000/api/v1/models/test \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "ollama",
    "model": "phi3:mini",
    "prompt": "What is artificial intelligence?"
  }' | jq

# Response: Model test result
```

### 🐙 Direct Ollama Testing
```bash
# Check Ollama models
curl http://localhost:11434/api/tags | jq

# Test Ollama generation
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3:mini",
    "prompt": "What is AI?",
    "stream": false
  }' | jq

# Response: Direct Ollama model response
```

## 🔧 Docker Commands

```bash
# Start all services
docker-compose up -d

# Rebuild and start
docker-compose up -d --build

# Check container status
docker-compose ps

# View application logs
docker-compose logs -f app

# View all logs
docker-compose logs

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart app

# Execute command in container
docker-compose exec app bash
```

## 🌐 Web Interfaces

- **🔗 API Documentation**: http://localhost:8000/docs (Interactive Swagger UI)
- **❤️ Health Check**: http://localhost:8000/health  
- **🦙 Ollama API**: http://localhost:11434
- **📊 Redis**: redis://localhost:6379

## ⚡ One-Liner System Tests

```bash
# Complete system validation
curl -s http://localhost:8000/health && \
curl -s http://localhost:8000/api/v1/mcp/servers | jq -r '.[].name' && \
curl -s http://localhost:8000/api/v1/mcp/tools | jq -r '.total' && \
curl -s http://localhost:11434/api/tags | jq -r '.models[].name'

# Test MCP tool execution
curl -s -X POST http://localhost:8000/api/v1/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name":"web_search","arguments":{"query":"test","max_results":1}}' | \
  jq '.success'

# Test agent interaction (if agents are loaded)
curl -s -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello!","agent_id":"dummy_agent"}' | \
  jq '.response // .error'

# Test full pipeline health
echo "Testing Multi-Agent System..." && \
curl -s http://localhost:8000/health | jq '.status' && \
curl -s http://localhost:8000/api/v1/mcp/health | jq '.overall_status' && \
curl -s http://localhost:11434/api/tags | jq '.models | length' && \
echo "System test complete!"
```

## 🧪 Dummy Agent Test Commands

```bash
# Test dummy agent capabilities
curl -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"help","agent_id":"dummy_agent"}' | jq '.response'

# Test echo functionality
curl -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"echo Hello World!","agent_id":"dummy_agent"}' | jq '.response'

# Test status reporting
curl -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"status","agent_id":"dummy_agent"}' | jq '.response'

# Get a random fact
curl -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"fact","agent_id":"dummy_agent"}' | jq '.response'

# Get a joke
curl -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"joke","agent_id":"dummy_agent"}' | jq '.response'
```

## 🚨 Troubleshooting Commands

```bash
# Check if services are running
docker-compose ps

# Check container logs for errors
docker-compose logs app | grep -i error

# Test Redis connection
docker-compose exec redis redis-cli ping

# Test Ollama connection and models
curl -s http://localhost:11434/api/tags | jq '.models[].name'

# Check app container health
curl -s http://localhost:8000/health

# Monitor resource usage
docker stats --no-stream

# Restart everything
docker-compose down && docker-compose up -d --build
```

## 📋 Quick Status Check

```bash
# Run this for a complete system overview
echo "=== Multi-Agent System Status ===" && \
echo "App Health: $(curl -s http://localhost:8000/health | jq -r '.status')" && \
echo "MCP Status: $(curl -s http://localhost:8000/api/v1/mcp/health | jq -r '.overall_status')" && \
echo "MCP Servers: $(curl -s http://localhost:8000/api/v1/mcp/servers | jq -r 'length')" && \
echo "MCP Tools: $(curl -s http://localhost:8000/api/v1/mcp/tools | jq -r '.total')" && \
echo "Ollama Models: $(curl -s http://localhost:11434/api/tags | jq -r '.models | length')" && \
echo "Agents: $(curl -s http://localhost:8000/api/v1/agents/list | jq -r '.total')" && \
echo "================================"
```