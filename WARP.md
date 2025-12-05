# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Email Campaign Management Platform - A Django REST API with React frontend for managing email marketing campaigns. This is a monorepo with separate backend and frontend directories.

**Architecture:**
- **Backend**: Django 5.2.8 + Django REST Framework 3.15.2 + PostgreSQL 16 + Redis 7
- **Frontend**: React TypeScript (planned, currently empty directory)
- **Task Queue**: Celery 5.3.4 with Celery Beat for scheduled campaigns
- **Deployment**: Docker Compose for both dev and production environments

## Repository Structure

```
.
├── backend/                 # Django REST API
│   ├── apps/                # Django applications
│   │   ├── authentication/  # User, Organization, JWT auth
│   │   ├── campaigns/       # Main app: campaigns, contacts, email delivery
│   │   └── utils/          # Shared utilities
│   ├── core/               # Core utilities (exceptions, mixins)
│   ├── project_config/     # Django settings & Celery config
│   │   └── settings/       # Split settings: base, development, production, testing
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile          # Multi-stage build (dev & prod)
│   └── docker-compose.yml  # Development services
├── frontend/               # React app (empty, planned)
└── .env.local             # Root environment config
```

## Development Commands

### Local Development (Non-Docker)

```bash
# From backend/ directory
cd backend

# Install dependencies (requires Python 3.13)
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Create platform admin (has platform-wide access)
python manage.py create_platform_admin admin@example.com --create --password admin123 --staff

# Start dev server
python manage.py runserver

# Start Celery worker (in separate terminal)
celery -A project_config worker -l info

# Start Celery Beat scheduler (in separate terminal)
celery -A project_config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Docker Development (Recommended)

```bash
# Quick start with automated setup
cd backend
bash docker-quickstart.sh dev

# Manual Docker workflow
cd backend
docker-compose up --build

# Django commands via Docker
docker-compose exec app python manage.py migrate
docker-compose exec app python manage.py createsuperuser
docker-compose exec app python manage.py shell

# View logs
docker-compose logs -f app
docker-compose logs -f celery

# Database access
docker-compose exec postgres psql -U postgres -d email_campaign_db

# Stop services
docker-compose down
```

### Testing

```bash
# Run all tests
cd backend
python manage.py test

# Run specific app tests
python manage.py test apps.campaigns

# Run specific test file
python manage.py test apps.campaigns.tests.test_email_logs

# With Docker
docker-compose exec app python manage.py test
docker-compose exec app pytest  # If using pytest
```

### Database

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create backup
docker-compose exec postgres pg_dump -U postgres email_campaign_db > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U postgres email_campaign_db < backup.sql
```

## Architecture & Code Organization

### Multi-Organization Model

This platform uses a **multi-tenant architecture** where each `Organization` has:
- Isolated data access (campaigns, contacts, email configs scoped by organization)
- User membership model with roles: `owner`, `admin`, `member`
- Organization-scoped email providers and configurations

**Key Models:**
- `User` (authentication app) - Custom user model with `organization` FK
- `Organization` (authentication app) - Tenant model
- `OrganizationMembership` - Links users to organizations with roles

### Campaign System Architecture

The campaigns app is the core of the platform and follows this flow:

1. **Campaign Creation** (`Campaign` model)
   - User creates campaign with email content (HTML/text)
   - Selects target `ContactList(s)` 
   - Can use `EmailTemplate` for reusable layouts
   - Assigns `OrganizationEmailProvider` (or uses org default)

2. **Email Queue System**
   - `EmailQueue` - Queues emails for batch sending
   - `EmailDeliveryLog` - Tracks each email sent (sent, delivered, bounced, etc.)
   - `EmailAction` - Tracks opens, clicks, unsubscribes

3. **Celery Tasks** (apps/campaigns/tasks.py)
   - `launch_campaign_task` - Launches a campaign, queues emails
   - `send_email_batch_task` - Sends batch of emails via provider
   - `check_campaign_status` - Periodic task to check campaign state
   - `process_email_events` - Processes delivery webhooks
   - Celery Beat schedules: every 5 min for campaign status, every 1 min for events

4. **Email Provider System** (apps/campaigns/backends.py)
   - Abstracted provider interface: `BaseEmailBackend`
   - Implementations: `AWSEmailBackend` (SES), `TwilioEmailBackend` (SendGrid)
   - Multi-provider support at organization level
   - Fallback/load-balancing capabilities

### Settings Architecture

**Split settings pattern:**
- `project_config/settings/base.py` - Common settings for all envs
- `project_config/settings/development.py` - Dev-specific (DEBUG=True, console email backend)
- `project_config/settings/production.py` - Production security settings
- `project_config/settings/testing.py` - Test-specific

**Environment variables:**
- Uses `python-decouple` for env var management
- Root `.env.local` for shared config
- `backend/.env.local` for Django-specific config

### URL Structure

All API endpoints are prefixed with `/api/v1/`:

