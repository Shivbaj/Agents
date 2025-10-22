#  API Usage Examples

This document provides comprehensive examples of using the Multi-Agent System API.

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, the API doesn't require authentication. In production, implement proper authentication mechanisms.

---

##  Agent Discovery & Management

### Discover Agents by Query
Find the most suitable agents for your task:

```bash
# Find agents for summarization
curl -X GET "http://localhost:8000/api/v1/agents/discover?query=summarize%20document&limit=3"

# Find agents for image analysis
curl -X GET "http://localhost:8000/api/v1/agents/discover?query=analyze%20image&limit=5"

# Find all text processing agents
curl -X GET "http://localhost:8000/api/v1/agents/discover?query=text%20processing"
```

**Response:**
```json
{
  "query": "summarize document",
  "agents": [
    {
      "id": "summarizer_agent",
      "name": "Document Summarizer",
      "description": "Specializes in summarizing documents, articles, and text content",
      "agent_type": "text",
      "capabilities": ["document_summarization", "key_points_extraction"],
      "model_provider": "openai",
      "model_name": "gpt-4-turbo-preview",
      "status": "active",
      "relevance_score": 15
    }
  ],
  "total": 1
}
```

### List All Agents
```bash
# List all agents
curl -X GET "http://localhost:8000/api/v1/agents/list"

# Filter by agent type
curl -X GET "http://localhost:8000/api/v1/agents/list?agent_type=vision"

# Filter by status
curl -X GET "http://localhost:8000/api/v1/agents/list?status=active"
```

### Get Agent Details
```bash
curl -X GET "http://localhost:8000/api/v1/agents/summarizer_agent"
```

---

##  Chat with Agents

### Basic Chat
```bash
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain quantum computing in simple terms",
    "agent_id": "general_assistant",
    "session_id": "learning_session_001"
  }'
```

### Advanced Chat with Context
```bash
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Summarize this research paper: [Your long text here...]",
    "agent_id": "summarizer_agent",
    "session_id": "research_session_001",
    "context": {
      "summary_length": 200,
      "summary_style": "academic",
      "document_type": "research_paper"
    }
  }'
```

### Streaming Chat
```bash
curl -X POST "http://localhost:8000/api/v1/agents/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Write a detailed explanation of machine learning",
    "agent_id": "general_assistant",
    "session_id": "streaming_session_001",
    "stream": true,
    "context": {
      "response_style": "detailed",
      "personality": "educational"
    }
  }'
```

---

##  Multimodal Interactions

### Image Analysis
```bash
curl -X POST "http://localhost:8000/api/v1/agents/multimodal" \
  -F "message=Describe this image in detail" \
  -F "agent_id=vision_agent" \
  -F "session_id=vision_session_001" \
  -F "files=@/path/to/your/image.jpg"
```

### Multiple Files
```bash
curl -X POST "http://localhost:8000/api/v1/agents/multimodal" \
  -F "message=Compare these two images" \
  -F "agent_id=vision_agent" \
  -F "session_id=comparison_session" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg"
```

### Document + Image Analysis
```bash
curl -X POST "http://localhost:8000/api/v1/agents/multimodal" \
  -F "message=Analyze this chart and extract the data" \
  -F "agent_id=vision_agent" \
  -F "session_id=data_extraction" \
  -F "files=@chart.png"
```

---

##  Model Management

### List Available Models
```bash
# All models
curl -X GET "http://localhost:8000/api/v1/models/list"

# Filter by provider
curl -X GET "http://localhost:8000/api/v1/models/list?provider=openai"

# Filter by type
curl -X GET "http://localhost:8000/api/v1/models/list?model_type=vision"

# Multiple filters
curl -X GET "http://localhost:8000/api/v1/models/list?provider=anthropic&model_type=text"
```

### Test Model
```bash
curl -X POST "http://localhost:8000/api/v1/models/test" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "model_name": "gpt-3.5-turbo",
    "test_message": "Hello, how are you?"
  }'
```

### Load/Unload Ollama Models
```bash
# Load a model
curl -X POST "http://localhost:8000/api/v1/models/ollama/llama3.2:1b/load"

# Unload a model
curl -X DELETE "http://localhost:8000/api/v1/models/ollama/llama3.2:1b/unload"
```

---

##  Health Checks

### Basic Health Check
```bash
curl -X GET "http://localhost:8000/health"
```

