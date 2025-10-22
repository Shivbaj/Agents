# 🤖 Multi-Agent System

A **clean, modular, and extensible** multi-agent system built with **FastAPI**, **LangChain**, **LangGraph**, and **Model Context Protocol (MCP)**. This system allows you to easily plug in new tools, servers, models, and APIs while maintaining a clean, object-oriented architecture.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-purple.svg)](https://python.langchain.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

### 🏗️ **Modular Architecture**
- **Object-oriented design** with clean interfaces
- **Plugin-based system** for easy extensibility
- **Base agent classes** for rapid development
- **Comprehensive error handling** and logging

### 🧠 **LangChain & LangGraph Integration**
- **Unified LLM interfaces** across providers
- **Advanced memory management** (conversation + vector storage)
- **Multi-agent workflows** with LangGraph
- **Prompt template system** with versioning

### 🛠️ **Tool Ecosystem**
- **Web search capabilities** (DuckDuckGo, Google)
- **File processing** (PDF, DOCX, TXT, images)
- **Safe code execution** (sandboxed Python)
- **Mathematical calculations**
- **Custom tool creation** framework

### 🌐 **Model Provider Support**
- **OpenAI** (GPT-4, GPT-3.5, DALL-E, Whisper)
- **Anthropic** (Claude 3)
- **Ollama** (Local models)
- **Easy provider extension**

### 🧮 **Advanced Memory**
- **Conversation buffer management**
- **Vector-based semantic search**
- **Persistent storage options**
- **Context-aware retrieval**

### 🔄 **Workflow Orchestration**
- **Multi-agent coordination** with LangGraph
- **Conditional routing** and decision making
- **Parallel execution** capabilities
- **Error recovery** and retry logic

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **OpenAI API Key** (recommended)
- **Docker & Docker Compose** (optional)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd multi-agent-system
```

2. **Install dependencies**
```bash
# Using pip
pip install -e .

# Or using uv (recommended)
pip install uv
uv sync
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

**Example .env file:**
```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional: Local model settings
OLLAMA_BASE_URL=http://localhost:11434

# Optional: Web search
GOOGLE_SEARCH_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id

# Database
DATABASE_URL=sqlite:///./data/agents.db

# Logging
LOG_LEVEL=INFO
```

4. **Run the quick start example**
```bash
python -m tests.examples.quickstart
```

5. **Start the FastAPI server**
```bash
# Development
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production
python -m src.main
```

6. **Test the API**
```bash
# Health check
curl http://localhost:8000/health

# Chat with an agent
curl -X POST "http://localhost:8000/api/v1/agents/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello! Can you help me calculate 25 * 17?",
    "agent_id": "general_assistant",
    "session_id": "test_session"
  }'
```

---

## 📁 Project Structure

```
multi-agent-system/
├── src/
│   ├── agents/                 # 🤖 Agent implementations
│   │   ├── base/              #   └── Base agent classes
│   │   ├── implementations/   #   └── Concrete agent implementations
│   │   ├── registry/          #   └── Agent discovery & management
│   │   └── specialized/       #   └── Domain-specific agents
│   │
│   ├── api/                   # 🌐 FastAPI routes & endpoints
│   │   └── v1/               #   └── API version 1
│   │
│   ├── config/                # ⚙️ Configuration management
│   │   └── settings.py       #   └── Pydantic settings
│   │
│   ├── core/                  # 🏛️ Core system components
│   │   ├── exceptions.py     #   └── Exception handling
│   │   ├── logging.py        #   └── Logging setup
│   │   └── middleware.py     #   └── FastAPI middleware
│   │

│   │
│   ├── memory/                # 🧠 Memory management
│   │   └── conversation.py   #   └── Conversation & vector memory
│   │
│   ├── mcp/                   # 🔌 Model Context Protocol
│   │   ├── base/             #   └── MCP base classes
│   │   ├── servers/          #   └── MCP server implementations
│   │   └── tools/            #   └── MCP tools
│   │
│   ├── models/                # 🤖 LLM model providers
│   │   └── providers/        #   └── Provider implementations
│   │
│   ├── observability/         # 📊 Monitoring & observability
│   │   └── langsmith.py      #   └── LangSmith integration
│   │
│   ├── orchestrator/          # 🎭 Multi-agent workflows
│   │   └── workflow.py       #   └── LangGraph workflows
│   │
│   ├── prompts/               # 📝 Prompt management
│   │   ├── manager.py        #   └── Template manager
│   │   └── templates/        #   └── Prompt templates (JSON)
│   │
│   ├── services/              # 🔧 Business logic services
│   │   └── model_manager.py  #   └── Model lifecycle management
│   │
│   ├── tools/                 # 🛠️ Agent tools & utilities
│   │   └── base_tools.py     #   └── Core tool implementations
│   │
│   └── utils/                 # 🔨 Utility functions
│       └── file_utils.py     #   └── File operations
│
├── tests/                     # 🧪 Test suite
│   └── examples/             # 📚 Usage examples & demos
├── docker/                    # 🐳 Docker configurations
├── docs/                      # 📖 Documentation
├── .env.example              # 📄 Environment template
├── pyproject.toml            # 📦 Project configuration
└── README.md                 # 📋 This file
```

---

## 🎯 Core Concepts

### 🤖 **Agents**

Agents are the core components that process messages and perform tasks. All agents inherit from `BaseAgent`:

```python
from src.agents.base.agent import BaseAgent
from src.agents.implementations.general_assistant_enhanced import GeneralAssistant

# Create an agent
agent = GeneralAssistant(
    agent_id="my_assistant",
    use_tools=True,
    use_web_search=True
)

await agent.initialize()

# Process messages
response = await agent.process_message(
    message="What's the weather like?",
    session_id="user_123"
)
```

### 🧠 **Memory System**

The memory system provides conversation context and semantic search:

```python
from src.memory.conversation import MemoryManager

# Create memory manager
memory_manager = MemoryManager()

# Conversation memory
conv_memory = memory_manager.create_conversation_memory("session_123")
await conv_memory.add_message("user", "I like Python programming")

# Hybrid memory (conversation + vector search)
hybrid_memory = memory_manager.create_hybrid_memory("session_456")
relevant_context = await hybrid_memory.search_relevant_context("programming")
```

### 📝 **Prompt Templates**

Manage and version your prompts with the template system:

```python
from src.prompts.manager import PromptManager, create_agent_prompt

# Create prompt manager
prompt_manager = PromptManager()

# Create custom template
custom_prompt = create_agent_prompt(
    agent_name="Code Helper",
    task_description="Help with programming questions",
    personality_traits=["helpful", "technical", "patient"]
)

# Register and use
prompt_manager.register_template("code_helper", custom_prompt)
formatted_prompt = await prompt_manager.get_prompt("code_helper", {
    "user_input": "How do I create a Python class?"
})
```

### 🛠️ **Tools**

Tools extend agent capabilities:

```python
from src.tools.base_tools import get_tool

# Get a tool
calc_tool = get_tool("calculator")
result = await calc_tool._arun("(15 + 25) * 2")

# Web search
search_tool = get_tool("web_search")
results = await search_tool._arun("Python tutorials")

# File processing
file_tool = get_tool("file_processor")
content = await file_tool._arun("/path/to/document.pdf")
```

### 🔄 **Workflows**

Create complex multi-agent workflows with LangGraph:

```python
from src.orchestrator.workflow import WorkflowBuilder

# Create workflow
builder = WorkflowBuilder()
workflow = builder.create_research_workflow()

# Execute
result = await workflow.execute({
    "query": "Research AI developments in 2024"
})
```

---

## 🏗️ Extending the System

### 🤖 **Creating a Custom Agent**

```python
from src.agents.base.agent import BaseAgent, AgentResponse

class MyCustomAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(
            name="My Custom Agent",
            description="A specialized agent for specific tasks",
            agent_type="custom",
            capabilities=["custom_task", "specialized_processing"],
            **kwargs
        )
    
    async def _initialize_agent(self):
        # Custom initialization logic
        pass
    
    async def _process_message(self, message: str, session_id: str, context: dict) -> AgentResponse:
        # Custom message processing logic
        response_content = f"Processed: {message}"
        
        return AgentResponse(
            content=response_content,
            metadata={"custom_field": "value"}
        )
```

### 🛠️ **Creating a Custom Tool**

```python
from langchain_core.tools import BaseTool

class MyCustomTool(BaseTool):
    name: str = "my_tool"
    description: str = "Description of what my tool does"
    
    def _run(self, input_data: str) -> str:
        # Synchronous implementation
        return f"Processed: {input_data}"
    
    async def _arun(self, input_data: str) -> str:
        # Asynchronous implementation
        return f"Processed: {input_data}"

# Register the tool
from src.tools.base_tools import AVAILABLE_TOOLS
AVAILABLE_TOOLS["my_tool"] = MyCustomTool
```

### 🤖 **Adding a New Model Provider**

```python
from src.models.providers.base_provider import EnhancedBaseProvider

class MyModelProvider(EnhancedBaseProvider):
    def __init__(self, api_key: str, **kwargs):
        config = ProviderConfig(
            provider_name="my_provider",
            api_key=api_key,
            **kwargs
        )
        super().__init__(config)
    
    async def _initialize_provider(self):
        # Initialize connection to your model API
        pass
    
    def create_llm(self, model_name: str, **kwargs):
        # Create LangChain-compatible LLM instance
        pass
    
    async def list_models(self):
        # Return available models
        pass
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

## 🚀 Git Deployment Guide

### Quick Deployment Checklist

1. **Clone the repository**
```bash
git clone <your-repository-url>
cd multi-agent-system
```

2. **Environment Setup**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys and configuration
nano .env  # or your preferred editor
```

3. **Install Dependencies**
```bash
# Using pip
pip install -e .

# Using uv (recommended)
pip install uv
uv sync
```

4. **Initialize Database** (if needed)
```bash
# Create data directory
mkdir -p data

# Run any database migrations
python -m src.scripts.init_db  # if you have initialization scripts
```

5. **Start the Application**
```bash
# Development
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production
python -m src.main
```

### 🔧 Production Deployment

#### Environment Variables for Production
Ensure these are set in your production `.env`:
```bash
# Security - CHANGE THESE!
SECRET_KEY=your-super-secure-secret-key-here
DEBUG=false
ENVIRONMENT=production

# Database (use production database)
DATABASE_URL=postgresql://user:password@localhost/dbname

# Redis (production instance)
REDIS_URL=redis://your-redis-server:6379

# API Keys (your actual keys)
OPENAI_API_KEY=your_actual_openai_key
ANTHROPIC_API_KEY=your_actual_anthropic_key

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/multi-agent-system/app.log
```

#### Using Docker in Production
```bash
# Build and run with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Or build and run manually
docker build -t multi-agent-system:latest .
docker run -d \
  --name multi-agent-system \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  multi-agent-system:latest
```

#### Systemd Service (Linux Production)
Create `/etc/systemd/system/multi-agent-system.service`:
```ini
[Unit]
Description=Multi-Agent System API
After=network.target

[Service]
Type=simple
User=www-data
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
   - Generate new `SECRET_KEY`
   - Use production database credentials
   - Use production Redis instance

2. **Network security**:
   - Configure firewall rules
   - Use HTTPS/TLS certificates
   - Restrict API access if needed

3. **Environment isolation**:
   - Never commit `.env` files
   - Use environment-specific configurations
   - Rotate API keys regularly

### 📋 Pre-Deployment Verification

Run this checklist before deploying:
```bash
# Test the application
python -m pytest

# Check for security issues
python -m bandit -r src/

# Lint the code
python -m flake8 src/
python -m black --check src/

# Test Docker build
docker build -t multi-agent-system-test .

# Test with your .env file
uvicorn src.main:app --host 0.0.0.0 --port 8000
curl http://localhost:8000/health
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_agent_registry.py
```

---

## 📊 Monitoring & Observability

### LangSmith Integration
```python
# Set environment variables
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=multi-agent-system

# Automatic tracing is enabled for all LangChain operations
```

### Metrics
- Agent performance statistics
- Tool usage tracking
- Memory system metrics
- API endpoint monitoring

---

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit changes** (`git commit -m 'Add amazing feature'`)
4. **Push to branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Setup
```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run linting
black src tests
isort src tests
flake8 src tests
mypy src
```

---

## 📚 Documentation

- **API Documentation**: `http://localhost:8000/docs` (when running)
- **Architecture Guide**: `docs/ARCHITECTURE.md`
- **Development Guide**: `docs/DEVELOPMENT.md`
- **API Examples**: `API_EXAMPLES.md`

---

## ⚠️ Important Notes

### 🔒 **Security**
- **Sandboxed code execution** for safety
- **Input validation** for all tools
- **API rate limiting** enabled
- **Environment isolation** recommended

### 🎛️ **Performance**
- **Async/await** throughout the system
- **Connection pooling** for databases
- **Caching** for frequently used data
- **Memory optimization** for conversations

### 🔄 **Scalability**
- **Horizontal scaling** support
- **Load balancing** ready
- **Microservices architecture**
- **Database optimization**

---

## 🐛 Troubleshooting

### Common Issues

**1. Import errors after installation**
```bash
# Reinstall in development mode
pip install -e .
```

**2. OpenAI API errors**
```bash
# Check API key
echo $OPENAI_API_KEY

# Verify connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

**3. Database connection issues**
```bash
# Create data directory
mkdir -p data

# Check permissions
ls -la data/
```

**4. Memory system issues**
```bash
# Install vector database dependencies
pip install chromadb faiss-cpu
```

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[LangChain](https://python.langchain.com/)** - LLM framework
- **[LangGraph](https://langchain-ai.github.io/langgraph/)** - Multi-agent workflows
- **[FastAPI](https://fastapi.tiangolo.com/)** - Web framework
- **[Pydantic](https://docs.pydantic.dev/)** - Data validation
- **[ChromaDB](https://www.trychroma.com/)** - Vector database

---

## 🚀 Getting Started Checklist

- [ ] Install Python 3.10+
- [ ] Clone the repository
- [ ] Install dependencies (`pip install -e .`)
- [ ] Set up `.env` file with API keys
- [ ] Run quick start example (`python -m tests.examples.quickstart`)
- [ ] Start the API server (`uvicorn src.main:app --reload`)
- [ ] Test the API endpoints
- [ ] Explore the examples and documentation
- [ ] Create your first custom agent
- [ ] Build your first workflow

**Ready to build amazing AI agents? Let's get started! 🎉**