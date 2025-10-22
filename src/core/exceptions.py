"""
Custom exceptions for the multi-agent system
"""
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from loguru import logger


class AgentSystemException(Exception):
    """Base exception for agent system"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class AgentNotFoundException(AgentSystemException):
    """Exception raised when an agent is not found"""
    
    def __init__(self, agent_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Agent '{agent_id}' not found"
        super().__init__(
            message=message,
            details=details,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class AgentExecutionException(AgentSystemException):
    """Exception raised when agent execution fails"""
    
    def __init__(self, agent_id: str, error: str, details: Optional[Dict[str, Any]] = None):
        message = f"Agent '{agent_id}' execution failed: {error}"
        super().__init__(
            message=message,
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ModelProviderException(AgentSystemException):
    """Exception raised when model provider fails"""
    
    def __init__(self, provider: str, error: str, details: Optional[Dict[str, Any]] = None):
        message = f"Model provider '{provider}' error: {error}"
        super().__init__(
            message=message,
            details=details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class ValidationException(AgentSystemException):
    """Exception raised for validation errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details=details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class RateLimitException(AgentSystemException):
    """Exception raised when rate limit is exceeded"""
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        message = "Rate limit exceeded"
        super().__init__(
            message=message,
            details=details,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class AuthenticationException(AgentSystemException):
    """Exception raised for authentication errors"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


# Exception handlers
async def agent_system_exception_handler(request: Request, exc: AgentSystemException):
    """Handle AgentSystemException"""
    logger.error(f"AgentSystemException: {exc.message}", extra=exc.details)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
            "type": exc.__class__.__name__,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException"""
    logger.warning(f"HTTPException: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "type": "HTTPException",
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "type": "InternalServerError",
        },
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup exception handlers for FastAPI app"""
    
    app.add_exception_handler(AgentSystemException, agent_system_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)