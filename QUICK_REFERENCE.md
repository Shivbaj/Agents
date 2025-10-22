# Multi-Agent System - Quick API Reference

## � CURRENT SYSTEM STATUS (2025-10-22)

### ✅ **WORKING COMPONENTS**
- **System Health**: `GET /health` ✅
- **MCP Integration**: All endpoints working ✅
  - MCP Servers: 1 active (web_search_server)
  - MCP Tools: 2 available (web_search, url_extract)
  - Tool Execution: Working with some internal errors
- **Ollama Integration**: Fully functional ✅
  - Model: phi3:mini (3.8B parameters, 2.2GB)
  - Direct API: Generation working perfectly
- **Docker Environment**: All containers healthy ✅
- **Redis**: Connected and healthy ✅

### ⚠️ **PARTIALLY WORKING**
- **MCP Tool Execution**: API works but tools have internal errors
- **Model Management**: Limited provider registration

### ❌ **NOT WORKING (AGENT LOADING ISSUES)**
- **Agent System**: 0 agents loaded
  - Error: `'NoneType' object is not callable`
  - All agent endpoints return empty or not found errors
- **Agent Registration**: Fails due to initialization errors
- **Agent Chat/Interaction**: No agents available

### 🔧 **ROOT CAUSE**: Agent initialization failure after dependency resolution

---

## 🚀 VERIFIED WORKING ENDPOINTS

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

### 🤖 Agent Management Endpoints ⚠️ (AGENTS NOT LOADING - INITIALIZATION ERROR)

> **Current Issue**: Agents are not loading due to initialization errors: `'NoneType' object is not callable`
> **Status**: Framework is working, but agents fail to initialize
> **Expected Response**: `{"agents": [], "total": 0}` for most endpoints

#### List All Agents ⚠️ (RETURNS EMPTY)
```bash
curl http://localhost:8000/api/v1/agents/list | jq

# Current Response: {"agents": [], "total": 0}
# Issue: Agents not loading due to initialization errors
```

#### Discover Agents by Query ⚠️ (RETURNS EMPTY)
```bash
curl "http://localhost:8000/api/v1/agents/discover?query=summarization&limit=5" | jq

# Current Response: {"query": "summarization", "agents": [], "total": 0}
```

#### Get Agent Details ❌ (FAILS - AGENT NOT FOUND)
```bash
curl http://localhost:8000/api/v1/agents/general_assistant | jq

# Current Response: {"error": "Agent 'general_assistant' not found", "type": "AgentNotFoundException"}
```

#### Get Agent Statistics ❌ (FAILS - WRONG ENDPOINT)
```bash
# NOTE: This endpoint path is incorrect, should be a GET not requiring agent_id
curl http://localhost:8000/api/v1/agents/stats | jq

# Current Response: {"error": "Agent 'stats' not found", "type": "AgentNotFoundException"}
```

#### Get Agent Card ❌ (FAILS - AGENT NOT FOUND)
```bash
curl http://localhost:8000/api/v1/agents/dummy_agent/card | jq

# Current Response: {"error": "Agent 'dummy_agent' not found", "type": "AgentNotFoundException"}
```

#### Chat with Agent ❌ (FAILS - AGENT NOT FOUND)
```bash
curl -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello! Can you help me?",
    "agent_id": "dummy_agent",
    "session_id": "test_session_123"
  }' | jq

# Current Response: {"error": "Agent 'dummy_agent' not found", "type": "AgentNotFoundException"}
```

#### Streaming Chat ❌ (FAILS - AGENT NOT FOUND)
```bash
curl -X POST http://localhost:8000/api/v1/agents/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Write a long explanation about AI",
    "agent_id": "dummy_agent",
    "stream": true
  }' --no-buffer

# Current Response: Agent not found error
```

#### Register New Agent ❌ (FAILS - INITIALIZATION ERROR)
```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "custom_agent",
    "name": "Custom Test Agent",
    "description": "A custom agent for testing",
    "capabilities": ["testing", "validation"]
  }' | jq

# Current Response: {"error": "Failed to register agent: 'NoneType' object is not callable", "type": "HTTPException"}
```

#### Reload Agent ❌ (FAILS - AGENT NOT FOUND)
```bash
curl -X POST http://localhost:8000/api/v1/agents/dummy_agent/reload | jq

# Current Response: {"error": "Agent 'dummy_agent' not found", "type": "AgentNotFoundException"}
```

### 🤖 Model Management Endpoints ⚠️ (LIMITED FUNCTIONALITY)

#### List Available Models ⚠️ (RETURNS EMPTY)
```bash
curl http://localhost:8000/api/v1/models/list | jq

# Current Response: {"models": [], "total": 0}
# Issue: Models not properly registered with the system
```

#### List Model Providers ✅ (WORKING)
```bash
curl http://localhost:8000/api/v1/models/providers | jq

# Current Response: {"providers": ["openai"], "total": 1}
# Note: Only OpenAI provider registered, Ollama provider not showing
```

#### Test Model Generation ❌ (NOT TESTED - LIKELY FAILS)
```bash
curl -X POST http://localhost:8000/api/v1/models/test \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "ollama",
    "model": "phi3:mini",
    "prompt": "What is artificial intelligence?"
  }' | jq

# Status: Not tested due to provider registration issues
```

