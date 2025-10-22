"""
Custom middleware for the multi-agent system
"""
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from loguru import logger


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """Log request and response information"""
    start_time = time.time()
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else None,
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(
        f"Response: {response.status_code} in {process_time:.4f}s",
        extra={
            "status_code": response.status_code,
            "process_time": process_time,
        }
    )
    
    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    """Basic rate limiting middleware"""
    # TODO: Implement proper rate limiting with Redis
    # For now, just pass through
    return await call_next(request)


async def security_middleware(request: Request, call_next: Callable) -> Response:
    """Security middleware"""
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


def setup_middleware(app: FastAPI) -> None:
    """Setup custom middleware"""
    
    app.middleware("http")(logging_middleware)
    app.middleware("http")(security_middleware)
    app.middleware("http")(rate_limit_middleware)