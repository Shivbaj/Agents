# Multi-Agent System - Quick API Reference

## 🚀 Essential Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### List Agents
```bash
curl http://localhost:8000/api/v1/agents/list
```

### Chat with Agent
```bash
curl -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "agent_id": "general_assistant"
  }'
```

### Test Ollama Model
```bash
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi3:mini",
    "prompt": "What is AI?",
    "stream": false
  }'
```

### Streaming Chat
```bash
curl -X POST http://localhost:8000/api/v1/agents/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain multi-agent systems",
    "agent_id": "general_assistant"
  }' --no-buffer
```

### System Status
```bash
curl http://localhost:8000/api/v1/health/ | jq
```

## 🔧 Docker Commands

```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs app

# Stop services
docker-compose down
```

## 🌐 Web Interfaces

- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health
- **Ollama**: http://localhost:11434

## ⚡ One-Liner Tests

```bash
# Complete system test
curl -s http://localhost:8000/health && \
curl -s http://localhost:8000/api/v1/agents/list && \
curl -s http://localhost:11434/api/tags | jq '.models[].name'

# Quick chat test
curl -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello!","agent_id":"general_assistant"}' | jq '.response'
```