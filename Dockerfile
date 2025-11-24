# Multi-stage build for optimized production image
# Stage 1: Builder
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=TeamMoa.settings.prod

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    curl \
    cron \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create app user (non-root for security)
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R appuser:appuser /app && \
    touch /var/log/cron.log && \
    chown appuser:appuser /var/log/cron.log

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Copy crontab file and setup
# /etc/cron.d/ 파일은 cron 데몬이 자동으로 읽음
COPY deploy/crontab /etc/cron.d/django-tasks
RUN chmod 0644 /etc/cron.d/django-tasks

# Set execute permission for entrypoint script
RUN chmod +x /app/deploy/entrypoint.sh

# Note: USER appuser는 entrypoint.sh에서 처리
# entrypoint가 cron을 시작한 후 Django는 appuser로 실행

# Collect static files (will be run in entrypoint, but can pre-collect here)
# RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Use entrypoint script
ENTRYPOINT ["/app/deploy/entrypoint.sh"]

# Default command (can be overridden)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "TeamMoa.asgi:application"]
