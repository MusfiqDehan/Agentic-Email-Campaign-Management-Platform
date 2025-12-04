# Docker Setup Guide - Email Campaign Management Platform

## Overview

This guide explains how to run the Django backend application using Docker with PostgreSQL, Redis, Celery workers, and Celery Beat scheduler.

## Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 1.29+)

## Project Structure

```
backend/
├── Dockerfile                 # Multi-stage build (development & production)
├── docker-compose.yml         # Development docker-compose setup
├── .env.example              # Environment variables template
├── .env.local                # Local environment (copy from .env.example)
├── requirements.txt          # Python dependencies
├── manage.py                 # Django management script
├── project_config/           # Django settings
├── apps/                     # Django applications
│   ├── authentication/
│   ├── campaigns/
│   └── utils/
└── ...
```

## Setup Instructions

### 1. Clone the Repository

```bash
cd /path/to/Email-Campaign-Management-Platform
cd backend
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env.local

# Edit .env.local with your specific values
nano .env.local  # or use your favorite editor
```

**Important environment variables:**
- `SECRET_KEY`: Change this in production!
- `DEBUG`: Set to `False` in production
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `CELERY_BROKER_URL`: Celery broker (Redis)
- `CELERY_RESULT_BACKEND`: Celery results backend (Redis)

### 3. Build and Start Services

#### Option A: Development Mode (with live code reload)

```bash
# Build images and start services
docker-compose up --build

# In a new terminal, create superuser (one-time)
docker-compose exec app python manage.py createsuperuser

# Create platform admin user
docker-compose exec app python manage.py create_platform_admin admin@example.com --create --password SecurePass123! --staff
```

#### Option B: Production Mode

```bash
# Build production image
docker build --target production -t email-platform:latest .

# Run with docker-compose (production)
docker-compose -f docker-compose.yml up -d
```

### 4. Access the Application

- **Django API**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
- **Health Check**: http://localhost:8000/api/v1/campaigns/health/

### 5. Common Docker Compose Commands

```bash
# View logs
docker-compose logs -f app              # Django app logs
docker-compose logs -f celery           # Celery worker logs
docker-compose logs -f celery-beat      # Celery Beat logs
docker-compose logs -f postgres         # Database logs

# Run Django management commands
docker-compose exec app python manage.py migrate
docker-compose exec app python manage.py makemigrations
docker-compose exec app python manage.py createsuperuser
docker-compose exec app python manage.py create_platform_admin <email> --create --password <pwd>

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Rebuild specific service
docker-compose build --no-cache app
docker-compose up app
```

## Service Details

### 1. PostgreSQL Database

- **Image**: postgres:16-alpine
- **Container Name**: email-platform-db
- **Port**: 5432 (exposed on host)
- **Volumes**: postgres_data (persisted)
- **Healthcheck**: Every 10s

**Credentials** (from .env.local):
- User: `postgres`
- Password: `postgres`
- Database: `email_campaign_db`

### 2. Redis Cache

- **Image**: redis:7-alpine
- **Container Name**: email-platform-redis
- **Port**: 6379 (exposed on host)
- **Volumes**: redis_data (persisted)
- **Password**: (configured in .env.local)

**Used for:**
- Celery broker
- Django cache
- Session storage

### 3. Django App

- **Container Name**: email-platform-app
- **Port**: 8000 (exposed on host)
- **Command**: `python manage.py migrate && python manage.py runserver 0.0.0.0:8000`
- **Volumes**: 
  - Mount current directory (live code reload)
  - `stdin_open: true` (interactive shell)
  - `tty: true` (TTY allocation)

**Depends on**: PostgreSQL, Redis

### 4. Celery Worker

- **Container Name**: email-platform-celery
- **Command**: `celery -A project_config worker -l info`
- **Role**: Processes async tasks (email sending, campaign dispatch)

**Depends on**: PostgreSQL, Redis

### 5. Celery Beat

- **Container Name**: email-platform-celery-beat
- **Command**: `celery -A project_config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler`
- **Role**: Schedules periodic tasks (check scheduled campaigns, health checks)

**Depends on**: PostgreSQL, Redis

## Dockerfile Explanation

### Multi-Stage Build

The Dockerfile uses multi-stage builds to create two distinct images:

#### Base Stage
- Installs Python 3.13-slim
- Installs system dependencies (build tools, PostgreSQL client)
- Installs `uv` package manager (faster than pip)
- Creates non-root `appuser` (security best practice)

#### Development Stage
```dockerfile
FROM base AS development
RUN uv pip install --system -r requirements.txt
COPY --chown=appuser:appuser . .
USER appuser
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

**Advantages:**
- All dependencies installed (including dev tools)
- Live code reload via volume mount
- Smaller base image (slim variant)
- Faster installation with `uv`

#### Production Stage
```dockerfile
FROM base AS production
RUN uv pip install --system -r requirements.txt && \
    uv pip install --system gunicorn==21.2.0
