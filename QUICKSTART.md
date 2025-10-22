# 🚀 Quick Start Guide

This guide will help you get the Multi-Agent System up and running quickly.

## Prerequisites

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Docker & Docker Compose (optional, for local models)

## Installation

### Option 1: Quick Start Script (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd multi-agent-system

# Run the startup script (installs dependencies and starts the system)
./start.sh
```

The startup script will:
- Install uv if not present
- Install all dependencies
- Set up directories
- Create .env file from template
- Optionally start Docker services
- Launch the development server

### Option 2: Manual Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Create directories
mkdir -p data/uploads data/models logs

# Run setup script
uv run python scripts/dev_setup.py

# Start the server
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

Edit the `.env` file with your API keys and preferences:

```env
# Required: Add your API keys
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional: Ollama configuration (for local models)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.2:1b
```

## First Steps

1. **Access the API Documentation**
   - Open http://localhost:8000/docs in your browser
   - Explore the interactive API documentation

2. **Check System Health**
   ```bash
   curl http://localhost:8000/health
   ```

3. **List Available Agents**
   ```bash
   curl http://localhost:8000/api/v1/agents/list
   ```

4. **Chat with an Agent**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/agents/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Hello, can you help me?",
       "agent_id": "general_assistant",
       "session_id": "my_session"
     }'
   ```

## Using with Postman

Import the provided Postman collection (`postman_collection.json`) to get pre-configured requests for all endpoints.

## Docker Services (Optional)

To use local models with Ollama:

```bash
# Start Redis and Ollama
docker-compose up -d

# Pull a model
docker-compose exec ollama ollama pull llama3.2:1b

# Check running services
docker-compose ps
```

## Next Steps

- Explore the [API Examples](API_EXAMPLES.md)
- Learn about [Agent Development](AGENT_DEVELOPMENT.md)
- Check [Troubleshooting](TROUBLESHOOTING.md) if you encounter issues

## Common Issues

### Port Already in Use
```bash
# Check what's using port 8000
lsof -i :8000

# Use a different port
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

### Missing API Keys
- Ensure you've added your API keys to the `.env` file
- Check the logs for specific error messages

### Dependencies Issues
```bash
# Update uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clean and reinstall dependencies
rm -rf .venv
uv sync
```