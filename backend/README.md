# Backend Docker & Deployment Documentation

Complete Docker containerization and production deployment guide for the Email Campaign Management Platform backend.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [File Guide](#file-guide)
- [Docker Setup](#docker-setup)
- [Development](#development)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)

---

## 🚀 Quick Start

### Development Setup (Local)

```bash
# 1. Clone and navigate
cd backend

# 2. Build and start services
bash docker-quickstart.sh dev

# 3. Follow the prompts
# The script will create credentials and display URLs
```

**What happens:**
- Creates `.env.local` from template
- Builds Docker images
- Starts all services (PostgreSQL, Redis, Django, Celery, Celery Beat)
- Runs migrations
- Creates superuser and platform admin
- Displays credentials and next steps

**Access:**
- API: `http://localhost:8000/api/v1/`
- Admin: `http://localhost:8000/admin/`
- Credentials printed after setup

### Production Deployment

```bash
# 1. Prepare server (see PRODUCTION_DEPLOYMENT.md Step 1)

# 2. Clone repository and configure
cd /opt/email-platform/backend

# 3. Copy and edit production environment
cp .env.production .env.production.local
nano .env.production.local

# 4. Deploy
bash deploy.sh --branch production --force

# Or deploy specific version
bash deploy.sh --tag v1.2.0
```

---

## 📁 File Guide

### Core Docker Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build for development & production |
| `docker-compose.yml` | Local development setup (5 services) |
| `docker-compose.prod.yml` | Production setup with optimizations |
| `.env.example` | Development environment template |
| `.env.production` | Production environment template |

### Documentation Files

| File | Purpose |
|------|---------|
| `DOCKER_SETUP.md` | Comprehensive Docker guide for development |
| `PRODUCTION_DEPLOYMENT.md` | Production deployment procedures (600+ lines) |
| `README.md` | This file - Overview and quick reference |

### Configuration Files

| File | Purpose |
|------|---------|
| `nginx.conf` | Nginx reverse proxy configuration |
| `docker-quickstart.sh` | Automated local setup script |
| `deploy.sh` | Production deployment script |

---

## 🐳 Docker Setup

### Understanding the Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Client Applications                │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/HTTPS
┌────────────────────▼────────────────────────────────┐
│          Nginx (Reverse Proxy/SSL)                  │
│  - SSL/TLS termination                             │
│  - Load balancing                                  │
│  - Static file serving                             │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│      Django Application (Gunicorn/Runserver)        │
│  - REST API endpoints                              │
│  - Business logic                                  │
│  - Session management                              │
└─┬──────────────────────────────────┬────────────────┘
  │                                  │
  │ SQL                              │ Cache/Broker
  ▼                                  ▼
┌──────────────────┐        ┌──────────────────┐
│  PostgreSQL 16   │        │   Redis 7        │
│  - Data Storage  │        │  - Caching       │
│  - Persistence   │        │  - Celery Broker │
└──────────────────┘        └────────┬─────────┘
                                    │
                          ┌─────────┴────────────┐
                          │                      │
                     ┌────▼────┐         ┌──────▼────┐
                     │  Celery  │         │ Celery    │
                     │  Worker  │         │ Beat      │
                     │ (Tasks)  │         │(Scheduler)│
                     └──────────┘         └───────────┘
```

### Services Overview

**Development (docker-compose.yml):**
- **postgres**: PostgreSQL 16 with live data persistence
- **redis**: Redis 7 for caching and Celery
- **app**: Django dev server with auto-reload
- **celery**: Async task worker
- **celery-beat**: Periodic task scheduler

**Production (docker-compose.prod.yml):**
- Same services with optimization flags
- Gunicorn instead of runserver
- Persistent volume management
- Health checks on all services
- Proper restart policies

### ♻ Maintenance Tasks

- `apps.campaigns.tasks.cleanup_old_logs` runs nightly to purge aged delivery logs and terminal queue records so the database does not grow unbounded. Celery Beat already schedules it via `config/celery.py`.
- Control retention windows with `EMAIL_LOG_RETENTION_DAYS` (default `90`) and `EMAIL_QUEUE_RETENTION_DAYS` (default `30`). Tune these per environment to match compliance requirements before deploying.

### Environment Variables

Key production variables:
```bash
# Security
SECRET_KEY=your-64-char-random-key
DEBUG=False

# Database
DB_PASSWORD=strong-random-password
DATABASE_URL=postgresql://user:pass@postgres:5432/db

# Redis
REDIS_PASSWORD=strong-random-password

# Domains
ALLOWED_HOSTS=api.example.com
CSRF_TRUSTED_ORIGINS=https://app.example.com
```

See `.env.example` and `.env.production` for all variables.

---

## 💻 Development

### Starting Development Environment

**Option 1: Automated (Recommended)**
```bash
bash docker-quickstart.sh dev
```

**Option 2: Manual**
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Run migrations
docker-compose exec app python manage.py migrate

# Create users
docker-compose exec app python manage.py createsuperuser
docker-compose exec app python manage.py create_platform_admin admin@test.com --create --staff
```

### Common Development Commands

```bash
# View logs
docker-compose logs -f app
docker-compose logs -f celery
docker-compose logs -f postgres

# Django management
docker-compose exec app python manage.py shell
docker-compose exec app python manage.py makemigrations
docker-compose exec app python manage.py migrate
docker-compose exec app python manage.py createsuperuser

# Database
docker-compose exec postgres psql -U postgres -d email_campaign_db
docker-compose exec postgres pg_dump -U postgres email_campaign_db > backup.sql

# Run tests
docker-compose exec app python manage.py test

# View Celery tasks
docker-compose exec app celery -A config inspect active
docker-compose exec app celery -A config events

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: loses data)
docker-compose down -v
```

### Development Workflow

```bash
# 1. Start services
docker-compose up -d

# 2. Make code changes (auto-reload enabled)
# Edit your Django code, changes reload automatically

# 3. Check migrations
docker-compose exec app python manage.py makemigrations

# 4. Apply migrations
docker-compose exec app python manage.py migrate

# 5. Run tests
docker-compose exec app python manage.py test apps/campaigns

# 6. Debug with shell
docker-compose exec app python manage.py shell

# 7. View logs in real-time
docker-compose logs -f app
```

### Debugging Issues

```bash
# Check if port is in use
sudo lsof -i :8000

# View service health
docker-compose ps

# Inspect service logs
docker-compose logs app

# Check service configuration
docker-compose config

# Execute command in container
docker-compose exec app bash
docker-compose exec postgres psql -U postgres
```

---

## 🚀 Production Deployment

### Pre-Deployment Checklist

- [ ] All environment variables set securely
- [ ] SSL certificates obtained (Let's Encrypt)
- [ ] Database backups configured
- [ ] Monitoring tools set up (Sentry, etc.)
- [ ] Firewall configured (22, 80, 443 only)
- [ ] Domain pointed to server
- [ ] Load testing completed
- [ ] Rollback plan documented

### Deployment Process

**Step 1: Initial Setup**
```bash
# SSH to production server
ssh user@production-server

# See PRODUCTION_DEPLOYMENT.md Steps 1-3
mkdir -p /opt/email-platform
cd /opt/email-platform

# Clone repository
git clone https://github.com/yourorg/email-platform.git .
cd backend

# Configure environment
cp .env.production .env.production.local
# Edit with strong passwords and domain-specific values
```

**Step 2: Deploy**
```bash
# Automated deployment with checks and rollback support
bash deploy.sh --branch production --force

# Or specific version
bash deploy.sh --tag v1.2.0

# Or dry-run to test
bash deploy.sh --dry-run
```

**Step 3: Verify**
```bash
# Check services
docker-compose -f docker-compose.prod.yml ps

# Test API
curl https://api.example.com/api/v1/campaigns/health/

# View logs
docker-compose -f docker-compose.prod.yml logs -f app
```

### Deployment Script Features

The `deploy.sh` script provides:
- ✅ Pre-flight checks (Docker, disk space, permissions)
- ✅ Automatic database backups
- ✅ Code updates from git
- ✅ Docker image builds
- ✅ Graceful service shutdown
- ✅ Database migrations
- ✅ Health checks
- ✅ Automatic cleanup
- ✅ Rollback on failure
- ✅ Detailed logging

### Manual Deployment (If Needed)

```bash
# 1. Update code
git fetch origin
git checkout production
git pull origin production

# 2. Build images
docker-compose -f docker-compose.prod.yml build

# 3. Run migrations (backup first!)
docker-compose -f docker-compose.prod.yml exec app python manage.py migrate

# 4. Stop services
docker-compose -f docker-compose.prod.yml stop -t 30

# 5. Start services
docker-compose -f docker-compose.prod.yml up -d

# 6. Verify
docker-compose -f docker-compose.prod.yml ps
curl https://api.example.com/api/v1/campaigns/health/
```

---

## 🔧 Dockerfile Overview

### Multi-Stage Build

The `Dockerfile` uses multi-stage builds for efficiency:

**Stage 1: Base**
- Python 3.13-slim image
- System dependencies
- uv package manager installation
- Non-root user setup

**Stage 2: Development**
- Builds from base
- Full dependencies (dev + prod)
- Django runserver
- Auto-reload enabled
- Used for local development

**Stage 3: Production**
- Builds from base
- Production dependencies only
- Gunicorn (4 workers)
- Static file collection
- Health checks
- Optimized for production

### Key Features

```dockerfile
# Fast package installation with uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN uv pip install --system -r requirements.txt

# Non-root user for security
RUN useradd -m -u 1000 appuser

# Health checks
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/campaigns/health/ || exit 1

# Proper signal handling
ENTRYPOINT ["dumb-init", "--"]
```

---

## 📊 Monitoring & Maintenance

### Health Checks

All services have health checks:
```bash
# View health status
docker-compose ps

# Manual health check
curl http://localhost:8000/api/v1/campaigns/health/
```

### Logs

```bash
# Real-time logs
docker-compose logs -f

# Specific service
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail 100

# Follow specific time period
docker-compose logs --since 1h
```

### Database Maintenance

```bash
# Backup
docker-compose exec postgres pg_dump -U postgres email_campaign_db | gzip > backup.sql.gz

# Restore
zcat backup.sql.gz | docker-compose exec -T postgres psql -U postgres

# Check database size
docker-compose exec postgres psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('email_campaign_db'));"
```

### Performance Optimization

```bash
# Monitor container resources
docker stats

# Clear unused containers/images
docker system prune -a

# Check disk usage
du -sh /var/lib/docker/

# Optimize PostgreSQL
docker-compose exec postgres psql -U postgres -c "VACUUM ANALYZE;"
```

---

## ❌ Troubleshooting

### Port Already in Use

```bash
# Find what's using port 8000
sudo lsof -i :8000

# Stop conflicting service
sudo kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### Database Connection Failed

```bash
# Check database status
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U postgres -c "SELECT 1;"

# Check logs
docker-compose logs postgres

# Rebuild database
docker-compose down -v
docker-compose up -d postgres
docker-compose exec app python manage.py migrate
```

### Out of Memory

```bash
# Check memory usage
docker stats

# Reduce services temporarily
docker-compose stop celery celery-beat

# Or increase available memory
# Edit docker-compose.yml memory limits
```

### SSL Certificate Issues

```bash
# Check certificate expiry
openssl x509 -in ssl/fullchain.pem -noout -dates

# Renew Let's Encrypt certificate
sudo certbot renew --force-renewal

# Copy renewed certificate
sudo cp /etc/letsencrypt/live/yourdomain.com/*.pem ./ssl/
```

### Celery Not Processing Tasks

```bash
# Check Celery status
docker-compose logs celery

# Inspect active tasks
docker-compose exec app celery -A config inspect active

# Check Redis connection
docker-compose exec redis redis-cli ping

# Purge stuck tasks
docker-compose exec app celery -A config purge
```

---

## 🏗️ Architecture Details

### Technology Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.13 | Application runtime |
| Django | 5.2.8 | Web framework |
| Django REST Framework | 3.15.2 | API framework |
| PostgreSQL | 16 | Primary database |
| Redis | 7 | Cache & message broker |
| Celery | 5.3.4 | Async tasks |
| Django Celery Beat | 2.5.0 | Task scheduler |
| Gunicorn | 21.2.0 | Production WSGI server |
| Nginx | Latest Alpine | Reverse proxy |
| uv | Latest | Fast package installer |

### Data Flow

```
User Request
    ↓
Nginx (Reverse Proxy)
    ↓
Django (REST API)
    ├─ Read/Write → PostgreSQL
    ├─ Cache → Redis
    └─ Async Task → Celery
              ↓
        Workers process
        using Redis broker
              ↓
        Results stored in Redis
```

### Network Architecture

```
Development:
- All services in single docker network
- Port 8000 exposed locally

Production:
- Behind Nginx reverse proxy
- PostgreSQL/Redis not exposed
- Only port 80/443 accessible
- App only accessible internally
```

### Volume Management

```
Development:
- Live code mount (auto-reload)
- Database data persistence
- Redis data persistence

Production:
- Static files volume
- Media files volume
- Database data (persistent)
- Redis data (persistent)
```

---

## 📚 Additional Resources

### Documentation
- [Docker Documentation](https://docs.docker.com/)
- [Django Deployment Guide](https://docs.djangoproject.com/en/5.0/howto/deployment/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Celery Documentation](https://docs.celeryproject.org/)

### Production Guides
- [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md) - Complete production setup
- [DOCKER_SETUP.md](./DOCKER_SETUP.md) - Detailed Docker guide

### Helpful Commands

```bash
# Create backup
docker-compose exec postgres pg_dump -U postgres email_campaign_db | gzip > db_$(date +%Y%m%d_%H%M%S).sql.gz

# Scale services
docker-compose up -d --scale celery=3

# Update single image
docker-compose build app

# Push to registry
docker tag email-platform:latest myregistry.com/email-platform:1.0.0
docker push myregistry.com/email-platform:1.0.0

# Clean up everything
docker system prune -a --volumes
```

---

## 🆘 Getting Help

### Debug Information

When reporting issues, provide:
```bash
# Docker version
docker --version
docker-compose --version

# Service status
docker-compose ps
docker-compose logs --tail 50

# System info
df -h
free -h
docker stats
```

### Support Channels
- GitHub Issues: [YourRepo]/issues
- Email: devops@example.com
- Documentation: See PRODUCTION_DEPLOYMENT.md

---

**Last Updated:** $(date)
**Version:** 1.0.0
**Maintainer:** DevOps Team
