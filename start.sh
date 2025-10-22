#!/bin/bash

# Multi-Agent System Startup Script
# This script sets up and runs the multi-agent system

set -e

echo " Multi-Agent System Startup"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED} uv is not installed. Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

echo -e "${GREEN}✓ uv is available${NC}"

# Install dependencies
echo -e "${BLUE} Installing dependencies with uv...${NC}"
uv sync

# Create necessary directories
echo -e "${BLUE} Setting up directories...${NC}"
mkdir -p data/uploads data/models logs

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}  Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}  Please update .env with your API keys and configuration${NC}"
fi

# Setup development environment
echo -e "${BLUE} Setting up development environment...${NC}"
uv run python scripts/dev_setup.py

# Check if Docker is available and offer to start services
if command -v docker &> /dev/null && (command -v docker-compose &> /dev/null || command -v docker compose &> /dev/null); then
    echo -e "${BLUE}🐳 Docker is available${NC}"
    
    # Determine docker-compose command
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        DOCKER_COMPOSE="docker compose"
    fi
    
    echo "Available Docker configurations:"
    echo "1) Development (dev) - with hot reload and debugging"
    echo "2) Production (prod) - optimized for production"
    echo "3) Local services only (redis + ollama)"
    echo "4) Skip Docker setup"
    
    read -p "Choose option (1-4): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            echo -e "${BLUE}🚀 Starting development environment...${NC}"
            $DOCKER_COMPOSE -f docker-compose.dev.yml up -d
            echo -e "${GREEN}✓ Development environment started${NC}"
            echo -e "${BLUE}📡 API: http://localhost:8000${NC}"
            echo -e "${BLUE}📚 Docs: http://localhost:8000/docs${NC}"
            echo -e "${BLUE}🔧 Redis Commander: http://localhost:8081${NC}"
            ;;
        2)
            echo -e "${BLUE}🏭 Starting production environment...${NC}"
            $DOCKER_COMPOSE -f docker-compose.prod.yml up -d
            echo -e "${GREEN}✓ Production environment started${NC}"
            echo -e "${BLUE}📡 API: https://localhost${NC}"
            echo -e "${BLUE}📊 Grafana: http://localhost:3000${NC}"
            echo -e "${BLUE}📈 Prometheus: http://localhost:9090${NC}"
            ;;
        3)
            echo -e "${BLUE}🔧 Starting local services only...${NC}"
            $DOCKER_COMPOSE up -d redis ollama
            
            # Wait for services
            echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
            sleep 10
            
            # Pull Ollama model
            echo -e "${BLUE}📥 Pulling Ollama model (llama3.2:1b)...${NC}"
            $DOCKER_COMPOSE exec ollama ollama pull llama3.2:1b || echo -e "${YELLOW}⚠️  Could not pull model, you can do this later${NC}"
            ;;
        4)
            echo -e "${YELLOW}⏭️  Skipping Docker setup${NC}"
            ;;
        *)
            echo -e "${YELLOW}⏭️  Invalid option, skipping Docker setup${NC}"
            ;;
    esac
fi

# Start the application
echo -e "${GREEN} Starting Multi-Agent System...${NC}"
echo -e "${BLUE} API Documentation will be available at: http://localhost:8000/docs${NC}"
echo -e "${BLUE} Health check available at: http://localhost:8000/health${NC}"
echo -e "${BLUE} Postman collection: postman_collection.json${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start the server with uv
exec uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000