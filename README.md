# 🤖 Multi-Agent System

A **clean, modular, and extensible** multi-agent system built with **FastAPI**, **Model Context Protocol (MCP)**, and **multiple LLM providers**. This system provides a flexible framework for AI agents with tool integration, conversation memory, and comprehensive observability.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-Enabled-purple.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

### 🏗️ **Modular Architecture**
- **Object-oriented design** with clean interfaces
- **Plugin-based agent system** for easy extensibility
- **Base agent classes** for rapid development
- **Comprehensive error handling** and logging with Loguru

### 🔌 **Model Context Protocol (MCP) Integration**
- **Extensible tool system** via MCP servers
- **Web search capabilities** with built-in server
- **Dynamic server registration** and management
- **Tool composition** for complex workflows

### 🤖 **Multi-Agent Framework**
- **General Assistant Agent** with enhanced capabilities
- **Summarizer Agent** for content processing
- **Vision Agent** for multimodal interactions
- **Agent Registry** for dynamic discovery and management

### 🌐 **Multiple LLM Provider Support**
- **OpenAI** (GPT-4, GPT-3.5-turbo, and more)
- **Anthropic** (Claude 3 family)
- **Ollama** (Local models - phi3:mini, llama2, etc.)
- **Easy provider extension** with unified interface

### 🧮 **Advanced Memory & State**
- **Conversation memory** with Redis backend
- **Session management** across interactions
- **Persistent conversation history**
- **Configurable memory retention**

### 🔄 **Workflow & Orchestration**
- **Async/await based** execution
- **FastAPI integration** with automatic API documentation
- **Health monitoring** for all services
- **Docker containerization** for easy deployment

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** 
- **Docker & Docker Compose** (recommended for full deployment)
- **Optional**: LLM Provider API Keys (OpenAI, Anthropic)

### 🐳 Docker Deployment (Recommended)

1. **Clone the repository**
```bash
git clone <repository-url>
cd multi-agent-system
```

2. **Start all services with Docker Compose**
```bash
# Start all services (FastAPI app, Redis, Ollama with phi3:mini)
docker-compose up -d

# View logs
docker-compose logs -f app

# Check service health
docker-compose ps
```

3. **Test the deployment**
```bash
# Health check
curl http://localhost:8000/health

# List available agents
curl http://localhost:8000/api/v1/agents/

# Chat with dummy agent for testing
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello! Can you tell me a random fact?",
    "agent_id": "dummy_agent",
    "session_id": "test_session"
  }'
```

### 🔧 Manual Installation

1. **Install dependencies using uv (recommended)**
```bash
# Install uv package manager
pip install uv

# Install project dependencies
uv sync
```

2. **Set up environment variables**
```bash
# Copy example environment file
cp .env.example .env

# Edit with your configuration
nano .env
```

**Example .env file:**
```bash
# LLM Provider API Keys (optional - Ollama works without them)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Ollama settings (for local models)
OLLAMA_BASE_URL=http://localhost:11434

# Redis settings
REDIS_URL=redis://localhost:6379

# API Configuration
API_TITLE=Multi-Agent System
API_VERSION=1.0.0
LOG_LEVEL=INFO
DEBUG=false

# CORS settings
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

3. **Start Redis and Ollama (if running manually)**
```bash
# Start Redis
redis-server