- `/api/v1/auth/` - Authentication (register, login, JWT token management)
- `/api/v1/campaigns/` - Campaign management, contacts, email operations
  - `campaigns/` - CRUD campaigns
  - `campaigns/<uuid>/launch/`, `pause/`, `resume/`, `cancel/` - Campaign actions
  - `campaigns/<uuid>/analytics/` - Campaign statistics
  - `contacts/` - Contact management
  - `contact-lists/` - Contact list management
  - `templates/` - Email templates
  - `config/` - Organization email configuration
  - `providers/` - Email provider setup
  - `rules/` - Automation rules
  - `trigger/email/` - Trigger transactional emails

### Error Handling

Custom exception handler in `core/exceptions.py`:
- Wraps all API errors in consistent format:
  ```json
  {
    "message": "Error description",
    "status_type": "error",
    "status_code": 400,
    "timestamp": "2024-01-01T00:00:00Z",
    "errors": {...}
  }
  ```

### Authentication & Permissions

- **JWT Authentication** via `djangorestframework-simplejwt`
- Access token: 15 minutes
- Refresh token: 7 days
- Custom permission: `IsPlatformAdmin` for platform-wide operations
- Organization-scoped access enforced in views/querysets

## Production Deployment

### Docker Production Deployment

```bash
# On production server
cd /opt/email-platform/backend

# Configure environment
cp .env.production .env.production.local
nano .env.production.local  # Set secure passwords, domains

# Deploy with automated script
bash deploy.sh --branch production --force

# Or deploy specific version
bash deploy.sh --tag v1.2.0

# Manual production startup
docker-compose -f docker-compose.prod.yml up -d

# Check health
curl http://localhost:8000/api/v1/campaigns/health/
docker-compose -f docker-compose.prod.yml ps
```

### Production Checklist

- Set `DEBUG=False` in production settings
- Use strong `SECRET_KEY`, `DB_PASSWORD`, `REDIS_PASSWORD`
- Configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
- Set up SSL certificates (Let's Encrypt via Certbot)
- Configure Nginx reverse proxy
- Set up monitoring (Sentry via `sentry-sdk`)
- Configure email backend (AWS SES or SendGrid via Twilio)
- Enable database backups

## Key Development Patterns

### Creating New Models

Models in campaigns app are organized by domain:
- `campaign_models.py` - Campaign, core campaign logic
- `contact_models.py` - Contact, ContactList
- `email_config_models.py` - EmailTemplate
- `email_tracking_models.py` - EmailQueue, EmailDeliveryLog, EmailAction, EmailValidation
- `organization_email_config.py` - OrganizationEmailConfiguration
- `provider_models.py` - EmailProvider, OrganizationEmailProvider
- `automation_rule_model.py` - AutomationRule
- `sms_config_models.py` - SMS models

Use `apps.utils.base_models.BaseModel` for common fields:
- `id` (UUID), `created_at`, `updated_at`, `is_active`, `created_by`

### Creating New Endpoints

1. Create view in `apps/campaigns/views/` (organized by domain)
2. Add serializer in `apps/campaigns/serializers/`
3. Register URL in `apps/campaigns/urls.py`
4. Views use `APIView` pattern (explicit control over HTTP methods)
5. Apply organization scoping in `get_queryset()` or view logic

### Celery Tasks

Celery is configured in `project_config/celery.py`:
- Auto-discovers tasks from all apps
- Beat schedule defined for periodic tasks
- Redis as broker and result backend

To create new task:
```python
from celery import shared_task

@shared_task
def my_task(param):
    # Task logic
    pass
```

### Multi-Provider Email Sending

Email sending is abstracted via backends in `apps/campaigns/backends.py`:
- Inherit from `BaseEmailBackend`
- Implement `send_email()` method
- Register in provider system
- Supports SES, SendGrid (Twilio), and extensible for others

## Important Notes

- **Organization Scoping**: Always filter by `request.user.organization` for user data access
- **UUID Primary Keys**: All models use UUID PKs, not integer PKs
- **Celery for Async**: Use Celery tasks for email sending, long-running operations
- **Campaign Status Flow**: DRAFT → SCHEDULED → SENDING → SENT (or PAUSED/CANCELLED/FAILED)
- **Statistics Caching**: Campaign stats are denormalized in `Campaign` model (`stats_*` fields) for performance
- **Email Tracking**: Opens/clicks tracked via unique URLs with tracking pixels
- **Frontend**: Frontend directory is empty - React app is planned but not yet implemented

## Services & Ports

**Development:**
- Django API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

**Production:**
- Nginx reverse proxy on 80/443
- Django API on internal port 8000
- PostgreSQL & Redis not exposed externally

## Useful Management Commands

```bash
# Platform admin management
python manage.py create_platform_admin <email> --create --password <pass> --staff

# Django shell with IPython
python manage.py shell

# Collect static files
python manage.py collectstatic

# Check for issues
python manage.py check

# Database shell
python manage.py dbshell
```

## Linting & Formatting

Tools configured in requirements.txt:
- `black` - Code formatter
- `isort` - Import sorting
- `flake8` - Linting
- `pre-commit` - Pre-commit hooks

Run before committing:
```bash
black backend/
isort backend/
flake8 backend/
```
