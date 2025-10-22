"""
Main API router that includes all route modules
"""
from fastapi import APIRouter

from src.api.v1.agent_routes import router as agents_router
from src.api.v1.models import router as models_router
from src.api.v1.health import router as health_router
from src.api.v1.mcp import router as mcp_router

# Create main API router
api_router = APIRouter()

# Include v1 routes
v1_router = APIRouter(prefix="/v1")
v1_router.include_router(agents_router, prefix="/agents", tags=["agents"])
v1_router.include_router(models_router, prefix="/models", tags=["models"])
v1_router.include_router(health_router, prefix="/health", tags=["health"])
v1_router.include_router(mcp_router, prefix="/mcp", tags=["mcp"])

# Include v1 router in main API router
api_router.include_router(v1_router)