# Install and start Ollama with phi3:mini model
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
ollama pull phi3:mini
```

4. **Run the FastAPI server**
```bash
# Development mode with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
python -m src.main
```

---

## 📁 Project Structure

```
multi-agent-system/
├── src/
│   ├── agents/                 # 🤖 Agent implementations
│   │   ├── base/              #   └── Base agent classes & interfaces
│   │   │   └── agent.py      #   └── BaseAgent abstract class
│   │   ├── implementations/   #   └── Concrete agent implementations
│   │   │   ├── general_assistant_enhanced.py  # General purpose agent
│   │   │   ├── summarizer_agent.py            # Text summarization   agent  
│   │   │   └── vision_agent.py                # Multimodal vision agent
│   │   └── registry/          #   └── Agent discovery & management
│   │       └── manager.py    #   └── AgentManager for registration
│   │
│   ├── api/                   # 🌐 FastAPI routes & endpoints
│   │   ├── routes.py         #   └── Main router setup
│   │   └── v1/               #   └── API version 1
│   │       ├── agent_routes.py #   └── Agent interaction endpoints
│   │       ├── health.py     #   └── Health check endpoints
│   │       ├── mcp.py        #   └── MCP integration endpoints
│   │       ├── models.py     #   └── Model management endpoints
│   │       └── schemas.py    #   └── Pydantic data models
│   │
│   ├── config/                # ⚙️ Configuration management
│   │   └── settings.py       #   └── Pydantic settings with env vars
│   │
│   ├── core/                  # 🏛️ Core system components
│   │   ├── exceptions.py     #   └── Custom exception classes
│   │   ├── logging.py        #   └── Loguru logging setup
│   │   └── middleware.py     #   └── FastAPI middleware
│   │
│   ├── memory/                # 🧠 Memory & conversation management
│   │   └── conversation.py   #   └── Redis-backed conversation storage
│   │
│   ├── mcp/                   # 🔌 Model Context Protocol integration
│   │   ├── base/             #   └── MCP base classes
│   │   │   └── tool.py      #   └── BaseMCPTool class
│   │   ├── manager.py        #   └── MCP server lifecycle management
│   │   └── servers/          #   └── MCP server implementations
│   │       └── web_search.py #   └── Web search MCP server
│   │
│   ├── services/              # 🔧 Business logic services
│   │   └── model_manager.py  #   └── Model lifecycle & provider management
│   │
│   ├── observability/         # 📊 Monitoring & observability
│   │   └── langsmith.py      #   └── LangSmith integration (optional)
│   │
│   ├── orchestrator/          # 🎭 Workflow orchestration
│   │   └── workflow.py       #   └── Multi-agent workflow management
│   │
│   ├── prompts/               # 📝 Prompt template management
│   │   ├── manager.py        #   └── Template manager & loader
│   │   └── templates/        #   └── JSON prompt templates
│   │       ├── general_assistant.json    # General assistant prompts
│   │       ├── summarizer_agent.json     # Summarizer prompts  
│   │       └── vision_agent.json         # Vision agent prompts
│   │
│   ├── tools/                 # 🛠️ Agent tools & utilities
│   │   └── base_tools.py     #   └── Core tool implementations
│   │
│   ├── utils/                 # 🔨 Utility functions
│   │   └── file_utils.py     #   └── File operations & helpers
│   │
│   └── main.py               # 🚀 FastAPI application entry point
│
├── tests/                     # 🧪 Test suite
│   └── test_agent_registry.py  # Agent registry tests
├── scripts/                   # 🔧 Development scripts  
│   └── dev_setup.py          #   └── Development environment setup
├── docker/                   # 🐳 Docker configuration files
│   └── prometheus.yml        #   └── Prometheus monitoring config
├── data/                     # 📁 Data directory (created at runtime)
│   ├── cache/               #   └── Cache files
│   ├── uploads/             #   └── File uploads
│   └── models/              #   └── Model storage
├── logs/                     # 📋 Application logs (created at runtime)
├── docker-compose.yml        # � Docker orchestration
├── Dockerfile               # � Application container definition
├── pyproject.toml           # 📦 Project configuration & dependencies
├── requirements.txt         # 📦 Python dependencies (fallback)
└── README.md               # 📋 This documentation
```

---

## 🎯 Core Concepts

### 🤖 **Agents**

Agents are the core components that process messages and perform tasks. All agents inherit from `BaseAgent`:

**Available Agents:**
- **GeneralAssistant**: Enhanced general purpose agent with tool integration
- **SummarizerAgent**: Specialized for content summarization and analysis  
- **VisionAgent**: Multimodal agent for processing images and visual content
- **DummyAgent**: Simple test agent for demonstration and system validation

```python
from src.agents.registry.manager import AgentManager

# Get the agent manager
agent_manager = AgentManager()
await agent_manager.initialize()

# List available agents
agents = agent_manager.list_agents()
print(f"Found {len(agents)} agents")  # Found 4 agents

# Get a specific agent
agent = agent_manager.get_agent("dummy_agent")

# Process messages
response = await agent.process_message(
    message="What can you help me with?",
    session_id="user_123",
    context={}
)
```

### 🧠 **Memory System**

Redis-backed conversation memory with session management:

```python
from src.memory.conversation import ConversationMemory

