````markdown
# Docker Environment Setup Guide

This project is configured to run with PostgreSQL in Docker across multiple environments: **local**, **dev**, and **prod**.

## 📋 Prerequisites

- Docker (20.10+)
- Docker Compose (2.0+)

## 🚀 Quick Start

### Local Development

```bash
# Start local environment
docker-compose -f ../docker-compose.local.yml up --build

# Access the application
http://localhost:8000

# Run migrations
docker-compose -f ../docker-compose.local.yml exec web python manage.py migrate

# Create superuser
docker-compose -f ../docker-compose.local.yml exec web python manage.py createsuperuser

# Stop containers
docker-compose -f ../docker-compose.local.yml down
```

### Development Server

```bash
# Start dev environment
docker-compose -f ../docker-compose.dev.yml up -d --build

# View logs
docker-compose -f ../docker-compose.dev.yml logs -f web

# Stop containers
docker-compose -f ../docker-compose.dev.yml down
```

### Production Deployment

```bash
# Build and start production environment
docker-compose -f ../docker-compose.prod.yml up -d --build

# View logs
docker-compose -f ../docker-compose.prod.yml logs -f

# Stop containers
docker-compose -f ../docker-compose.prod.yml down
```

## 🔧 Environment Configuration

Each environment has its own configuration file:

- **`.env.local`** - Local development settings
- **`.env.dev`** - Development server settings
- **`.env.prod`** - Production settings

### Important: Update Environment Files

Before running, copy `.env.example` and update values:

```bash
# For local development (already created)
cp ../.env.example ../.env.local

# For dev/prod, update the respective files with your values
```

**🔒 Security Note:** Never commit `.env.*` files to version control!

## 🗄️ Database Management

### Access PostgreSQL

```bash
# Local
docker-compose -f ../docker-compose.local.yml exec db psql -U postgres -d email_campaign_db

# Dev
docker-compose -f ../docker-compose.dev.yml exec db psql -U postgres -d email_campaign_dev_db

# Prod
docker-compose -f ../docker-compose.prod.yml exec db psql -U postgres -d email_campaign_prod_db
```

### Database Backups

```bash
# Create backup (local)
docker-compose -f ../docker-compose.local.yml exec db pg_dump -U postgres email_campaign_db > ../backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose -f ../docker-compose.local.yml exec -T db psql -U postgres -d email_campaign_db < ../backup_20231119.sql
```

## 🧪 Common Commands

### Run Django Commands

```bash
# Local environment
docker-compose -f ../docker-compose.local.yml exec web python manage.py <command>

# Examples:
docker-compose -f ../docker-compose.local.yml exec web python manage.py makemigrations
docker-compose -f ../docker-compose.local.yml exec web python manage.py migrate
docker-compose -f ../docker-compose.local.yml exec web python manage.py shell
docker-compose -f ../docker-compose.local.yml exec web python manage.py test
```

### View Logs

```bash
# All services
docker-compose -f ../docker-compose.local.yml logs -f

# Specific service
docker-compose -f ../docker-compose.local.yml logs -f web
docker-compose -f ../docker-compose.local.yml logs -f db
```

### Clean Up

```bash
# Remove containers and networks
docker-compose -f ../docker-compose.local.yml down

# Remove containers, networks, and volumes (⚠️ deletes database)
docker-compose -f ../docker-compose.local.yml down -v

# Remove all unused Docker resources
docker system prune -a
```

## 📁 Project Structure

```
.
├── config/
│   └── settings/
│       ├── __init__.py      # Auto-loads environment-specific settings
│       ├── base.py          # Common settings
│       ├── local.py         # Local development
│       ├── dev.py           # Development server
│       └── prod.py          # Production
├── docker-compose.local.yml # Local development
├── docker-compose.dev.yml   # Development server
├── docker-compose.prod.yml  # Production (with Nginx)
├── Dockerfile               # Multi-stage build
├── .env.local              # Local environment variables
├── .env.dev                # Dev environment variables
├── .env.prod               # Prod environment variables
└── .env.example            # Example environment file
```

## 🔑 Key Features

### Multi-Stage Dockerfile
- **Development stage**: Hot-reload, debugging tools
- **Production stage**: Optimized, non-root user, Gunicorn

### Environment Separation
- Each environment has isolated:
  - Database instance
  - Configuration settings
  - Docker Compose file
  - Environment variables

### Production Features
- Nginx reverse proxy
- Gunicorn WSGI server
- Redis caching (ready to enable)
- SSL/TLS support (configure nginx)
- Non-root container user
- Health checks
- Proper logging

## 🛡️ Security Checklist for Production

- [ ] Update `SECRET_KEY` in `.env.prod`
- [ ] Set `DEBUG=False` in `.env.prod`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Use strong database passwords
- [ ] Enable SSL/TLS in Nginx
- [ ] Configure Redis authentication
- [ ] Set up proper firewall rules
- [ ] Enable HTTPS redirect
- [ ] Configure backup strategy
- [ ] Set up monitoring and alerting

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check if database is healthy
docker-compose -f ../docker-compose.local.yml ps

# Restart database
docker-compose -f ../docker-compose.local.yml restart db

# Check database logs
docker-compose -f ../docker-compose.local.yml logs db
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Or change port in docker-compose file:
ports:
  - "8001:8000"
```

### Clear Docker Cache

```bash
# Rebuild without cache
docker-compose -f ../docker-compose.local.yml build --no-cache
```

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Nginx Documentation](https://nginx.org/en/docs/)

## 🤝 Contributing

When making changes, ensure all three environments are tested:
1. Test locally with `docker-compose.local.yml`
2. Test dev build with `docker-compose.dev.yml`
3. Verify production build with `docker-compose.prod.yml`

````