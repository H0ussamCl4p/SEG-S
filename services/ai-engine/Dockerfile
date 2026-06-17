# ==========================================
# AI Engine Dockerfile (Speed Optimized)
# Target: <10s incremental, <60s clean build
# ==========================================

# Use slim (not alpine) - has pre-built wheels
FROM python:3.10-slim AS base

# Single layer for system deps (rarely changes)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl libgomp1 && \
    rm -rf /var/lib/apt/lists/*

# Dependency installation stage
FROM base AS deps
WORKDIR /app

# Copy only requirements (changes rarely = better cache)
COPY requirements-base.txt requirements-app.txt ./

# Use BuildKit cache mount for pip - MASSIVE speedup
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --default-timeout=1000 --no-compile -r requirements-base.txt -r requirements-app.txt

# Final runtime stage
FROM base
WORKDIR /app

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ /app/src/

# Bake static AI assets into the image so the service is self-contained in the
# cloud (no bind mounts there). Locally, docker-compose bind-mounts ./data and
# ./models over these, so dev behavior is unchanged.
#   - models/: tracked metadata + registry (pretrained .pkl are gitignored, as on the VPS)
#   - data/:   default manuals, training_data.csv, column_mapping.json
COPY models/ /app/models/
COPY data/ /app/data/

# Writable runtime dirs. In the cloud an Azure Files share is mounted at
# /app/persist and CHROMA_PERSIST_DIR points there, so the vector index survives
# restarts (manuals aren't re-embedded on every cold start).
RUN mkdir -p /app/logs /app/persist

# Create Supervisord configuration
RUN echo '[supervisord]' > /etc/supervisord.conf && \
    echo 'nodaemon=true' >> /etc/supervisord.conf && \
    echo 'user=root' >> /etc/supervisord.conf && \
    echo 'logfile=/app/logs/supervisord.log' >> /etc/supervisord.conf && \
    echo '' >> /etc/supervisord.conf && \
    echo '[program:fastapi]' >> /etc/supervisord.conf && \
    echo 'command=uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload' >> /etc/supervisord.conf && \
    echo 'directory=/app' >> /etc/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisord.conf && \
    echo 'stderr_logfile=/app/logs/fastapi.err.log' >> /etc/supervisord.conf && \
    echo 'stdout_logfile=/app/logs/fastapi.out.log' >> /etc/supervisord.conf && \
    echo '' >> /etc/supervisord.conf && \
    echo '[program:ai_consumer]' >> /etc/supervisord.conf && \
    echo 'command=python src/main.py' >> /etc/supervisord.conf && \
    echo 'directory=/app' >> /etc/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisord.conf && \
    echo 'stderr_logfile=/app/logs/ai_consumer.err.log' >> /etc/supervisord.conf && \
    echo 'stdout_logfile=/app/logs/ai_consumer.out.log' >> /etc/supervisord.conf

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run Supervisord
CMD ["/usr/local/bin/supervisord", "-c", "/etc/supervisord.conf"]