# Create conversation memory for a session
memory = ConversationMemory("session_123")

# Add messages to conversation history
await memory.add_message("user", "Tell me about Python")
await memory.add_message("assistant", "Python is a programming language...")

# Get conversation history
history = await memory.get_messages(limit=10)

# Clear session memory
await memory.clear()
```

### 📝 **Prompt Templates**

JSON-based prompt template system with dynamic loading:

```python
from src.prompts.manager import PromptManager

# Load prompt templates
prompt_manager = PromptManager()
await prompt_manager.load_templates()

# Get system prompts for agents
general_prompt = prompt_manager.get_template("general_assistant")
summarizer_prompt = prompt_manager.get_template("summarizer_agent")

# Templates include:
# - system_prompt: Core agent instructions
# - task_definitions: Specific task descriptions  
# - response_formats: Expected output formats
```

### � **MCP Integration**

Model Context Protocol servers provide extensible tool functionality:

```python
from src.mcp.manager import get_mcp_manager
from src.mcp.servers.web_search import WebSearchServer

# Get MCP manager
mcp_manager = get_mcp_manager()
await mcp_manager.initialize()

# Register a new server
web_server = WebSearchServer()
await mcp_manager.register_server(web_server)

# List available tools from all servers
tools = await mcp_manager.list_tools()

# Execute a tool
result = await mcp_manager.call_tool("web_search", {
    "query": "Python tutorials",
    "max_results": 5
})
```

### 🤖 **Model Management**

Unified model management through the ModelManager service:

```python
from src.services.model_manager import ModelManager

# Get the model manager
model_manager = ModelManager()
await model_manager.initialize()

# List available models from all providers
models = await model_manager.list_models()

# Get models from specific provider
ollama_models = await model_manager.list_models(provider="ollama")
openai_models = await model_manager.list_models(provider="openai")

# Generate text using a model
response = await model_manager.generate_text(
    provider="ollama",
    model_name="phi3:mini",
    prompt="Hello! How can I help you?"
)
```

---

## � API Documentation

The system exposes a comprehensive REST API for agent interaction. Once running, visit `http://localhost:8000/docs` for interactive API documentation.

### 📋 **Health & System Endpoints**

```bash
# System health check
GET /health
curl http://localhost:8000/health

# API information  
GET /
curl http://localhost:8000/

# Get system configuration
GET /api/v1/models/config
curl http://localhost:8000/api/v1/models/config
```

### 🤖 **Agent Management Endpoints**

```bash
# List all available agents
GET /api/v1/agents/list
curl http://localhost:8000/api/v1/agents/list

# Get agent statistics
GET /api/v1/agents/stats
curl http://localhost:8000/api/v1/agents/stats

# Get specific agent details
GET /api/v1/agents/{agent_id}
curl http://localhost:8000/api/v1/agents/dummy_agent

# Get agent card with detailed info
GET /api/v1/agents/{agent_id}/card
curl http://localhost:8000/api/v1/agents/dummy_agent/card

# Discover agents by query
GET /api/v1/agents/discover?query={query}&limit={limit}
curl "http://localhost:8000/api/v1/agents/discover?query=summarize%20text&limit=5"
```

### 💬 **Chat Endpoints**

```bash
# Chat with an agent
POST /api/v1/agents/chat
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello! Can you help me with Python programming?",
    "agent_id": "general_assistant",
    "session_id": "my_session_123",
    "context": {}
  }'

# Stream chat response  
POST /api/v1/agents/chat/stream
curl -X POST "http://localhost:8000/api/v1/agents/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Write a detailed explanation about machine learning",
    "agent_id": "general_assistant",
    "stream": true
  }'

# Multimodal chat (with file upload)
POST /api/v1/agents/multimodal
curl -X POST "http://localhost:8000/api/v1/agents/multimodal" \
  -F "file=@image.jpg" \
  -F "message=Describe this image" \
  -F "agent_id=vision_agent" \
  -F "session_id=session_123"
```

### � **MCP Integration Endpoints**

