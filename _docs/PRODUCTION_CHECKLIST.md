````markdown
# 🚀 Production Deployment Checklist

Use this checklist before deploying to production.

## 📋 Pre-Deployment Checklist

### 1. Environment Configuration

- [ ] Copy `../.env.example` to `../.env.prod`
- [ ] Generate new `SECRET_KEY` (min 50 characters)
  ```bash
  python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
  ```
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set proper `CSRF_TRUSTED_ORIGINS`
- [ ] Configure database credentials (strong password!)
- [ ] Configure email settings (SMTP credentials)

### 2. Database

- [ ] Change default PostgreSQL password
- [ ] Configure database connection pooling
- [ ] Set up automated backups
- [ ] Test backup/restore process
- [ ] Configure database monitoring

### 3. Security

- [ ] Generate and set unique `SECRET_KEY`
- [ ] Review all environment variables in `../.env.prod`
- [ ] Ensure `../.env.prod` is in `../.gitignore`
- [ ] Configure SSL/TLS certificates in Nginx
- [ ] Enable HTTPS redirect (`SECURE_SSL_REDIRECT=True`)
- [ ] Set secure cookie flags
- [ ] Review Django security settings
- [ ] Configure firewall rules
- [ ] Disable unnecessary ports
- [ ] Set up fail2ban or similar

### 4. Nginx Configuration

- [ ] Update domain name in `../nginx/conf.d/default.conf`
- [ ] Configure SSL certificates
- [ ] Test SSL configuration
- [ ] Enable HTTPS redirect
- [ ] Configure proper security headers
- [ ] Set up rate limiting (optional)
- [ ] Configure log rotation

### 5. Redis (Optional but Recommended)

- [ ] Enable Redis in `../docker-compose.prod.yml`
- [ ] Configure Redis password
- [ ] Update `REDIS_URL` in `../.env.prod`
- [ ] Configure Redis persistence
- [ ] Set up Redis monitoring

### 6. Static & Media Files

- [ ] Run `collectstatic` command
- [ ] Verify static files are served correctly
- [ ] Configure media upload directory permissions
- [ ] Set up CDN for static/media files (optional)

### 7. Logging & Monitoring

- [ ] Configure production logging
- [ ] Set up log rotation
- [ ] Configure error reporting (e.g., Sentry)
- [ ] Set up application monitoring
- [ ] Configure database monitoring
- [ ] Set up uptime monitoring
- [ ] Configure alerts

### 8. Performance

- [ ] Review Gunicorn worker count (2-4 × CPU cores)
- [ ] Configure proper timeouts
- [ ] Enable database connection pooling
- [ ] Configure Redis caching
- [ ] Review and optimize database queries
- [ ] Set up CDN for static assets

### 9. Backup Strategy

- [ ] Configure automated database backups
- [ ] Test restore process
- [ ] Set up off-site backup storage
- [ ] Configure media files backup
- [ ] Document backup procedures
- [ ] Test disaster recovery plan

### 10. Testing

- [ ] Run all tests
- [ ] Test migrations on production-like data
- [ ] Load testing
- [ ] Security testing
- [ ] Test backup/restore
- [ ] Verify SSL certificate
- [ ] Test error pages (404, 500, etc.)

## 🔧 Deployment Steps

### Step 1: Server Preparation

```bash
# Update system
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
```

### Step 2: Project Setup

```bash
# Clone repository
git clone <your-repo-url>
cd Email-Campaign-Management-Platform

# Checkout production branch
git checkout main  # or your production branch

# Copy and configure environment file
cp .env.example .env.prod
nano .env.prod  # Update all values
```

### Step 3: SSL Certificate Setup

```bash
# Using Let's Encrypt (certbot)
sudo apt install certbot python3-certbot-nginx -y

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates to nginx directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem

# Set up auto-renewal
sudo certbot renew --dry-run
```

### Step 4: Deploy Application

