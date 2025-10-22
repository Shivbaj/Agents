#!/bin/bash

# Docker startup script for Multi-Agent System
# This script handles initialization and startup in Docker environment

set -e

echo "🐳 Starting Multi-Agent System in Docker..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Environment check
echo -e "${BLUE}🔍 Environment Check${NC}"
echo "  - Python: $(python --version)"
echo "  - Environment: ${ENVIRONMENT:-development}"
echo "  - Docker: ${DOCKER_ENV:-false}"

# Wait for external services
echo -e "${BLUE}⏳ Waiting for external services...${NC}"

# Wait for Redis (if configured)
if [ -n "$REDIS_URL" ] && [ "$REDIS_URL" != "" ]; then
    echo -e "${YELLOW}  Checking Redis connection...${NC}"
    max_retries=30
    for i in $(seq 1 $max_retries); do
        if uv run python -c "import redis; redis.from_url('${REDIS_URL}').ping()" > /dev/null 2>&1; then
            echo -e "${GREEN}  ✓ Redis is ready${NC}"
            break
        fi
        if [ $i -eq $max_retries ]; then
            echo -e "${RED}  ✗ Redis failed to start after $max_retries attempts${NC}"
            exit 1
        fi
        echo -e "${YELLOW}  Attempt $i/$max_retries - Redis not ready, waiting...${NC}"
        sleep 2
    done
else
    echo -e "${YELLOW}  ⚠ Redis not configured, skipping...${NC}"
fi

# Wait for Ollama (if configured)
if [ -n "$OLLAMA_BASE_URL" ] && [ "$OLLAMA_BASE_URL" != "" ]; then
    echo -e "${YELLOW}  Checking Ollama connection...${NC}"
    for i in $(seq 1 $max_retries); do
        if curl -s "${OLLAMA_BASE_URL}/api/tags" > /dev/null 2>&1; then
            echo -e "${GREEN}  ✓ Ollama is ready${NC}"
            break
        fi
        if [ $i -eq $max_retries ]; then
            echo -e "${YELLOW}  ⚠ Ollama not available (continuing anyway)${NC}"
            break
        fi
        echo -e "${YELLOW}  Attempt $i/$max_retries - Ollama not ready, waiting...${NC}"
        sleep 2
    done
else
    echo -e "${YELLOW}  ⚠ Ollama not configured, skipping...${NC}"
fi

# Initialize application
echo -e "${BLUE}🚀 Initializing application...${NC}"
if ! uv run python scripts/dev_setup.py; then
    echo -e "${YELLOW}  ⚠ Setup script had issues (continuing anyway)${NC}"
fi

# Create runtime directories
echo -e "${BLUE}📁 Preparing runtime directories...${NC}"
mkdir -p /app/logs /app/data/uploads /app/data/models /app/data/cache
chown -R app:app /app/logs /app/data 2>/dev/null || true

# Check API keys
echo -e "${BLUE}🔑 API Key Status${NC}"
if [ -n "$OPENAI_API_KEY" ]; then
    echo -e "${GREEN}  ✓ OpenAI API key configured${NC}"
else
    echo -e "${YELLOW}  ⚠ OpenAI API key not configured${NC}"
fi

if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo -e "${GREEN}  ✓ Anthropic API key configured${NC}"
else
    echo -e "${YELLOW}  ⚠ Anthropic API key not configured${NC}"
fi

if [ -n "$LANGSMITH_API_KEY" ]; then
    echo -e "${GREEN}  ✓ LangSmith API key configured${NC}"
else
    echo -e "${YELLOW}  ⚠ LangSmith API key not configured (using mock mode)${NC}"
fi

# Start the application
echo -e "${GREEN}🎯 Starting Multi-Agent System API Server...${NC}"
echo -e "${BLUE}  📡 API: http://0.0.0.0:8000${NC}"
echo -e "${BLUE}  📚 Docs: http://0.0.0.0:8000/docs${NC}"
echo -e "${BLUE}  ❤️ Health: http://0.0.0.0:8000/health${NC}"
echo ""

# Handle shutdown gracefully
trap 'echo -e "\n${YELLOW}🛑 Shutting down Multi-Agent System...${NC}"; exit 0' INT TERM

# Start the server with proper error handling
exec uv run uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --loop uvloop \
    --http httptools \
    --log-level info \
    --access-log \
    --use-colors