```bash
# List MCP servers
GET /api/v1/mcp/servers
curl http://localhost:8000/api/v1/mcp/servers

# List available MCP tools
GET /api/v1/mcp/tools
curl http://localhost:8000/api/v1/mcp/tools

# Execute MCP tool
POST /api/v1/mcp/tools/execute
curl -X POST "http://localhost:8000/api/v1/mcp/tools/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "web_search",
    "arguments": {
      "query": "Python tutorials",
      "max_results": 5
    }
  }'

# Check MCP system health
GET /api/v1/mcp/health
curl http://localhost:8000/api/v1/mcp/health
```

### �🔧 **Model Management Endpoints**

```bash
# List available models
GET /api/v1/models/list
curl http://localhost:8000/api/v1/models/list

# List model providers
GET /api/v1/models/providers
curl http://localhost:8000/api/v1/models/providers

# Test model generation
POST /api/v1/models/test
curl -X POST "http://localhost:8000/api/v1/models/test" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "ollama",
    "model": "phi3:mini",
    "prompt": "Hello! How can I help you?"
  }'
```

### 📊 **Response Formats**

**Agent Chat Response:**
```json
{
  "response": "Hello! I'm here to help you with Python programming...",
  "agent_id": "general_assistant",
  "session_id": "my_session_123",
  "metadata": {
    "model_used": "phi3:mini",
    "provider": "ollama",
    "processing_time": 1.23,
    "token_count": 45
  }
}
```

**Agent List Response:**
```json
{
  "agents": [
    {
      "agent_id": "general_assistant",
      "name": "General Assistant",
      "description": "Enhanced general purpose agent",
      "capabilities": ["conversation", "tool_use", "web_search"],
      "status": "active"
    }
  ],
  "total": 3
}
```

**Error Response:**
```json
{
  "detail": "Agent not found: invalid_agent",
  "error_type": "AgentNotFoundException",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## �🏗️ Extending the System

### 🤖 **Creating a Custom Agent**

```python
from src.agents.base.agent import BaseAgent