```bash
# Build and start containers
../docker-manage.sh prod up -d --build

# Check container status
../docker-manage.sh prod ps

# View logs
../docker-manage.sh prod logs -f

# Run migrations
../docker-manage.sh prod migrate

# Collect static files
../docker-manage.sh prod collectstatic

# Create superuser
../docker-manage.sh prod createsuperuser
```

### Step 5: Verify Deployment

```bash
# Check all containers are running
docker ps

# Test application
curl https://yourdomain.com

# Check Django admin
curl https://yourdomain.com/admin/

# Check health endpoint (if configured)
curl https://yourdomain.com/health/

# Review logs
../docker-manage.sh prod logs web
../docker-manage.sh prod logs nginx
../docker-manage.sh prod logs db
```

## 🔍 Post-Deployment Verification

### Application Health

- [ ] Homepage loads correctly
- [ ] Admin panel is accessible
- [ ] API endpoints respond correctly
- [ ] Static files load properly
- [ ] Media uploads work
- [ ] Database connections are stable
- [ ] No errors in logs

### Security Verification

- [ ] HTTPS is working
- [ ] HTTP redirects to HTTPS
- [ ] SSL certificate is valid
- [ ] Security headers are present
  ```bash
  curl -I https://yourdomain.com
  ```
- [ ] Debug mode is disabled
- [ ] Admin panel requires authentication

### Performance Checks

- [ ] Page load times are acceptable
- [ ] Database queries are optimized
- [ ] Caching is working
- [ ] CDN is serving static files (if configured)

## 📊 Monitoring Setup

### Application Monitoring

- [ ] Set up error tracking (Sentry, etc.)
- [ ] Configure uptime monitoring
- [ ] Set up performance monitoring
- [ ] Configure log aggregation

### Alerts

- [ ] High error rate
- [ ] Server down
- [ ] High response times
- [ ] Database connection issues
- [ ] Disk space low
- [ ] SSL certificate expiring

## 🔄 Maintenance

### Regular Tasks

- [ ] Review logs weekly
- [ ] Monitor resource usage
- [ ] Review security updates
- [ ] Test backups monthly
- [ ] Update dependencies regularly
- [ ] Review and optimize database
- [ ] Renew SSL certificates (automated)

### Update Procedure

```bash
# 1. Backup first!
../docker-manage.sh prod backup

# 2. Pull latest code
git pull origin main

# 3. Rebuild containers
../docker-manage.sh prod down
../docker-manage.sh prod up -d --build

# 4. Run migrations
../docker-manage.sh prod migrate

# 5. Collect static files
../docker-manage.sh prod collectstatic

# 6. Verify deployment
../docker-manage.sh prod logs -f
```

## 🆘 Rollback Procedure

```bash
# 1. Stop current deployment
../docker-manage.sh prod down

# 2. Restore previous version
git checkout <previous-commit>

# 3. Restore database backup (if needed)
../docker-manage.sh prod restore ../backups/backup_prod_YYYYMMDD_HHMMSS.sql

# 4. Rebuild and start
../docker-manage.sh prod up -d --build

# 5. Verify
../docker-manage.sh prod logs -f
```

## 📞 Emergency Contacts

Document your emergency contacts:

- [ ] System Administrator: _______________
- [ ] Database Administrator: _______________
- [ ] DevOps Lead: _______________
- [ ] Security Team: _______________
- [ ] Hosting Provider Support: _______________

## 📝 Documentation

- [ ] Update deployment documentation
- [ ] Document custom configurations
- [ ] Create runbook for common issues
- [ ] Document backup/restore procedures
- [ ] Update architecture diagrams
- [ ] Document monitoring setup

## ✅ Sign-off

- [ ] Technical Lead Approval: _________________ Date: _______
- [ ] Security Review: _________________ Date: _______
- [ ] Operations Approval: _________________ Date: _______

---

## 📖 Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [OWASP Security Guidelines](https://owasp.org/www-project-web-security-testing-guide/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)
- [Nginx Security](https://nginx.org/en/docs/http/ngx_http_ssl_module.html)

---

**Remember:** Never rush production deployments. Take time to verify each step!

````