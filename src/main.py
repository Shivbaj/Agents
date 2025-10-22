"""
Main FastAPI application entry point
"""
import os
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.api.routes import api_router
from src.config.settings import get_settings
from src.core.exceptions import setup_exception_handlers
from src.core.logging import setup_logging
from src.core.middleware import setup_middleware
from src.agents.registry.manager import AgentManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting Multi-Agent System...")
    
    # Initialize observability first
    try:
        from src.observability import initialize_observability
        await initialize_observability(
            project_name="multi-agent-system",
            environment=os.getenv("ENVIRONMENT", "development")
        )
        logger.info("✓ Observability system initialized")
    except Exception as e:
        logger.warning(f"Observability initialization failed (continuing without): {e}")
    
    # Initialize MCP manager
    try:
        from src.mcp.manager import get_mcp_manager
        mcp_manager = get_mcp_manager()
        await mcp_manager.initialize()
        app.state.mcp_manager = mcp_manager
        logger.info("✓ MCP manager initialized")
        
        # Register default MCP servers
        from src.mcp.servers.web_search import WebSearchServer
        web_server = WebSearchServer()
        await mcp_manager.register_server(web_server)
        logger.info("✓ Default MCP servers registered")
        
    except Exception as e:
        logger.warning(f"MCP system initialization failed (continuing without): {e}")
    
    # Initialize agent registry
    agent_registry = AgentManager()
    await agent_registry.initialize()
    app.state.agent_registry = agent_registry
    
    # Load initial agents
    await agent_registry.discover_and_load_agents()
    logger.info(f"✓ Loaded {len(agent_registry.list_agents())} agents")
    
    # Health check for external services
    await _check_external_services()
    
    logger.info("🚀 Multi-Agent System startup complete!")
    
    # Yield control to the application
    yield
    
    # Shutdown (when the application stops)
    logger.info("🛑 Multi-Agent System shutting down...")
    
    # Cleanup resources
    try:
        if hasattr(app.state, 'mcp_manager'):
            await app.state.mcp_manager.cleanup()
        logger.info("✓ Cleanup complete")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


async def _check_external_services():
    """Check connectivity to external services"""
    settings = get_settings()
    
    # Check Redis connection
    try:
        import redis.asyncio as redis
        redis_client = redis.from_url(settings.redis_url)
        await redis_client.ping()
        logger.info("✓ Redis connection healthy")
        await redis_client.close()
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")
    
    # Check Ollama connection
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                logger.info("✓ Ollama connection healthy")
            else:
                logger.warning(f"⚠️ Ollama returned status {response.status_code}")
    except Exception as e:
        logger.warning(f"⚠️ Ollama connection failed: {e}")
    
    # Check model providers
    if settings.openai_api_key:
        logger.info("✓ OpenAI API key configured")
    else:
        logger.warning("⚠️ OpenAI API key not configured")
        
    if settings.anthropic_api_key:
        logger.info("✓ Anthropic API key configured")
    else:
        logger.warning("⚠️ Anthropic API key not configured")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    # Setup logging (force text format to avoid JSON issues)
    setup_logging(settings.log_level, "text")
    
    app = FastAPI(
        title=settings.api_title,
        description="A comprehensive multi-agent system with LLM integration",
        version=settings.api_version,
        debug=settings.debug,
        lifespan=lifespan,
    )
    
    # Setup CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Setup custom middleware
    setup_middleware(app)
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Include API routes
    app.include_router(api_router, prefix="/api")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "version": settings.api_version,
            "environment": settings.environment,
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information"""
        return {
            "message": "Multi-Agent System API",
            "version": settings.api_version,
            "docs_url": "/docs",
            "health_url": "/health",
        }
    
    return app


# Create the FastAPI application instance
app = create_app()


def main():
    """Main entry point for CLI"""
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()