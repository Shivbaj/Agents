# Multi-stage Dockerfile for Multi-Agent System

# Base stage with common dependencies
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_SYSTEM_PYTHON=1
ENV DOCKER_ENV=true
ENV PATH="/root/.local/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Set work directory
WORKDIR /app

# Development stage
FROM base AS development

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock* ./

# Install all dependencies including dev dependencies
RUN uv sync --frozen

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

# Copy dependency files first for better caching
COPY pyproject.toml ./
COPY uv.lock* ./

# Install only production dependencies
RUN uv sync --frozen --no-dev

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

# Initialize the application (non-critical)
RUN uv run python scripts/dev_setup.py || true

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default stage is production
FROM production