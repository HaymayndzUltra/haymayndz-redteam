# EvilPanel Dockerfile
# Source: plan-aligned-implementation-protocol.md Task 5.1
# OPSEC: Minimal image, no unnecessary packages

FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    certbot \
    openssl \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for OPSEC
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p \
    /app/data \
    /app/logs \
    /app/certs \
    /app/evilpanel/phishlets/custom \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose ports
# 443 - HTTPS proxy
# 8080 - Dashboard API
EXPOSE 443 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Default command
CMD ["uvicorn", "evilpanel.dashboard.api.main:app", "--host", "0.0.0.0", "--port", "8080"]

