````markdown
# Docker & PostgreSQL Setup

## 🐳 Multi-Environment Docker Configuration

This project supports three separate environments, each with its own Docker configuration:

### Environments

| Environment | Use Case | Docker File | Env File |
|------------|----------|-------------|----------|
| **Local** | Daily development | `../docker-compose.local.yml` | `../.env.local` |
| **Dev** | Staging/Dev server | `../docker-compose.dev.yml` | `../.env.dev` |
| **Prod** | Production deployment | `../docker-compose.prod.yml` | `../.env.prod` |

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Start Development Environment

```bash
# Using the helper script (recommended)
../docker-manage.sh local up --build

# Or using docker-compose directly  
docker-compose -f ../docker-compose.local.yml up --build
```

Access at: http://localhost:8000

### Create Superuser

```bash
../docker-manage.sh local createsuperuser
```

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[DOCKER_SETUP.md](DOCKER_SETUP.md)** - Comprehensive setup guide
- **[SUMMARY.md](SUMMARY.md)** - Overview of all changes

## 🛠️ Common Commands

```bash
# Start environment (with rebuild)
../docker-manage.sh local up --build

# View logs
../docker-manage.sh local logs web

# Run migrations
../docker-manage.sh local migrate

# Django shell
../docker-manage.sh local shell

# Database shell
../docker-manage.sh local dbshell

# Run tests
../docker-manage.sh local test

# Stop environment
../docker-manage.sh local down

# Backup database
../docker-manage.sh local backup
```

## 🏗️ Architecture

### Local Development
- Django development server with hot-reload
- PostgreSQL 16 database
- Console email backend
- Volume mounts for live code updates

### Production
- Nginx reverse proxy
- Gunicorn WSGI server (4 workers)
- PostgreSQL 16 database with persistent volumes
- Redis caching
- SSL/TLS ready
- Static file serving with WhiteNoise

## 🔐 Environment Variables

Each environment uses its own `.env` file:

```bash
# Local (ready to use)
../.env.local

# Development server (update before use)
../.env.dev

# Production (update before use)
../.env.prod
```

**Important:** Never commit `.env.*` files to version control!

## 📦 Services

### Web (Django)
- **Local**: Django development server (port 8000)
- **Dev/Prod**: Gunicorn WSGI server

### Database (PostgreSQL)
- PostgreSQL 16 Alpine
- Persistent data volumes
- Health checks
- Backup support

### Nginx (Production only)
- Reverse proxy
- Static/media file serving
- SSL/TLS termination
- Security headers

### Redis (Production, optional)
- Caching backend
- Session storage

## 🔧 Configuration

### Settings Structure
```
config/settings/
├── __init__.py      # Auto-loads based on DJANGO_ENV
├── base.py          # Shared settings
├── local.py         # Local development
├── dev.py           # Development server
└── prod.py          # Production
```

The appropriate settings file is loaded based on the `DJANGO_ENV` environment variable.

## 🐘 Database Access

### From Host Machine
```bash
# Using the helper script
../docker-manage.sh local dbshell

# Using psql directly
docker exec -it email_campaign_db_local psql -U postgres -d email_campaign_db
```

### From GUI Tools (e.g., pgAdmin, DBeaver)
- Host: `localhost`
- Port: `5432`
- Database: `email_campaign_db` (local), `email_campaign_dev_db` (dev), etc.
- Username: `postgres`
- Password: See respective `.env` file

## 🔄 Database Management

### Migrations
```bash
# Create migrations
../docker-manage.sh local makemigrations

# Apply migrations
../docker-manage.sh local migrate
```

### Backup & Restore
```bash
# Backup
../docker-manage.sh local backup

# Restore
../docker-manage.sh local restore ../backups/backup_local_20231119_120000.sql
```

## 🧪 Running Tests

```bash
# All tests
../docker-manage.sh local test

# Specific app
../docker-manage.sh local test authentication

# With coverage
docker-compose -f ../docker-compose.local.yml exec web python manage.py test --coverage
```

## 🚀 Deployment

### Development Server
```bash
# Update .env.dev with your configuration
../docker-manage.sh dev up -d --build
../docker-manage.sh dev migrate
../docker-manage.sh dev createsuperuser
```

### Production
```bash
# Update .env.prod with production values
../docker-manage.sh prod up -d --build
../docker-manage.sh prod migrate
../docker-manage.sh prod collectstatic
../docker-manage.sh prod createsuperuser
```

## 🛡️ Security Checklist (Production)

Before deploying to production:

- [ ] Generate new `SECRET_KEY` in `../.env.prod`
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use strong database passwords
- [ ] Set up SSL/TLS certificates
- [ ] Configure proper CORS settings
- [ ] Enable Redis authentication
- [ ] Set up monitoring and logging
- [ ] Configure backup automation
- [ ] Review security headers in Nginx

## 🐛 Troubleshooting

### Port Already in Use
Change port mapping in the docker-compose file:
```yaml
ports:
  - "8001:8000"  # Use 8001 instead
```

### Database Connection Issues
Check database health:
```bash
docker-compose -f ../docker-compose.local.yml logs db
docker-compose -f ../docker-compose.local.yml ps
```

### Reset Everything
```bash
# Stop and remove all containers and volumes
../docker-manage.sh local down -v

# Rebuild from scratch
../docker-manage.sh local up --build
```

## 📖 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/configure.html)

---

For more detailed information, see [DOCKER_SETUP.md](DOCKER_SETUP.md)

````