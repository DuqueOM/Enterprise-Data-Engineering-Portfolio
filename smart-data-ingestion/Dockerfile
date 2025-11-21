# ============================================================================
# Smart Data Ingestion - Production Dockerfile
# Multi-stage build for optimized image size and security
# ============================================================================

# ===== Stage 1: Builder =====
FROM python:3.10.13-slim-bullseye AS builder

# Build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=1.0.0

# Labels (OCI annotations)
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.authors="Portfolio Team" \
      org.opencontainers.image.url="https://github.com/yourusername/portfolio" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.title="Smart Data Ingestion" \
      org.opencontainers.image.description="Production-grade web scraping and data ingestion system"

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r /tmp/requirements.txt && \
    pip install playwright && \
    playwright install chromium --with-deps

# ===== Stage 2: Runtime =====
FROM python:3.10.13-slim-bullseye AS runtime

# Runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app \
    APP_USER=appuser \
    APP_UID=1000 \
    APP_GID=1000

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    curl \
    ca-certificates \
    # Playwright dependencies (minimal)
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g ${APP_GID} ${APP_USER} && \
    useradd -u ${APP_UID} -g ${APP_GID} -m -s /bin/bash ${APP_USER}

# Copy virtual environment from builder
COPY --from=builder --chown=${APP_USER}:${APP_USER} /opt/venv /opt/venv

# Copy Playwright browsers from builder
COPY --from=builder --chown=${APP_USER}:${APP_USER} /root/.cache/ms-playwright /home/${APP_USER}/.cache/ms-playwright

# Set working directory
WORKDIR ${APP_HOME}

# Copy application code
COPY --chown=${APP_USER}:${APP_USER} scripts/ ${APP_HOME}/scripts/
COPY --chown=${APP_USER}:${APP_USER} tests/ ${APP_HOME}/tests/
COPY --chown=${APP_USER}:${APP_USER} pytest.ini ${APP_HOME}/

# Create data directories
RUN mkdir -p ${APP_HOME}/data/raw ${APP_HOME}/data/processed && \
    chown -R ${APP_USER}:${APP_USER} ${APP_HOME}/data

# Switch to non-root user
USER ${APP_USER}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
ENTRYPOINT ["python", "-m"]
CMD ["scripts.ingest", "--help"]

# ===== Stage 3: Development (optional) =====
FROM runtime AS development

USER root

# Install development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN /opt/venv/bin/pip install \
    ipython==8.18.1 \
    ipdb==0.13.13 \
    jupyter==1.0.0

USER ${APP_USER}

# Development command (Jupyter for exploration)
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