### 🐙 Direct Ollama Testing ✅ (FULLY WORKING)

```bash
# Check Ollama models ✅
curl http://localhost:11434/api/tags | jq

# Current Response: Shows phi3:mini model (2.2GB) loaded and ready
# {
#   "models": [{
#     "name": "phi3:mini",
#     "size": 2176178913,
#     "parameter_size": "3.8B"
#   }]
# }

# Test Ollama generation ✅
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3:mini",
    "prompt": "What is AI? Answer briefly.",
    "stream": false
  }' | jq -r '.response'

# Current Response: Working! Returns AI explanation
# "Artificial Intelligence (AI) refers to the simulation of human intelligence..."

# Test streaming generation ✅
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3:mini",
    "prompt": "Explain machine learning in one paragraph.",
    "stream": true
  }' --no-buffer

# Response: Streaming chunks from Ollama
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

## ⚡ One-Liner System Tests (UPDATED FOR CURRENT STATUS)

```bash
# 🟢 Complete working system validation
curl -s http://localhost:8000/health && \
curl -s http://localhost:8000/api/v1/mcp/servers | jq -r '.[].name' && \
curl -s http://localhost:8000/api/v1/mcp/tools | jq -r '.total' && \
curl -s http://localhost:11434/api/tags | jq -r '.models[].name'

# Expected Output:
# {"status":"healthy","version":"v1","environment":"docker"}
# web_search_server  
# 2
# phi3:mini

# 🟡 Test MCP tool execution (works but may have internal errors)
curl -s -X POST http://localhost:8000/api/v1/mcp/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name":"web_search","arguments":{"query":"test","max_results":1}}' | \
  jq '.success'

# Expected: true (though tool may have internal errors)

# 🔴 Test agent interaction (WILL FAIL - NO AGENTS LOADED)
curl -s -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello!","agent_id":"dummy_agent"}' | \
  jq '.error'

# Expected: "Agent 'dummy_agent' not found"

# 🟢 Test Ollama direct (FULLY WORKING)
curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"phi3:mini","prompt":"Hello!","stream":false}' | \
  jq -r '.response'

# Expected: AI generated response

# 🟢 Full working components health check
echo "=== WORKING COMPONENTS TEST ===" && \
echo "System: $(curl -s http://localhost:8000/health | jq -r '.status')" && \
echo "MCP Status: $(curl -s http://localhost:8000/api/v1/mcp/health | jq -r '.overall_status')" && \
echo "MCP Tools: $(curl -s http://localhost:8000/api/v1/mcp/tools | jq -r '.total')" && \
echo "Ollama: $(curl -s http://localhost:11434/api/tags | jq -r '.models | length') model(s)" && \
echo "Agents: $(curl -s http://localhost:8000/api/v1/agents/list | jq -r '.total') (EXPECTED: 0)" && \
echo "==============================="
```

## 🧪 Agent Test Commands ❌ (ALL FAIL - NO AGENTS LOADED)

> **Note**: All agent-related commands will fail because agents are not loading due to initialization errors.

```bash
# ❌ These will all return "Agent not found" errors:

curl -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"help","agent_id":"dummy_agent"}' | jq '.error'
# Response: "Agent 'dummy_agent' not found"

curl -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hello","agent_id":"general_assistant"}' | jq '.error'  
# Response: "Agent 'general_assistant' not found"
```

## 🔄 Workaround: Use Direct Ollama Instead

Since agents are not working, you can use Ollama directly for AI interactions:

```bash
# ✅ Working AI chat via Ollama directly
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3:mini",
    "prompt": "Hello! How can I help you today?",
    "stream": false
  }' | jq -r '.response'

# ✅ Ask questions directly
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3:mini", 
    "prompt": "Explain what a multi-agent system is in simple terms.",
    "stream": false
  }' | jq -r '.response'

# ✅ Get help/information
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3:mini",
    "prompt": "List 3 interesting facts about artificial intelligence.",
    "stream": false
  }' | jq -r '.response'
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

---

## 🎯 **CURRENT RECOMMENDATION**

### ✅ **What You Can Use Right Now:**
1. **Direct Ollama AI**: Fully functional for text generation
2. **MCP System**: Server and tool management working
3. **System Health**: All monitoring endpoints operational
4. **Docker Environment**: Stable and healthy

### 🔧 **What Needs Fixing:**
1. **Agent Loading**: `'NoneType' object is not callable` error
2. **Model Provider Registration**: Ollama provider not showing in system
3. **Agent-System Integration**: Complete agent framework not operational

### 📝 **Issue Summary:**
- **Dependencies resolved**: bs4/beautifulsoup4 now installed ✅
- **New issue discovered**: Agent initialization failing during loading
- **Workaround available**: Use Ollama directly for AI functionality ✅
- **System infrastructure**: Healthy and ready for agents when fixed ✅

### 🚀 **Quick AI Test (Working Alternative):**
```bash
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"phi3:mini","prompt":"Your question here","stream":false}' | \
  jq -r '.response'
```