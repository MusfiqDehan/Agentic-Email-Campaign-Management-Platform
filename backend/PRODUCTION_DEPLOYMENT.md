# Production Deployment Guide

This guide covers deploying the Email Campaign Management Platform to production using Docker.

**Table of Contents**
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [System Requirements](#system-requirements)
3. [Deployment Steps](#deployment-steps)
4. [Database Setup](#database-setup)
5. [SSL/TLS Configuration](#ssltls-configuration)
6. [Nginx Configuration](#nginx-configuration)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup Strategy](#backup-strategy)
9. [Scaling](#scaling)
10. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

Before deploying to production:

- [ ] All environment variables set in `.env.production`
- [ ] Database credentials changed from defaults
- [ ] Redis password set to strong random value
- [ ] SECRET_KEY changed to new random value (64+ chars)
- [ ] ALLOWED_HOSTS configured for your domain
- [ ] SSL/TLS certificates obtained (Let's Encrypt recommended)
- [ ] CORS origins configured correctly
- [ ] Email service (SES/SMTP) configured and tested
- [ ] AWS credentials set if using SES
- [ ] Database backups configured
- [ ] Monitoring tools set up (Sentry, DataDog, etc.)
- [ ] Security scan completed (bandit, safety)
- [ ] Load testing performed
- [ ] Rollback plan documented

---

## System Requirements

**Minimum Production Server:**
- CPU: 4 cores
- RAM: 8 GB
- Storage: 50 GB SSD
- OS: Ubuntu 20.04 LTS or later

**Recommended Production Server:**
- CPU: 8+ cores
- RAM: 16+ GB
- Storage: 100+ GB SSD (with snapshots)
- OS: Ubuntu 22.04 LTS

**Docker Requirements:**
```bash
Docker version: 20.10+
Docker Compose version: 2.0+
```

---

## Deployment Steps

### Step 1: Prepare Server

```bash
# SSH into production server
ssh user@production-server

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Create app directory
mkdir -p /opt/email-platform
cd /opt/email-platform
```

### Step 2: Clone Repository

```bash
# Clone your repository (use deploy key or token)
git clone https://github.com/yourorg/email-platform.git .

# Checkout production branch
git checkout production

# Navigate to backend
cd backend
```

### Step 3: Configure Environment

```bash
# Copy production environment template
cp .env.production .env.production.local

# Edit with production values
nano .env.production.local

# Security: Set proper permissions
chmod 600 .env.production.local
```

**Critical environment variables to update:**
```bash
# Security
SECRET_KEY="your-64-char-random-secret-key-here"
DEBUG=False

# Database
DB_PASSWORD="your-very-strong-database-password"
DATABASE_URL="postgresql://user:password@postgres:5432/email_campaign_db_prod"

# Redis
REDIS_PASSWORD="your-very-strong-redis-password"

# Domains
ALLOWED_HOSTS="api.example.com,www.example.com"
CSRF_TRUSTED_ORIGINS="https://app.example.com,https://www.example.com"

# Email
EMAIL_HOST_PASSWORD="your-email-app-password"
AWS_ACCESS_KEY_ID="your-aws-key"
AWS_SECRET_ACCESS_KEY="your-aws-secret"

# Monitoring
SENTRY_DSN="your-sentry-dsn"
```

### Step 4: Build Images

```bash
# Build Docker images
docker-compose -f docker-compose.prod.yml build

# Verify images
docker images | grep email-platform
```

### Step 5: Start Services

```bash
# Start services in background
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Wait for services to be healthy
docker-compose -f docker-compose.prod.yml ps --services --filter "status=running"
```

### Step 6: Initialize Database

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec app python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec app python manage.py createsuperuser

# Create platform admin
docker-compose -f docker-compose.prod.yml exec app python manage.py create_platform_admin admin@example.com --create --staff

# Collect static files
docker-compose -f docker-compose.prod.yml exec app python manage.py collectstatic --no-input

# Verify setup
docker-compose -f docker-compose.prod.yml exec app python manage.py check
```

### Step 7: Setup Nginx & SSL

See [SSL/TLS Configuration](#ssltls-configuration) section below.

---

## Database Setup

### Backup Configuration

```bash
# Create backup script: /opt/email-platform/backup.sh
#!/bin/bash

BACKUP_DIR="/opt/email-platform/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"

mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U postgres email_campaign_db_prod | gzip > $BACKUP_FILE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
```

### Automated Backups (Cron)

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /opt/email-platform && bash backup.sh >> /var/log/db-backup.log 2>&1

# Weekly backup to S3 (optional)
0 3 * * 0 cd /opt/email-platform && bash backup.sh && aws s3 sync backups/ s3://your-bucket/backups/
```

### Database Scaling

For high volume deployments:

1. **Read Replicas:**
   ```bash
   # Configure primary-replica replication in PostgreSQL
   # Use read replicas for reporting queries
   ```

2. **Connection Pooling:**
   ```bash
   # Add PgBouncer service
   # Pool connections at application level
   ```

3. **Sharding:**
   ```bash
   # For multi-tenant separation by organization
   # Implement logical sharding
   ```

---

## SSL/TLS Configuration

### Option 1: Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Create SSL directory
sudo mkdir -p /opt/email-platform/ssl

# Obtain certificate (domain must be pointed to server)
sudo certbot certonly --standalone \
    -d api.example.com \
    -d www.example.com \
    --non-interactive \
    --agree-tos \
    --email admin@example.com

# Copy certificates to app directory
sudo cp /etc/letsencrypt/live/api.example.com/fullchain.pem /opt/email-platform/ssl/
sudo cp /etc/letsencrypt/live/api.example.com/privkey.pem /opt/email-platform/ssl/
sudo chown -R $USER:$USER /opt/email-platform/ssl/

# Auto-renewal cron job
sudo certbot renew --quiet --no-eff-email
```

### Option 2: Self-Signed Certificate (Development)

```bash
# Generate self-signed cert
openssl req -x509 -newkey rsa:4096 \
    -keyout ssl/privkey.pem \
    -out ssl/fullchain.pem \
    -days 365 -nodes \
    -subj "/C=US/ST=State/L=City/O=Org/CN=api.example.com"
```

### Option 3: Cloud Provider Certificate

For AWS, GCP, or Azure deployments:
- Use AWS Certificate Manager (ACM)
- Use Google Managed Certificates
- Use Azure Key Vault

---

## Nginx Configuration

### Enable Nginx Service

```bash
# Create Nginx container (optional - use reverse proxy service)
docker-compose -f docker-compose.prod.yml up -d nginx

# Or install Nginx directly on host
sudo apt install -y nginx

# Copy configuration
sudo cp nginx.conf /etc/nginx/sites-available/email-platform
sudo ln -s /etc/nginx/sites-available/email-platform /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Check status
sudo systemctl status nginx
```

### Firewall Configuration

```bash
# Open only necessary ports
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw deny incoming     # Deny all other

# Enable firewall
sudo ufw enable
```

---

## Monitoring & Logging

### Application Monitoring

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs --follow

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f app
docker-compose -f docker-compose.prod.yml logs -f celery
docker-compose -f docker-compose.prod.yml logs -f postgres

# Rotate logs
docker-compose -f docker-compose.prod.yml logs --follow --tail 100

# View logs from outside container
tail -f /var/lib/docker/containers/*/\*-json.log
```

### Health Checks

```bash
# Check service health
curl http://localhost:8000/api/v1/campaigns/health/

# Check all services
docker-compose -f docker-compose.prod.yml ps

# Monitor system resources
docker stats

# Check disk space
df -h

# Check memory usage
free -h
```

### Set up Monitoring Tools

**1. Sentry (Error Tracking)**
```bash
# Create account at sentry.io
# Set SENTRY_DSN in .env.production.local
# Errors will be automatically reported
```

**2. Prometheus & Grafana**
```yaml
# Add to docker-compose.prod.yml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
```

**3. ELK Stack (Logging)**
- Elasticsearch for log storage
- Logstash for log processing
- Kibana for visualization

### Log Rotation

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/email-platform

# Configuration:
/var/log/nginx/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

---

## Backup Strategy

### Daily Backups

```bash
# Database backup script
#!/bin/bash
BACKUP_DIR="/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)

docker-compose -f docker-compose.prod.yml exec -T postgres \
    pg_dump -U postgres email_campaign_db_prod | \
    gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep 30 days of backups
find $BACKUP_DIR -mtime +30 -delete
```

### Media Files Backup

```bash
# Backup media uploads to S3
docker run --rm \
    -v email-platform_media_files:/app/media \
    -e AWS_ACCESS_KEY_ID=$AWS_KEY \
    -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET \
    amazon/aws-cli s3 sync /app/media s3://your-bucket/media/
```

### Disaster Recovery

```bash
# Test restore procedure regularly
docker-compose -f docker-compose.prod.yml down

# Restore database
zcat backup.sql.gz | docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres

# Restore media files
aws s3 sync s3://your-bucket/media/ /opt/email-platform/media/

# Verify restoration
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml exec app python manage.py check
```

---

## Scaling

### Horizontal Scaling (Multiple App Instances)

```yaml
# docker-compose.prod.yml with multiple app instances
version: '3.9'

services:
  app:
    deploy:
      replicas: 3  # Run 3 instances
      update_config:
        parallelism: 1
        delay: 10s
```

### Load Balancing Configuration

Update Nginx upstream block:
```nginx
upstream django_app {
    least_conn;  # Load balancing algorithm
    server app-1:8000;
    server app-2:8000;
    server app-3:8000;
}
```

### Database Connection Scaling

```bash
# Increase PGPOOL workers
POSTGRES_MAX_CONNECTIONS=200

# Add connection pooling
PG_BOUNCER_POOL_SIZE=50
```

### Celery Scaling

```bash
# Increase worker concurrency
CELERY_WORKERS=8
CELERY_PREFETCH_MULTIPLIER=4

# Run multiple worker processes
docker-compose -f docker-compose.prod.yml up -d --scale celery=3
```

---

## Troubleshooting

### Service Not Starting

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs app

# Common issues:
# 1. Port already in use
sudo lsof -i :8000

# 2. Permission denied
sudo chown -R $USER:$USER /opt/email-platform

# 3. Out of disk space
df -h
docker system prune -a
```

### Database Connection Issues

```bash
# Test database connection
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U postgres -d email_campaign_db_prod -c "SELECT 1;"

# Check PostgreSQL logs
docker-compose -f docker-compose.prod.yml logs postgres

# Common fixes:
# - Verify DB_PASSWORD matches POSTGRES_PASSWORD
# - Check DATABASE_URL format
# - Verify network connectivity
```

### Memory Issues

```bash
# Monitor memory usage
docker stats

# Reduce Celery workers
CELERY_WORKERS=2

# Reduce Redis maxmemory
REDIS_MAX_MEMORY=256mb

# Increase server RAM if needed
```

### Slow Queries

```bash
# Enable query logging
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U postgres -d email_campaign_db_prod \
    -c "ALTER DATABASE email_campaign_db_prod SET log_min_duration_statement = 1000;"

# Check slow query log
docker-compose -f docker-compose.prod.yml logs postgres | grep slow
```

### SSL/TLS Issues

```bash
# Test SSL configuration
openssl s_client -connect api.example.com:443

# Check certificate validity
openssl x509 -in ssl/fullchain.pem -text -noout

# Renew expired certificate
sudo certbot renew --force-renewal

# Common issues:
# - Certificate not found: Check nginx.conf paths
# - Certificate expired: Run renewal command
# - Mixed content (HTTP/HTTPS): Update ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS
```

### Celery Issues

```bash
# Check Celery tasks
docker-compose -f docker-compose.prod.yml exec app \
    celery -A project_config inspect active

# Purge stuck tasks
docker-compose -f docker-compose.prod.yml exec app \
    celery -A project_config purge

# Monitor task queue
docker-compose -f docker-compose.prod.yml exec app \
    celery -A project_config events

# Check Redis connection
docker-compose -f docker-compose.prod.yml exec redis \
    redis-cli ping
```

### Performance Optimization

```bash
# 1. Enable caching
CACHES_TIMEOUT=3600  # Cache for 1 hour

# 2. Database query optimization
DJANGO_DEBUG=False  # Disable debug queries

# 3. CDN setup
# Point static files to CDN

# 4. Database indexing
# Check slow queries and add indexes

# 5. Celery optimization
CELERY_TASK_TIME_LIMIT=3600
CELERY_TASK_SOFT_TIME_LIMIT=3000

# 6. Redis optimization
REDIS_MEMORY_LIMIT=1gb
REDIS_EVICTION_POLICY=allkeys-lru
```

---

## Rollback Procedure

```bash
# In case of critical issues, rollback to previous version

# 1. Stop current services
docker-compose -f docker-compose.prod.yml down

# 2. Checkout previous working version
git checkout previous-tag

# 3. Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 4. Run migrations if needed
docker-compose -f docker-compose.prod.yml exec app python manage.py migrate

# 5. Verify health
docker-compose -f docker-compose.prod.yml ps
curl http://localhost:8000/api/v1/campaigns/health/
```

---

## Support & Resources

- [Docker Documentation](https://docs.docker.com/)
- [Django Deployment Guide](https://docs.djangoproject.com/en/5.0/howto/deployment/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)

For issues or questions, contact: devops@example.com
