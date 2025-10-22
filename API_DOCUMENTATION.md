# Multi-Agent System API Documentation

## 🚀 Overview

This document provides comprehensive API documentation for the Multi-Agent System, including all available endpoints, request/response formats, and practical curl examples.

**Base URL:** `http://localhost:8000`  
**API Version:** v1  
**Environment:** Docker with CPU-only Ollama phi3:mini model

## 📋 Table of Contents

1. [System Health & Status](#system-health--status)
2. [Agent Registry Management](#agent-registry-management)
3. [Chat & Conversation APIs](#chat--conversation-apis)
4. [Model Management](#model-management)
5. [MCP Server Integration](#mcp-server-integration)
6. [Direct Ollama Integration](#direct-ollama-integration)
7. [Authentication & Headers](#authentication--headers)
8. [Error Handling](#error-handling)

---

## 🏥 System Health & Status

### Basic Health Check
```bash
curl -X GET "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "healthy",
  "version": "v1",
  "environment": "docker"
}
```

### Detailed Health Check
```bash
curl -X GET "http://localhost:8000/api/v1/health/"
```

**Response:**
```json
{
  "status": "healthy",
  "version": "v1",
  "timestamp": "2025-10-22T14:43:01.786909",
  "components": {
    "database": {
      "status": "healthy",
      "response_time": 0.011,
      "details": "Database connection successful"
    },
    "redis": {
      "status": "healthy",
      "response_time": 0.007,
      "details": "Redis connection successful"
    },
    "ollama": {
      "status": "healthy",
      "response_time": 0.023,
      "models_loaded": 1,
      "details": "Ollama service is running"
    },
    "model_providers": {
      "status": "checked",
      "providers": {
        "openai": {
          "status": "configured",
          "api_key": "present"
        },
        "anthropic": {
          "status": "configured",
          "api_key": "present"
        },
        "ollama": {
          "status": "configured",
          "base_url": "http://ollama:11434"
        }
      }
    }
  }
}
```

### Liveness Probe
```bash
curl -X GET "http://localhost:8000/api/v1/health/live"
```

### Readiness Probe
```bash
curl -X GET "http://localhost:8000/api/v1/health/ready"
```

---

## 🤖 Agent Registry Management

### List All Agents
```bash
curl -X GET "http://localhost:8000/api/v1/agents/list"
```

**Response:**
```json
{
  "agents": [
    {
      "id": "general_assistant",
      "name": "General Assistant",
      "description": "A versatile AI assistant for general tasks",
      "capabilities": ["chat", "reasoning", "tool_use"],
      "status": "active",
      "version": "1.0.0"
    }
  ],
  "total": 1
}
```

### Discover Agents by Query
```bash
curl -X GET "http://localhost:8000/api/v1/agents/discover?query=assistant"
```

**Response:**
```json
{
  "query": "assistant",
  "agents": [
    {
      "id": "general_assistant",
      "name": "General Assistant",
      "relevance_score": 0.95,
      "match_reasons": ["name_match", "capability_match"]
    }
  ],
  "total": 1
}
```

### Get Specific Agent Details
```bash
curl -X GET "http://localhost:8000/api/v1/agents/general_assistant"
```

**Response:**
```json
{
  "id": "general_assistant",
  "name": "General Assistant",
  "description": "A versatile AI assistant for general tasks",
  "capabilities": ["chat", "reasoning", "tool_use"],
  "status": "active",
  "version": "1.0.0",
  "configuration": {
    "model_provider": "openai",
    "default_model": "gpt-4",
    "max_tokens": 4000,
    "temperature": 0.7
  },
  "tools": ["web_search", "file_operations"],
  "created_at": "2025-10-22T10:00:00Z",
  "last_updated": "2025-10-22T14:00:00Z"
}
```

### Reload Agent
```bash
curl -X POST "http://localhost:8000/api/v1/agents/general_assistant/reload"
```

**Response:**
```json
{
  "message": "Agent reloaded successfully",
  "agent_id": "general_assistant",
  "status": "active",
  "reload_timestamp": "2025-10-22T14:45:00Z"
}
```

---

## 💬 Chat & Conversation APIs

### Standard Chat
```bash
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, can you help me understand multi-agent systems?",
    "agent_id": "general_assistant",
    "conversation_id": "conv-123",
    "model_override": "phi3:mini",
    "provider_override": "ollama",
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 1000
    }
  }'
```

**Response:**
```json
{
  "response": "Hello! I'd be happy to help you understand multi-agent systems...",
  "conversation_id": "conv-123",
  "message_id": "msg-456",
  "agent_id": "general_assistant",
  "model_used": "phi3:mini",
  "provider_used": "ollama",
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 150,
    "total_tokens": 175
  },
  "tools_used": [],
  "timestamp": "2025-10-22T14:45:00Z"
}
```

### Streaming Chat
```bash
curl -X POST "http://localhost:8000/api/v1/agents/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain the architecture of this multi-agent system",
    "agent_id": "general_assistant",
    "conversation_id": "conv-123"
  }' \
  --no-buffer
```

**Response (Server-Sent Events):**
```
data: {"type": "start", "conversation_id": "conv-123"}

data: {"type": "token", "content": "This", "delta": "This"}

data: {"type": "token", "content": " multi-agent", "delta": " multi-agent"}

data: {"type": "end", "usage": {"total_tokens": 200}}
```

### Multimodal Chat (Vision)
```bash
curl -X POST "http://localhost:8000/api/v1/agents/multimodal" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Describe what you see in this image",
    "agent_id": "vision_agent",
    "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAAA...",
    "image_type": "jpeg",
    "conversation_id": "conv-vision-1"
  }'
```

**Response:**
```json
{
  "response": "I can see a diagram showing a multi-agent system architecture...",
  "conversation_id": "conv-vision-1",
  "agent_id": "vision_agent",
  "image_analysis": {
    "detected_objects": ["diagram", "text", "arrows"],
    "confidence": 0.92
  },
  "usage": {
    "image_tokens": 1000,
    "text_tokens": 150
  }
}
```

### Chat with Tool Usage
```bash
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Search for the latest information about AI agents and summarize it",
    "agent_id": "general_assistant",
    "use_tools": true,
    "tool_config": {
      "web_search": {
        "max_results": 5,
        "include_snippets": true
      }
    }
  }'
```

**Response:**
```json
{
  "response": "Based on my search, here are the latest developments in AI agents...",
  "tools_used": [
    {
      "tool_name": "web_search",
      "query": "AI agents 2025 latest developments",
      "results_count": 5,
      "execution_time": 2.3
    }
  ],
  "sources": [
    {"url": "https://example.com/ai-agents", "title": "Latest AI Agent Research"}
  ]
}
```

---

## 🔧 Model Management

### List Model Providers
```bash
curl -X GET "http://localhost:8000/api/v1/models/providers"
```

**Response:**
```json
{
  "providers": [
    {
      "name": "openai",
      "status": "configured",
      "models": ["gpt-4", "gpt-3.5-turbo"],
      "capabilities": ["chat", "completion", "embedding"]
    },
    {
      "name": "anthropic", 
      "status": "configured",
      "models": ["claude-3-sonnet", "claude-3-haiku"],
      "capabilities": ["chat", "completion"]
    },
    {
      "name": "ollama",
      "status": "running",
      "models": ["phi3:mini"],
      "capabilities": ["chat", "completion", "embedding"]
    }
  ],
  "total": 3
}
```

### List All Models
```bash
curl -X GET "http://localhost:8000/api/v1/models/list"
```

**Response:**
```json
{
  "models": [
    {
      "provider": "ollama",
      "name": "phi3:mini",
      "size": "2.2GB",
      "status": "loaded",
      "capabilities": ["chat", "completion"],
      "parameters": "3.8B",
      "quantization": "Q4_0"
    }
  ],
  "total": 1
}
```

### Test Model
```bash
curl -X POST "http://localhost:8000/api/v1/models/test" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "ollama",
    "model": "phi3:mini",
    "prompt": "What is artificial intelligence?",
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 100
    }
  }'
```

**Response:**
```json
{
  "provider": "ollama",
  "model": "phi3:mini",
  "response": "Artificial intelligence (AI) is a branch of computer science...",
  "usage": {
    "prompt_tokens": 8,
    "completion_tokens": 95,
    "total_tokens": 103
  },
  "latency": 1.25,
  "status": "success"
}
```

### Load Model
```bash
curl -X POST "http://localhost:8000/api/v1/models/ollama/phi3:mini/load"
```

### Unload Model
```bash
curl -X POST "http://localhost:8000/api/v1/models/ollama/phi3:mini/unload"
```

### Get Model Information
```bash
curl -X GET "http://localhost:8000/api/v1/models/ollama/phi3:mini"
```

---

## 🔌 MCP Server Integration

The system includes Model Context Protocol (MCP) servers for extended functionality.

### Available MCP Tools
The web_search_server provides these tools:
- `web_search`: Search the web for information
- `url_fetch`: Fetch content from specific URLs

### Using MCP Tools via Chat
```bash
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Use web search to find information about Docker containers and then summarize the benefits",
    "agent_id": "general_assistant",
    "use_tools": true,
    "mcp_tools": ["web_search"]
  }'
```

### MCP Server Status
Check MCP server status through the health endpoint:
```bash
curl -X GET "http://localhost:8000/api/v1/health/" | jq '.components.mcp_servers'
```

---

## 🦙 Direct Ollama Integration

### List Ollama Models
```bash
curl -X GET "http://localhost:11434/api/tags"
```

**Response:**
```json
{
  "models": [
    {
      "name": "phi3:mini",
      "model": "phi3:mini", 
      "modified_at": "2025-10-22T14:33:05.931154002Z",
      "size": 2176178913,
      "digest": "4f222292793889a9a40a020799cfd28d53f3e01af25d48e06c5e708610fc47e9",
      "details": {
        "parent_model": "",
        "format": "gguf",
        "family": "phi3",
        "parameter_size": "3.8B",
        "quantization_level": "Q4_0"
      }
    }
  ]
}
```

### Generate with Ollama
```bash
curl -X POST "http://localhost:11434/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3:mini",
    "prompt": "Explain the benefits of using multi-agent systems in software development",
    "stream": false,
    "options": {
      "temperature": 0.7,
      "num_predict": 500
    }
  }'
```

### Chat with Ollama
```bash
curl -X POST "http://localhost:11434/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3:mini",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful AI assistant specialized in software architecture."
      },
      {
        "role": "user", 
        "content": "What are the key components of a multi-agent system?"
      }
    ],
    "stream": false
  }'
```

### Streaming Generation
```bash
curl -X POST "http://localhost:11434/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3:mini",
    "prompt": "Write a detailed explanation of agent orchestration",
    "stream": true
  }' \
  --no-buffer
```

### Check Ollama Model Information
```bash
curl -X POST "http://localhost:11434/api/show" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3:mini"
  }'
```

---

## 🔐 Authentication & Headers

### Required Headers
```bash
# All API requests should include:
-H "Content-Type: application/json"
-H "Accept: application/json"

# Optional headers:
-H "X-Request-ID: unique-request-id"
-H "User-Agent: YourApp/1.0"
```

### API Key Configuration
If using external providers (OpenAI, Anthropic), ensure environment variables are set:
```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

---

## ❌ Error Handling

### Standard Error Response Format
```json
{
  "error": {
    "code": "AGENT_NOT_FOUND",
    "message": "The specified agent 'unknown_agent' was not found",
    "details": {
      "agent_id": "unknown_agent",
      "available_agents": ["general_assistant", "vision_agent"]
    },
    "timestamp": "2025-10-22T14:45:00Z"
  }
}
```

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `404` - Not Found (agent/model not found)
- `422` - Unprocessable Entity (invalid parameters)
- `500` - Internal Server Error
- `503` - Service Unavailable (external service down)

### Example Error Scenarios

#### Agent Not Found
```bash
curl -X GET "http://localhost:8000/api/v1/agents/nonexistent"
# Returns 404 with agent suggestions
```

#### Invalid Request Format
```bash
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{"invalid": "request"}'
# Returns 422 with validation details
```

#### Model Unavailable
```bash
curl -X POST "http://localhost:8000/api/v1/models/test" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "ollama",
    "model": "nonexistent:model"
  }'
# Returns 404 with available models
```

---

## 🧪 Testing & Validation

### Complete System Test Script
```bash
#!/bin/bash

echo "🧪 Testing Multi-Agent System API..."

# Health Check
echo "1. Health Check"
curl -s "http://localhost:8000/health" | jq .

# List Agents
echo "2. Agent Registry"
curl -s "http://localhost:8000/api/v1/agents/list" | jq .

# Test Chat
echo "3. Chat Test"
curl -s -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, world!",
    "agent_id": "general_assistant"
  }' | jq .

# Model Test
echo "4. Model Test"
curl -s "http://localhost:8000/api/v1/models/providers" | jq .

# Ollama Test
echo "5. Ollama Test"
curl -s "http://localhost:11434/api/tags" | jq .

echo "✅ All tests completed!"
```

---

## 📊 Monitoring & Metrics

### Performance Metrics
All API responses include timing information:
```json
{
  "response": "...",
  "metadata": {
    "response_time": 1.25,
    "processing_time": 0.95,
    "queue_time": 0.30
  }
}
```

### Usage Statistics
```bash
# Get system usage stats
curl -X GET "http://localhost:8000/api/v1/health/" | jq '.components'
```

---

## 🚀 Quick Start Examples

### Basic Agent Interaction
```bash
# Start a conversation
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello! Can you help me understand how this multi-agent system works?",
    "agent_id": "general_assistant",
    "conversation_id": "demo-conversation"
  }'
```

### Agent Discovery and Testing
```bash
# Discover available agents
curl -X GET "http://localhost:8000/api/v1/agents/discover?query=assistant"

# Test with different models
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain multi-agent coordination",
    "agent_id": "general_assistant",
    "provider_override": "ollama",
    "model_override": "phi3:mini"
  }'
```

### Tool-Enhanced Conversations
```bash
# Use web search through agent
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Search for recent developments in AI agents and provide a summary",
    "agent_id": "general_assistant",
    "use_tools": true
  }'
```

---

## 📝 Notes

- **Base URL**: Update `localhost:8000` to your deployment URL
- **Ollama Port**: Direct Ollama access available on port `11434`
- **Redis Port**: Redis available on port `6379` for debugging
- **Model Loading**: phi3:mini model loads automatically on startup
- **Docker**: All services run in Docker containers with health checks
- **Logs**: Check `docker-compose logs app` for application logs

This API provides a complete foundation for building sophisticated multi-agent applications with support for multiple LLM providers, conversation management, tool integration, and comprehensive monitoring.