COPY --chown=appuser:appuser . .
RUN mkdir -p /app/staticfiles /app/media
RUN python manage.py collectstatic --noinput
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", ...]
```

**Advantages:**
- Runs with `gunicorn` (production WSGI server)
- Collects static files
- Non-root user (security)
- Health check configured
- Optimized for performance (multiple workers)

### Using uv for Faster Installation

The Dockerfile uses `uv` instead of `pip`:

```dockerfile
# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies with uv (much faster)
RUN uv pip install --system -r requirements.txt
```

**Benefits of uv:**
- 10-100x faster than pip
- Parallel downloads
- Better dependency resolution
- Smaller image footprint
- Instant resolution caching

## Useful Commands

### Development Workflow

```bash
# Start all services
docker-compose up

# Watch logs
docker-compose logs -f

# Run migrations
docker-compose exec app python manage.py migrate

# Create superuser
docker-compose exec app python manage.py createsuperuser

# Create platform admin
docker-compose exec app python manage.py create_platform_admin admin@example.com --create --password SecurePass123!

# Django shell
docker-compose exec app python manage.py shell

# Run tests
docker-compose exec app pytest

# Code formatting
docker-compose exec app black .
docker-compose exec app isort .

# Linting
docker-compose exec app flake8 .
```

### Database Management

```bash
# Create database backup
docker-compose exec postgres pg_dump -U postgres email_campaign_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres email_campaign_db < backup.sql

# Connect to PostgreSQL CLI
docker-compose exec postgres psql -U postgres email_campaign_db
```

### Celery Management

```bash
# View active Celery workers
docker-compose exec celery celery -A project_config inspect active

# View pending tasks
docker-compose exec celery celery -A project_config inspect scheduled

# Purge all tasks
docker-compose exec celery celery -A project_config purge
```

### Production Deployment

```bash
# Build production image
docker build --target production -t email-platform:v1.0 .

# Tag for registry
docker tag email-platform:v1.0 myregistry.azurecr.io/email-platform:v1.0

# Push to registry
docker push myregistry.azurecr.io/email-platform:v1.0

# Run on production server
docker run -d \
  --name email-platform \
  --env-file .env.prod \
  -p 8000:8000 \
  myregistry.azurecr.io/email-platform:v1.0
```

## Troubleshooting

### Issue: Database connection refused

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
docker-compose exec app python manage.py migrate
```

### Issue: Redis connection error

```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Restart Redis
docker-compose restart redis
```

### Issue: Celery tasks not processing

```bash
# Check Celery worker logs
docker-compose logs celery

# View active tasks
docker-compose exec celery celery -A project_config inspect active

# Restart Celery worker
docker-compose restart celery
```

### Issue: Static files not found in production

```bash
# Collect static files
docker-compose exec app python manage.py collectstatic --noinput

# Check staticfiles directory
docker-compose exec app ls -la /app/staticfiles
```

### Issue: Port already in use

```bash
# Change port in docker-compose.yml or .env.local
# Example: change APP_PORT from 8000 to 8001

# Or kill the process using the port
lsof -i :8000
kill -9 <PID>
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `True` | Django debug mode |
| `SECRET_KEY` | (required) | Django secret key |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed hostnames |
| `DATABASE_URL` | (required) | PostgreSQL connection |
| `REDIS_URL` | (required) | Redis connection |
| `CELERY_BROKER_URL` | (required) | Celery broker |
| `CELERY_RESULT_BACKEND` | (required) | Celery results |
| `APP_PORT` | `8000` | Django app port |
| `DB_PORT` | `5432` | PostgreSQL port |
| `REDIS_PORT` | `6379` | Redis port |

## Performance Tuning

### Gunicorn Workers

In `Dockerfile` production stage:
```dockerfile
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4",           # Increase for high load
     "--worker-class", "sync",   # Or "gevent" for I/O heavy
     "--max-requests", "1000",   # Restart after N requests
     "--timeout", "60",          # Request timeout
     ...]
```

**Worker formula**: `(2 × CPU cores) + 1`
- 2 cores = 5 workers
- 4 cores = 9 workers

### Celery Concurrency

To change Celery worker concurrency, modify `docker-compose.yml`:
```bash
command: celery -A project_config worker -l info --concurrency=8
```

### Database Connection Pooling

Update `project_config/settings/production.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 600,  # Connection pooling timeout
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

## Next Steps

1. **Configure Email Provider**: Set up AWS SES or SMTP credentials in `.env.local`
2. **Create Admin User**: Run `docker-compose exec app python manage.py createsuperuser`
3. **Create Platform Admin**: Run `docker-compose exec app python manage.py create_platform_admin <email> --create --password <pwd>`
4. **Access Admin Dashboard**: Navigate to http://localhost:8000/admin
5. **Create Email Provider**: Add a shared email provider via admin panel
6. **Start Sending Campaigns**: Use the API to create campaigns

## Support

For issues, check the logs:
```bash
# View all logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f <service-name>
```