### Comprehensive Health Check
```bash
curl -X GET "http://localhost:8000/api/v1/health/"
```

### Readiness Check (for K8s)
```bash
curl -X GET "http://localhost:8000/api/v1/health/ready"
```

---

##  Real-World Examples

### Document Summarization Workflow
```bash
# 1. Discover summarization agents
curl -X GET "http://localhost:8000/api/v1/agents/discover?query=document%20summary"

# 2. Summarize a long document
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Please summarize this research paper: [Long academic text here...]",
    "agent_id": "summarizer_agent",
    "session_id": "research_workflow_001",
    "context": {
      "summary_length": 300,
      "summary_style": "executive",
      "document_type": "academic"
    }
  }'

# 3. Ask follow-up questions in the same session
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the key findings mentioned in the summary?",
    "agent_id": "summarizer_agent",
    "session_id": "research_workflow_001"
  }'
```

### Image Analysis Workflow
```bash
# 1. Upload and analyze an image
curl -X POST "http://localhost:8000/api/v1/agents/multimodal" \
  -F "message=What objects do you see in this image?" \
  -F "agent_id=vision_agent" \
  -F "session_id=image_analysis_001" \
  -F "files=@product_photo.jpg"

# 2. Ask specific questions about the same image
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you identify the brand visible in the image?",
    "agent_id": "vision_agent",
    "session_id": "image_analysis_001"
  }'
```

### Creative Writing Workflow
```bash
# 1. Start creative writing session
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Write a short story about AI agents collaborating to solve climate change",
    "agent_id": "general_assistant",
    "session_id": "creative_writing_001",
    "context": {
      "personality": "creative",
      "response_style": "detailed"
    }
  }'

# 2. Continue the story
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Continue the story and add more detail about the different types of AI agents",
    "agent_id": "general_assistant",
    "session_id": "creative_writing_001"
  }'
```

---

## Advanced Usage

### Session Management
Sessions allow you to maintain context across multiple interactions:

```bash
# Start a session
SESSION_ID="analysis_$(date +%s)"

# First message
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"I need help analyzing market data\",
    \"agent_id\": \"general_assistant\",
    \"session_id\": \"$SESSION_ID\"
  }"

# Follow-up messages maintain context
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Focus on the technology sector specifically\",
    \"agent_id\": \"general_assistant\",
    \"session_id\": \"$SESSION_ID\"
  }"
```

### Error Handling
```bash
# Handle agent not found
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello",
    "agent_id": "nonexistent_agent",
    "session_id": "test"
  }' \
  -w "HTTP Status: %{http_code}\n"

# Handle invalid requests
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "invalid": "request"
  }' \
  -w "HTTP Status: %{http_code}\n"
```

---

##  Response Formats

### Successful Chat Response
```json
{
  "response": "Here's my helpful response to your question...",
  "agent_id": "general_assistant",
  "session_id": "my_session_123",
  "metadata": {
    "processing_time": 1.234,
    "model_used": "openai/gpt-4-turbo-preview",
    "message_length": 25,
    "response_length": 150,
    "task_type": "question_answering"
  }
}
```

### Error Response
```json
{
  "error": "Agent 'nonexistent_agent' not found",
  "details": {},
  "type": "AgentNotFoundException",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## Testing & Development

### Test All Endpoints
```bash
# Health check
curl -f http://localhost:8000/health || echo "Health check failed"

# List agents
curl -f http://localhost:8000/api/v1/agents/list || echo "Agent listing failed"

# Test chat
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test message",
    "agent_id": "general_assistant",
    "session_id": "test_session"
  }' || echo "Chat test failed"
```

### Performance Testing
```bash
# Measure response time
time curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quick test",
    "agent_id": "general_assistant",
    "session_id": "perf_test"
  }'
```

---

##  Tips & Best Practices

1. **Use appropriate session IDs** to maintain context across related interactions
2. **Choose the right agent** using the discovery endpoint for better results
3. **Provide context** in your requests to get more targeted responses
4. **Handle errors gracefully** by checking HTTP status codes
5. **Use streaming** for long-running tasks to improve user experience
6. **Test with different models** to find the best performance/cost balance

---

##  Notes

- All timestamps are in ISO 8601 format
- File uploads are limited by the `MAX_FILE_SIZE` setting
- Session data is kept in memory (implement persistent storage for production)
- Rate limiting may apply (check the `RATE_LIMIT_*` settings)