#!/usr/bin/env python3
"""
Development and Docker setup script for the Multi-Agent System
"""
import asyncio
import os
import sys
import subprocess
from pathlib import Path

# Add src to path for development
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def check_environment():
    """Check if we're running in Docker or development"""
    return os.getenv("DOCKER_ENV") == "true" or os.path.exists("/.dockerenv")


def create_directories():
    """Create necessary directories"""
    directories = [
        "data/uploads",
        "data/models",
        "data/cache",
        "logs",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")


def setup_logging():
    """Setup logging configuration"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create empty log files
    (log_dir / "app.log").touch()
    (log_dir / "error.log").touch()
    print("✓ Logging directories configured")


def check_dependencies():
    """Check if critical dependencies are available"""
    try:
        # Check if we can import key modules
        import fastapi
        import uvicorn
        import pydantic
        print("✓ Core dependencies available")
        return True
    except ImportError as e:
        print(f"⚠️  Missing dependencies: {e}")
        return False


async def wait_for_services():
    """Wait for external services to be ready (Docker mode)"""
    if not check_environment():
        return
    
    print("🐳 Docker environment detected, waiting for services...")
    
    # Wait for Redis
    max_retries = 30
    for i in range(max_retries):
        try:
            import redis.asyncio as redis
            redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))
            await redis_client.ping()
            print("✓ Redis connection successful")
            await redis_client.close()
            break
        except Exception as e:
            if i == max_retries - 1:
                print(f"⚠️  Redis connection failed after {max_retries} attempts: {e}")
            else:
                print(f"⏳ Waiting for Redis... ({i+1}/{max_retries})")
                await asyncio.sleep(2)
    
    # Wait for Ollama
    for i in range(max_retries):
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
                response = await client.get(f"{ollama_url}/api/tags", timeout=5.0)
                if response.status_code == 200:
                    print("✓ Ollama connection successful")
                    break
        except Exception as e:
            if i == max_retries - 1:
                print(f"⚠️  Ollama connection failed after {max_retries} attempts: {e}")
            else:
                print(f"⏳ Waiting for Ollama... ({i+1}/{max_retries})")
                await asyncio.sleep(2)


async def initialize_system():
    """Initialize the multi-agent system"""
    try:
        from src.config.settings import get_settings
        settings = get_settings()
        
        print("🤖 Initializing Multi-Agent System...")
        
        # Initialize MCP system
        try:
            from src.mcp.manager import get_mcp_manager
            mcp_manager = get_mcp_manager()
            await mcp_manager.initialize()
            print("✓ MCP system initialized")
        except Exception as e:
            print(f"⚠️  MCP initialization failed: {e}")
        
        # Initialize observability
        try:
            from src.observability import initialize_observability
            await initialize_observability(
                langsmith_api_key=settings.langsmith_api_key,
                project_name=settings.langsmith_project,
                environment=settings.environment
            )
            print("✓ Observability system initialized")
        except Exception as e:
            print(f"⚠️  Observability initialization failed: {e}")
        
        print("✅ System initialization complete")
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        sys.exit(1)


async def setup_development_environment():
    """Setup complete development environment"""
    print("🚀 Setting up Multi-Agent System...")
    
    # Basic setup
    create_directories()
    setup_logging()
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Missing critical dependencies. Run: uv sync")
        sys.exit(1)
    
    # Wait for services in Docker
    if check_environment():
        await wait_for_services()
    
    # Initialize system
    await initialize_system()
    
    # Environment-specific messages
    if check_environment():
        print("🐳 Docker environment ready!")
        print("📡 API available at: http://0.0.0.0:8000")
        print("📚 Documentation: http://0.0.0.0:8000/docs")
        print("❤️  Health check: http://0.0.0.0:8000/health")
    else:
        print("💻 Development environment ready!")
        print("📡 API available at: http://localhost:8000")
        print("📚 Documentation: http://localhost:8000/docs")
        print("❤️  Health check: http://localhost:8000/health")
        print("🔧 Start with: uv run uvicorn src.main:app --reload")


def main():
    """Main entry point"""
    try:
        asyncio.run(setup_development_environment())
    except KeyboardInterrupt:
        print("\n👋 Setup interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()