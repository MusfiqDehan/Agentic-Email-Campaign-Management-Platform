# Multi-stage Dockerfile for Email Campaign Management Platform
FROM python:3.13-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy requirements
COPY backend/requirements.txt requirements.txt

# Development stage
FROM base AS development
RUN pip install --no-cache-dir -r requirements.txt
USER appuser
CMD ["python", "manage.py", "runserver", "0.0.0.0:8800"]

# Production stage
FROM base AS production
RUN pip install --no-cache-dir -r requirements/prod.txt

# Copy backend application code
COPY --chown=appuser:appuser backend/ .

# Create directories for static/media files
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R appuser:appuser /app/staticfiles /app/media

USER appuser

# Collect static files
RUN python manage.py collectstatic --noinput

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/admin/login/ || exit 1

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8800", "--workers", "3", "project_config.wsgi:application"]