class MyCustomAgent(BaseAgent):
    def __init__(self, agent_id: str = "custom_agent", **kwargs):
        super().__init__(
            agent_id=agent_id,
            name="My Custom Agent",
            description="A specialized agent for specific tasks",
            capabilities=["custom_processing", "domain_specific"],
            **kwargs
        )
        self.custom_config = {}
    
    async def _initialize_agent(self):
        """Initialize custom agent resources"""
        self.logger.info(f"Initializing {self.name}")
        # Load custom configuration, models, tools, etc.
        self.custom_config = {"initialized": True}
    
    async def _process_message(self, message: str, session_id: str, context: dict = None) -> dict:
        """Process message with custom logic"""
        self.logger.info(f"Processing message: {message}")
        
        # Custom processing logic
        processed_content = f"Custom processing: {message}"
        
        return {
            "content": processed_content,
            "agent_id": self.agent_id,
            "session_id": session_id,
            "metadata": {
                "processing_type": "custom",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
    
    async def _cleanup_agent(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up custom agent")

# Register with agent manager
from src.agents.registry.manager import AgentManager
agent_manager = AgentManager()
custom_agent = MyCustomAgent()
agent_manager.register_agent(custom_agent)
```

### � **Creating a Custom MCP Server**

```python
from src.mcp.base.tool import BaseMCPTool

class CustomMCPServer:
    def __init__(self):
        self.server_id = "custom_server"
        self.name = "Custom Server"
        self.description = "Custom MCP server implementation"
        self.tools = {
            "custom_tool": CustomTool()
        }
    
    async def initialize(self):
        """Initialize server resources"""
        pass
    
    async def get_tools(self) -> dict:
        """Return available tools"""
        return self.tools
    
    async def call_tool(self, tool_name: str, args: dict):
        """Execute a tool with given arguments"""
        if tool_name in self.tools:
            return await self.tools[tool_name].execute(args)
        raise ValueError(f"Tool {tool_name} not found")

class CustomTool(BaseMCPTool):
    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="A custom tool implementation"
        )
    
    async def execute(self, args: dict) -> dict:
        """Execute the custom tool"""
        # Custom tool logic here
        return {
            "result": f"Custom tool executed with: {args}",
            "success": True
        }

# Register with MCP manager
from src.mcp.manager import get_mcp_manager
mcp_manager = get_mcp_manager()
custom_server = CustomMCPServer()
await mcp_manager.register_server(custom_server)
```

### 🌐 **Extending Model Support**

To add support for new LLM providers, extend the ModelManager service:

```python
from src.services.model_manager import ModelManager

class EnhancedModelManager(ModelManager):
    def __init__(self):
        super().__init__()
        # Add custom provider initialization
        self.custom_providers = {}
    
    async def add_custom_provider(self, provider_name: str, provider_config: dict):
        """Add a custom model provider"""
        # Implement custom provider logic
        self.custom_providers[provider_name] = provider_config
    
    async def generate_custom_text(self, provider: str, model: str, prompt: str):
        """Generate text using custom provider"""
        if provider in self.custom_providers:
            # Implement custom generation logic
            pass
        return await super().generate_text(provider, model, prompt)
```
```

### 🛠️ **Adding Custom Tools**

Extend the base tools functionality:

```python
from src.tools.base_tools import BaseTool

class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_custom_tool",
            description="A custom tool for specific tasks"
        )
    
    async def execute(self, **kwargs):
        """Execute the custom tool"""
        # Implement your tool logic
        return {"result": "Custom tool executed successfully"}

# Register the tool
from src.tools.base_tools import get_tool, register_tool
register_tool("my_tool", MyCustomTool)
```

### 📝 **Creating Custom Prompt Templates**

Create JSON files in `src/prompts/templates/`:

```json
{
  "type": "chat",
  "metadata": {
    "id": "my_agent",
    "name": "My Custom Agent",
    "description": "A custom agent prompt",
    "version": "1.0.0",
    "variables": [
      {
        "name": "user_input",
        "type": "string",
        "required": true,
        "description": "User's input message"
      }
    ]
  },
  "system_message": "You are a helpful assistant specialized in...",
  "messages": [
    {
      "role": "human",
      "content": "{user_input}"
    }
  ]
}
```

### 🔄 **Creating Custom Workflows**

```python
from src.orchestrator.workflow import MultiAgentWorkflow, WorkflowNode

# Create custom workflow
workflow = MultiAgentWorkflow("my_workflow", "Custom Processing")

# Add nodes
workflow.add_node(WorkflowNode(
    name="validator",
    agent_type="general_assistant"
))

workflow.add_node(WorkflowNode(
    name="processor", 
    agent_type="specialized_agent"
))

workflow.add_node(WorkflowNode(
    name="formatter",
    function=my_custom_function
))

# Build workflow
workflow.compile()
workflow.add_edge("validator", "processor")
workflow.add_edge("processor", "formatter")
workflow.finish_at("formatter")

# Execute
result = await workflow.execute({"input": "data"})
```

---

## 🔧 Configuration

### ⚙️ **Environment Variables**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | - | No* |
| `ANTHROPIC_API_KEY` | Anthropic API key | - | No |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` | No |
| `DATABASE_URL` | Database connection | `sqlite:///./data/agents.db` | No |
| `REDIS_URL` | Redis connection | `redis://localhost:6379` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `DEBUG` | Debug mode | `False` | No |

*At least one model provider is recommended

### 📊 **Model Configuration**

```python
# In src/config/settings.py
class Settings(BaseSettings):
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_default_model: str = "gpt-4-turbo-preview"
    
    # Anthropic
    anthropic_api_key: Optional[str] = None
    anthropic_default_model: str = "claude-3-sonnet-20240229"
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3.2:1b"
```

---

## 🐳 Docker Deployment

### Development
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Custom Build
```bash
# Build image
docker build -t multi-agent-system .

# Run container
docker run -p 8000:8000 --env-file .env multi-agent-system
```

---

## � Configuration & Deployment

### ⚙️ **Environment Variables**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT models | - | No* |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude models | - | No |
| `OLLAMA_BASE_URL` | Ollama server endpoint | `http://localhost:11434` | Yes† |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` | Yes |
| `LOG_LEVEL` | Application log level | `INFO` | No |
| `DEBUG` | Enable debug mode | `false` | No |
| `CORS_ORIGINS` | Allowed CORS origins | `["*"]` | No |

*At least one model provider (OpenAI, Anthropic, or Ollama) is required  
†Ollama is included in Docker setup by default

### 🐳 **Production Deployment**

**Option 1: Docker Compose (Recommended)**
```bash
# Clone repository
git clone <your-repository-url>
cd multi-agent-system

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start all services
docker-compose up -d

# Check service health
docker-compose logs -f app
curl http://localhost:8000/health
```

**Option 2: Manual Installation**
```bash
# Install Python dependencies
pip install uv
uv sync

# Start external services
redis-server &
ollama serve &
ollama pull phi3:mini

# Run application
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 🔍 **Monitoring & Logs**

**View application logs:**
```bash
# Docker deployment
docker-compose logs -f app

# Manual deployment
tail -f logs/app.log
```

**Health monitoring endpoints:**
```bash
# System health
curl http://localhost:8000/health

# Agent registry status
curl http://localhost:8000/api/v1/agents/list

# Model availability
curl http://localhost:8000/api/v1/models/available
```
WorkingDirectory=/opt/multi-agent-system
Environment=PATH=/opt/multi-agent-system/venv/bin
ExecStart=/opt/multi-agent-system/venv/bin/python -m src.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable multi-agent-system
sudo systemctl start multi-agent-system
sudo systemctl status multi-agent-system
```

### 🔒 Security Considerations

**Before deploying to production:**

1. **Change default secrets**:
---

## 🧪 Testing & Validation

```bash
# Run system validation script
python validate_system.py

# Run API tests
bash test_api.sh

# Run specific tests  
python -m pytest tests/test_agent_registry.py -v
```

---

## 🐛 Troubleshooting

### **Common Issues**

**🔴 Docker Services Not Starting**
```bash
# Check Docker daemon
docker --version
docker-compose --version

# View service logs
docker-compose logs redis
docker-compose logs ollama
docker-compose logs app

# Restart specific service
docker-compose restart app
```

**🔴 Ollama Model Issues**
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Pull model manually
docker exec -it agents-ollama-1 ollama pull phi3:mini

# Check model availability
curl -X POST http://localhost:11434/api/generate \
  -d '{"model": "phi3:mini", "prompt": "test", "stream": false}'
```

**🔴 Redis Connection Failed**
```bash
# Test Redis connection
redis-cli ping

# Check Redis in Docker
docker-compose exec redis redis-cli ping

# Clear Redis cache
redis-cli FLUSHALL
```

**🔴 Agent Registry Issues**
```bash
# Check agent loading logs
docker-compose logs app | grep "agent"

# Test agent endpoints directly
curl http://localhost:8000/api/v1/agents/list
curl http://localhost:8000/api/v1/agents/general_assistant
```

**🔴 Memory/Performance Issues**
```bash
# Monitor Docker resource usage
docker stats

# Increase memory limits in docker-compose.yml
# Restart with fresh containers
docker-compose down && docker-compose up -d
```

### **Debug Commands**

```bash
# System health check
curl http://localhost:8000/health | jq

# Validate all components
python validate_system.py

# Test complete workflow
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, test the system",
    "agent_id": "general_assistant",
    "session_id": "debug_session"
  }' | jq
```

---

## 📚 Additional Resources

- **📖 [API Documentation](API_DOCUMENTATION.md)** - Complete API reference
- **🏗️ [Architecture Guide](ARCHITECTURE.md)** - System design & components  
- **⚡ [Quick Reference](QUICK_REFERENCE.md)** - Common commands & examples
- **🚀 [Development Guide](DEVELOPMENT.md)** - Contributing & customization
- **📋 [Validation Report](DOCKER_VALIDATION_REPORT.md)** - System test results

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### **Development Setup**
```bash
# Install development dependencies
uv sync --dev

# Run development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run validation tests
python validate_system.py
bash test_api.sh
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[FastAPI](https://fastapi.tiangolo.com/)** - High-performance web framework
- **[Ollama](https://ollama.ai/)** - Local LLM deployment platform  
- **[Redis](https://redis.io/)** - In-memory data structure store
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - Tool integration standard
- **[Docker](https://www.docker.com/)** - Containerization platform

---

## ⭐ Star History

If this project helps you, please consider giving it a star! 

**Ready to build powerful AI agents? Start with Docker deployment! 🚀**

```bash
docker-compose up -d && curl http://localhost:8000/health
```