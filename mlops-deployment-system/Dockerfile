# ============================================================================
# MLOps Deployment System - Production Dockerfile
# Multi-stage build with FastAPI optimization
# ============================================================================

# ===== Stage 1: Builder =====
FROM python:3.10.13-slim-bullseye AS builder

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=1.0.0

LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.authors="Portfolio Team" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.title="MLOps Deployment System" \
      org.opencontainers.image.description="Production ML model serving with monitoring"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r /tmp/requirements.txt

# ===== Stage 2: Runtime =====
FROM python:3.10.13-slim-bullseye AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app \
    APP_USER=mlops \
    APP_UID=1000 \
    APP_GID=1000 \
    PORT=8080 \
    WORKERS=4 \
    TIMEOUT=120

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g ${APP_GID} ${APP_USER} && \
    useradd -u ${APP_UID} -g ${APP_GID} -m -s /bin/bash ${APP_USER}

# Copy virtual environment from builder
COPY --from=builder --chown=${APP_USER}:${APP_USER} /opt/venv /opt/venv

# Set working directory
WORKDIR ${APP_HOME}

# Copy application code
COPY --chown=${APP_USER}:${APP_USER} space/ ${APP_HOME}/space/
COPY --chown=${APP_USER}:${APP_USER} scripts/ ${APP_HOME}/scripts/
COPY --chown=${APP_USER}:${APP_USER} train.py ${APP_HOME}/
COPY --chown=${APP_USER}:${APP_USER} drift_detector.py ${APP_HOME}/
COPY --chown=${APP_USER}:${APP_USER} flow_retrain.py ${APP_HOME}/

# Create necessary directories
RUN mkdir -p ${APP_HOME}/artifacts ${APP_HOME}/logs ${APP_HOME}/data && \
    chown -R ${APP_USER}:${APP_USER} ${APP_HOME}

# Switch to non-root user
USER ${APP_USER}

# Expose port
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Use gunicorn with uvicorn workers for production
CMD ["sh", "-c", "gunicorn space.app:app \
    --bind 0.0.0.0:${PORT} \
    --workers ${WORKERS} \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout ${TIMEOUT} \
    --access-logfile - \
    --error-logfile - \
    --log-level info"]

# ===== Stage 3: Development =====
FROM runtime AS development

USER root

# Install development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

RUN /opt/venv/bin/pip install \
    ipython==8.18.1 \
    ipdb==0.13.13 \
    jupyter==1.0.0

USER ${APP_USER}

# Development uses uvicorn with reload
CMD ["uvicorn", "space.app:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
