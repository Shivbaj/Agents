# Multi-stage Dockerfile for Multi-Agent System

# Base stage with common dependencies
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_SYSTEM_PYTHON=1
ENV DOCKER_ENV=true
ENV PATH="/root/.local/bin:$PATH"

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv package manager using pip for better reliability
RUN pip install uv && \
    uv --version

# Set work directory
WORKDIR /app

# Development stage
FROM base AS development

# Copy dependency files and README for better layer caching
COPY pyproject.toml uv.lock* README.md ./

# Install dependencies with timeout and caching optimizations
ENV UV_HTTP_TIMEOUT=120
ENV UV_CACHE_DIR=/tmp/uv-cache
RUN --mount=type=cache,target=/tmp/uv-cache \
    uv sync --frozen

# Copy application code
COPY . .

# Create directories
RUN mkdir -p logs data/uploads data/models data/cache

# Make scripts executable
RUN chmod +x scripts/dev_setup.py docker-entrypoint.sh

# Expose port
EXPOSE 8000

# Development command with hot reload
CMD ["uv", "run", "uvicorn", "src.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]

# Production stage
FROM base AS production

# Copy dependency files and README for better layer caching
COPY pyproject.toml uv.lock* README.md ./

# Install only production dependencies with optimizations  
ENV UV_HTTP_TIMEOUT=120
ENV UV_CACHE_DIR=/tmp/uv-cache
RUN --mount=type=cache,target=/tmp/uv-cache \
    uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p logs data/uploads data/models data/cache && \
    chmod 755 logs data && \
    chmod 777 data/uploads data/models data/cache

# Make scripts executable
RUN chmod +x scripts/dev_setup.py docker-entrypoint.sh

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Initialize the application (non-critical) - set build phase flag
RUN DOCKER_BUILD_PHASE=true uv run python scripts/dev_setup.py || true

# Create a non-root user for security and set up environment
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app && \
    echo 'export PATH="/root/.local/bin:$PATH"' >> /home/app/.bashrc

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint and default command
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD []

# Default stage is production
FROM production