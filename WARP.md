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
│   │   │   └── tests/       # Campaign app tests
│   │   └── utils/          # Shared utilities
│   ├── core/               # Core utilities (exceptions, mixins)
│   ├── project_config/     # Django settings & Celery config
│   │   ├── settings.py     # Main settings file
│   │   ├── celery.py       # Celery configuration
│   │   └── urls.py         # Root URL configuration
│   ├── scripts/            # Helper scripts
│   │   ├── django.sh       # Django management helper
│   │   └── setup-dev.sh    # Development setup script
│   ├── manage.py
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Multi-stage build (dev & prod)
│   └── docker-compose.yml  # Development services
├── frontend/               # HTML/CSS/JS (static frontend)
├── requirements.txt        # Root-level dependencies
└── .env.local             # Root environment config
```

## Development Commands

### Local Development (Non-Docker)

```bash
# Option 1: Using helper scripts (recommended)
cd backend

# Initial setup (creates venv, installs deps, creates .env.local)
bash scripts/setup-dev.sh

# Activate virtual environment
source venv/bin/activate

# Run migrations
bash scripts/django.sh migrate

# Create superuser
bash scripts/django.sh superuser

# Create platform admin (has platform-wide access)
python manage.py create_platform_admin admin@example.com --create --password admin123 --staff

# Start dev server
bash scripts/django.sh runserver

# Start Celery worker (in separate terminal)
celery -A project_config worker -l info

# Start Celery Beat scheduler (in separate terminal)
celery -A project_config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**Option 2: Manual setup**
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (requires Python 3.13)
pip install -r requirements.txt

# Copy environment template
cp .env.example .env.local

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start dev server
python manage.py runserver
```

### Docker Development (Recommended)

```bash
# Manual Docker workflow (no quickstart.sh script found in this project)
cd backend

# Start all services (postgres, redis, app, celery, celery-beat)
docker-compose up --build

# Or run in background
docker-compose up -d --build

# Django commands via Docker
docker-compose exec app python manage.py migrate
docker-compose exec app python manage.py createsuperuser
docker-compose exec app python manage.py shell

# View logs
docker-compose logs -f app
docker-compose logs -f celery
docker-compose logs -f celery-beat

# Database access
docker-compose exec postgres psql -U postgres -d email_campaign_db

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
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

# Run with coverage
pytest --cov=apps --cov-report=html

# With Docker
docker-compose exec app python manage.py test
docker-compose exec app pytest
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

**Single settings file:**
- `project_config/settings.py` - Main Django settings file
- Environment-specific configuration controlled via `DJANGO_ENV` variable
- Uses `python-decouple` for environment variable management

**Environment variables:**
- Root `.env.local` for shared config
- `backend/.env.local` for Django-specific config
- Copy from `backend/.env.example` to get started

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

**Note**: This project doesn't have docker-compose.prod.yml or deploy.sh scripts yet. For production, use the standard docker-compose.yml with production environment variables:

```bash
# On production server
cd backend

# Create production environment file
cp .env.example .env.production
nano .env.production  # Set DEBUG=False, secure passwords, domains

# Build and start services
ENV_FILE=.env.production docker-compose up -d --build

# Run migrations
docker-compose exec app python manage.py migrate

# Collect static files
docker-compose exec app python manage.py collectstatic --noinput

# Check health
curl http://localhost:8000/api/v1/campaigns/health/
docker-compose ps
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
- **Frontend**: Frontend contains static HTML/CSS/JS files (not React) - basic authentication pages

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

Tools installed in requirements.txt:
- `black` - Code formatter
- `isort` - Import sorting
- `flake8` - Linting
- `pre-commit` - Pre-commit hooks (if configured)

Run from backend directory:
```bash
cd backend

# Format code
black .

# Sort imports
isort .

# Check linting
flake8 .

# Run all checks
black . && isort . && flake8 .
```

**Note**: No .flake8, pyproject.toml, or .pre-commit-config.yaml configuration files exist yet. These can be added for custom settings.
