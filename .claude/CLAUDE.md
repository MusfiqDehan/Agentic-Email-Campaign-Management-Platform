# Email Campaign Management Platform — CLAUDE.md

Project guide for AI-assisted development. Read this before making any changes.

---

## Project Overview

A multi-tenant email campaign management platform with three sub-projects:

| Directory | Stack | Purpose |
|---|---|---|
| `backend/` | Django 5.2 + DRF | REST API + WebSocket server |
| `frontend/` | Next.js 16 + React 19 | Web dashboard |
| `mobile/` | Expo 55 + React Native 0.83 | Mobile app (Android/iOS) |

**Production URLs:**
- API: `https://emailcampaign-api.musfiqdehan.com/api/v1/`
- Frontend: `https://emailcampaign.musfiqdehan.com`
- API Docs (Swagger): `/api/v1/schemas/swagger-ui/`
- API Docs (ReDoc): `/api/v1/schemas/redoc`

---

## Backend

### Tech Stack

- **Django 5.2.8** — web framework
- **Django REST Framework 3.15.2** — REST API
- **Daphne 4** — ASGI server (HTTP + WebSocket)
- **Django Channels 4** — WebSocket support
- **channels-redis** — channel layer backend
- **SimpleJWT** — JWT authentication (access: 1 day, refresh: 7 days)
- **PostgreSQL 17** (via psycopg + psycopg2-binary)
- **Redis 7** — cache, Celery broker, channel layer
- **Celery 5.3.4** — async task queue
- **Django Celery Beat** — periodic/scheduled tasks (DatabaseScheduler)
- **drf-spectacular** — OpenAPI schema generation
- **Whitenoise** — static file serving
- **python-decouple** — `.env` configuration
- **Google Gemini API** — AI content generation
- **AWS SES** (django-ses) — email delivery provider
- **Twilio** — SMS and WhatsApp
- **py-vapid / pywebpush** — web push notifications
- **cryptography** — encrypted email provider credentials

### Project Structure

```
backend/
├── config/
│   ├── settings.py      # Django settings (all env-driven via decouple)
│   ├── urls.py          # Root URL conf
│   ├── celery.py        # Celery app configuration
│   ├── asgi.py          # ASGI application (HTTP + WebSocket routing)
│   └── wsgi.py
├── apps/
│   ├── authentication/  # User, Organization, Membership models + auth views
│   ├── campaigns/       # Core domain: campaigns, contacts, templates, providers
│   └── utils/           # Shared base models, pagination, mixins, responses
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml   # Local dev compose
└── .env.example
```

### App: `authentication`

Models:
- `User` (AbstractUser, UUID PK) — multi-org support, `unique_together=(email, organization)`
- `Organization` (UUID PK) — `custom_field_schema` (JSONField) for contact personalization variables
- `OrganizationMembership` — roles: `owner`, `admin`, `member`
- `EmailVerificationToken`, `PasswordResetToken`

Key behaviors:
- `User.is_platform_admin` — super-admin flag (separate from `is_staff`)
- `User.is_org_owner`, `User.is_org_admin` — computed properties
- `Organization.is_active` / `deactivation_reason` — org-level suspension

Auth endpoints (`/api/v1/auth/`):
```
POST signup/
POST login/
POST logout/
POST refresh/          # JWT token refresh
POST verify-email/
POST change-password/
POST request-password-reset/
POST reset-password/
GET/PUT profile/details/
```

### App: `campaigns`

**Models** (all under `apps/campaigns/models/`):

| Model | Key Fields | Notes |
|---|---|---|
| `Campaign` | `status`, `scheduled_at`, `contact_lists` (M2M), `email_provider`, inline `stats_*` fields | Lifecycle method: `launch()`, `pause()`, `resume()`, `cancel()` |
| `ContactList` | `subscription_token`, `double_opt_in`, denormalized stats | `unique_together=(organization, name)` |
| `Contact` | `email`, `status`, `custom_fields` (JSONField), `lists` (M2M) | Statuses: ACTIVE, UNSUBSCRIBED, BOUNCED, COMPLAINED, PENDING |
| `EmailTemplate` | `category`, `approval_status`, `is_global`, `organization` (nullable for global) | Versioning + approval workflow |
| `AutomationRule` | trigger rules for automated emails |  |
| `EmailDeliveryLog` | per-send tracking record |  |
| `OrganizationEmailProvider` | links org to shared providers |  |
| `PushSubscription` | VAPID web push endpoint, p256dh, auth |  |

**Campaign Status Lifecycle:**
```
DRAFT → SCHEDULED → SENDING → SENT
                 ↓         ↓
              PAUSED     FAILED
                 ↓
             CANCELLED
```
Scheduling uses Celery Beat (one-off `CrontabSchedule` + `PeriodicTask`).

**Template Approval Workflow:**
```
DRAFT → PENDING_APPROVAL → APPROVED
                         ↘ REJECTED
```

**Plan Tiers** (defined in `constants.py`):
- `FREE`, `BASIC`, `PROFESSIONAL`, `ENTERPRISE`
- Enforced limits: contacts_limit, campaigns_per_month, emails_per_day, etc.

**Campaign URL groups** (`/api/v1/campaigns/`):
1. Campaign management (CRUD + launch/pause/resume/cancel/preview/test-send/duplicate/analytics)
2. Contacts + Contact Lists (CRUD + bulk import + toggle status)
3. Email configuration (templates, org email config, providers)
4. Automation rules
5. Email delivery & tracking (queue, logs, validation, actions)
6. SMS/WhatsApp automation (configs + templates + triggers)
7. Admin/platform operations (requires `is_platform_admin`)
8. Public endpoints (unsubscribe, GDPR forget, public subscribe)
9. Notifications (list, mark read, delete)
10. Push notifications (subscribe/unsubscribe/test)
11. Template operations (use, duplicate, versioning, approval)
12. AI endpoints (`/ai/generate/email/content/`, `/ai/agent/contacts/`)
13. Variable management (list, extract, validate, preview, schema)

### `BaseModel` (apps/utils/base_models.py)

All domain models inherit from this:
- `created_at`, `updated_at`, `created_by`, `updated_by`
- `is_active`, `is_published`
- `is_deleted`, `deleted_at` — **soft delete** (default manager filters `is_deleted=False`)
- `objects = SoftDeleteManager()` — excludes soft-deleted by default
- `all_objects = Manager()` — includes deleted
- `delete()` → soft delete; `hard_delete()` → real delete; `restore()` → undo soft delete

### Settings Patterns

All settings use `python-decouple`. Required env vars:
```
SECRET_KEY, SIGNING_KEY
POSTGRES_ENGINE, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT
REDIS_PASSWORD, REDIS_HOST (default: "redis")
EMAIL_CONFIG_ENCRYPTION_KEY
GEMINI_API_KEY
VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_CLAIM_EMAIL
FRONTEND_URL, BACKEND_URL
```

See `backend/.env.example` for the complete reference.

### REST Framework Configuration

```python
DEFAULT_PAGINATION_CLASS = "PageNumberPagination"  # PAGE_SIZE = 10
DEFAULT_AUTHENTICATION_CLASSES = [JWTAuthentication]
DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]
DEFAULT_SCHEMA_CLASS = "drf_spectacular.openapi.AutoSchema"
EXCEPTION_HANDLER = "core.exceptions.custom_exception_handler"
```

Rate limits: `auth_burst: 20/min`, `auth_sustained: 100/day`, `organization: 500/min`, `email_sending: 60/min`

### Django Commands

```bash
# Database
python manage.py migrate
python manage.py makemigrations

# Custom management commands
python manage.py create_superuser
python manage.py create_platform_admin
python manage.py create_user_organizations
python manage.py assign_user_organization
python manage.py list_users_orgs
python manage.py generate_encryption_key
python manage.py sync_email_providers
python manage.py check_email_providers_health

# Run server (development)
daphne -p 8001 -b 0.0.0.0 config.asgi:application

# Celery
celery -A config.celery worker --loglevel=info
celery -A config.celery beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Testing

- **Framework:** pytest + pytest-django
- **Test location:** `apps/<app>/tests/` (e.g., `apps/campaigns/tests/`)
- **Coverage:** pytest-cov

```bash
cd backend
pytest
pytest --cov=apps
pytest apps/campaigns/tests/test_email_logs.py -v
```

### Code Style

- **formatter:** black (`black==23.12.0`)
- **import sorter:** isort
- **linter:** flake8
- **pre-commit:** configured (`.pre-commit-config.yaml` likely in root)

---

## Frontend

### Tech Stack

- **Next.js 16.1.1** — App Router
- **React 19.2.3**
- **TypeScript 5**
- **Tailwind CSS 4** — utility-first styling
- **Radix UI** — unstyled accessible components (shadcn UI pattern)
- **React Hook Form 7** + **Zod 4** — form validation
- **Axios 1.13** — HTTP client with JWT interceptor
- **js-cookie** — token storage (cookies)
- **next-themes** — dark/light mode
- **react-quill-new** — rich text/HTML email editor
- **sonner** — toast notifications
- **lucide-react** — icons
- **date-fns** — date utilities

### Project Structure

```
frontend/
├── app/               # Next.js App Router pages
│   ├── layout.tsx     # Root layout
│   ├── page.tsx       # Landing page (redirects to login/dashboard)
│   ├── login/
│   ├── signup/
│   ├── verify-email/
│   ├── reset-password/
│   └── dashboard/
│       ├── layout.tsx          # Dashboard shell (sidebar + header)
│       ├── page.tsx            # Dashboard home
│       ├── campaigns/          # Campaign list + detail + new
│       ├── contacts/           # Contact list + detail + import + new
│       ├── templates/          # Template list + edit + new
│       ├── settings/           # Settings + providers (CRUD)
│       ├── notifications/
│       ├── logs/
│       ├── profile/
│       ├── team/
│       └── admin/              # Platform admin panel
│           ├── page.tsx
│           ├── organizations/
│           ├── approvals/
│           └── templates/
├── components/
│   ├── ui/            # Radix/shadcn primitives
│   └── dashboard/     # Header, Sidebar, FloatingAgentInput, NotificationSettings
├── config/
│   ├── axios.ts       # Axios instance + JWT interceptor + auto-refresh
│   ├── constants.ts   # API URLs and app constants
│   ├── utils.ts       # Utility functions
│   └── template-utils.ts  # Template variable helpers
├── services/
│   ├── auth.ts        # Login, signup, logout, profile
│   ├── campaigns.ts   # Campaign, contact, template API calls
│   └── notifications.ts
└── next.config.ts
```

### API Client Pattern

`config/axios.ts` creates an axios instance with:
- Base URL: `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1'`
- Request interceptor: reads `access_token` from cookies → adds `Authorization: Bearer <token>`
- Response interceptor: on 401, auto-refreshes using `refresh_token` cookie; on failure, clears cookies and redirects to `/login`

Token storage: `access_token` and `refresh_token` in cookies. User data in `localStorage` under key `user`.

### Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8001
NEXT_PUBLIC_VAPID_PUBLIC_KEY=
```

### Development Commands

```bash
cd frontend
npm run dev    # Start dev server (port 3001 by default)
npm run build  # Production build
npm run start  # Run production build
npm run lint   # ESLint
```

---

## Mobile

### Tech Stack

- **Expo 55** (expo-router 55 for file-based routing)
- **React Native 0.83.2**
- **React 19.2**
- **TypeScript ~5.9**
- **expo-secure-store** — secure token storage (replaces cookies)
- **axios 1.7** — HTTP client with JWT interceptor
- **@react-native-async-storage/async-storage** — general storage
- **expo-image-picker** — avatar/photo upload
- **react-native-reanimated 4** + **react-native-gesture-handler** — animations

### Project Structure

```
mobile/
├── app/
│   ├── _layout.tsx           # Root layout (auth state check)
│   ├── index.tsx             # Entry redirect
│   ├── (auth)/               # Auth screens (unauthenticated)
│   │   ├── _layout.tsx
│   │   ├── login.tsx
│   │   ├── signup.tsx
│   │   ├── forgot-password.tsx
│   │   ├── reset-password.tsx
│   │   └── verify-email.tsx
│   └── (tabs)/               # Main app screens (authenticated)
│       ├── _layout.tsx       # Tab bar configuration
│       ├── dashboard.tsx
│       ├── campaigns.tsx
│       ├── campaign/[id].tsx
│       ├── contacts.tsx
│       ├── contact-list/[id].tsx
│       ├── templates.tsx
│       ├── template/[id].tsx
│       ├── notifications.tsx
│       └── profile.tsx
├── components/ui/            # Reusable UI components (Button, Input, Card, Badge, etc.)
├── services/                 # API service modules
│   ├── auth.ts
│   ├── campaigns.ts
│   ├── contacts.ts
│   ├── templates.ts
│   ├── notifications.ts
│   └── profile.ts
├── config/
│   ├── axios.ts              # Axios instance + SecureStore JWT interceptor
│   └── constants.ts          # API_URL and other constants
├── app.json                  # Expo app configuration
└── eas.json                  # EAS Build configuration
```

### Key Differences from Frontend

- Tokens stored in `expo-secure-store` (not cookies)
- axios interceptor is `async` (SecureStore is async)
- Navigation uses Expo Router route groups: `(auth)` and `(tabs)`
- Build profiles: `development`, `preview` (via EAS)

### Development Commands

```bash
cd mobile
npx expo start              # Start Expo development server
npx expo run:android        # Run on Android emulator/device
npx expo run:ios            # Run on iOS simulator (macOS only)
npx expo start --web        # Run in browser

# EAS builds
npx eas build --profile development --platform android
npx eas build --profile preview --platform android
```

---

## Infrastructure & Deployment

### Docker Services

| Service | Container | Image | Port |
|---|---|---|---|
| Nginx | `nginx-ecmp` | nginx:1.27-alpine | 80, 443 |
| Django (Daphne) | `backend-ecmp` | ecmp/backend:latest | 8001 (internal) |
| Celery Worker | `celery-ecmp` | ecmp/backend:latest | — |
| Celery Beat | `celery-beat-ecmp` | ecmp/backend:latest | — |
| Next.js | `frontend-ecmp` | ecmp/frontend:latest | 3001 (internal) |
| PostgreSQL | `db-ecmp` | postgres:17.5-alpine | 5441→5432 (local) |
| Redis | `redis-ecmp` | redis:7-alpine | 6391→6379 (local) |

Network: `ecmp_network` (bridge; Docker service name DNS for inter-service communication).

### Local Development

```bash
# Start all services
cd backend && docker compose up -d --build

# Or start the full production stack
docker compose up -d --build

# View logs
docker compose logs -f backend
docker compose logs -f celery
```

### Production Stack

Root `docker-compose.yml` deploys the full stack:
- Nginx handles SSL termination (Cloudflare Origin Certificate)
- Static/media files served by Nginx directly
- `frontend-newsletter/` directory served at a separate path for newsletter landing page
- All services share `ecmp_network`

### Health Checks

- Backend: `GET /api/v1/healthz/` (django-health-check)
- Nginx: `GET /nginx-health`

---

## Architecture Patterns

### Multi-Tenancy (Organization-Scoped)

Every significant resource belongs to an `Organization`. When writing queries:
- Always filter by `organization` (usually from `request.user.organization`)
- Platform admins (`is_platform_admin=True`) can see all organizations

### UUID Primary Keys

All main domain models use `UUIDField(primary_key=True, default=uuid4, editable=False)`. URL patterns use `<uuid:pk>`.

### Soft Delete

Do not use `.delete()` for data you want to archive. Use `BaseModel.delete()` (soft) or `hard_delete()`. The default manager filters out `is_deleted=True`.

### Async Task Pattern

For bulk or slow operations:
1. API view validates, creates a record (e.g., Campaign with `SENDING` status), returns 202
2. Celery task picks it up and processes asynchronously
3. WebSocket (Django Channels) pushes real-time status updates to the frontend

### Email Provider Hierarchy

Three levels of email providers:
1. **Platform shared providers** — managed by platform admins, visible to all orgs
2. **Organization-linked providers** — org admins link a shared provider to their org
3. **Organization-owned providers** — org creates their own SMTP/SES/provider config (credentials encrypted via `EMAIL_CONFIG_ENCRYPTION_KEY`)

### Campaign Sending

1. User launches campaign → `Campaign.launch()` → sets status to `SENDING`, dispatches `launch_campaign_task`
2. Celery task iterates contacts in `batch_size` chunks with `batch_delay_seconds` between batches
3. Each email creates an `EmailDeliveryLog` record
4. Stats are denormalized to `Campaign.stats_*` fields (aggregated via `update_stats_from_logs()`)

### Template Personalization Variables

Templates use `{{variable_name}}` syntax. Variables can be:
- Standard: `{{first_name}}`, `{{last_name}}`, `{{email}}`, `{{full_name}}`
- Custom: defined in `Organization.custom_field_schema` (JSONField array)
- Rendered via `apps/campaigns/utils/template_utils.py` and `variable_registry.py`

---

## Key Files Quick Reference

| File | Purpose |
|---|---|
| `backend/config/settings.py` | All Django/service configuration |
| `backend/config/urls.py` | Root URL routing |
| `backend/apps/authentication/models.py` | User, Organization, Membership |
| `backend/apps/campaigns/models/campaign_models.py` | Campaign model + lifecycle methods |
| `backend/apps/campaigns/models/contact_models.py` | ContactList + Contact models |
| `backend/apps/campaigns/models/email_config_models.py` | EmailTemplate model |
| `backend/apps/campaigns/tasks.py` | Celery tasks for sending |
| `backend/apps/campaigns/urls.py` | All 15 URL sections for campaigns app |
| `backend/apps/utils/base_models.py` | BaseModel (soft delete, timestamps) |
| `backend/apps/campaigns/constants.py` | Plan limits, status choices |
| `frontend/config/axios.ts` | API client with auto token refresh |
| `frontend/app/dashboard/layout.tsx` | Dashboard shell layout |
| `mobile/config/axios.ts` | Mobile API client (SecureStore tokens) |
| `mobile/app/_layout.tsx` | Root auth state check |

---

## Common Development Tasks

### Adding a New Backend Endpoint

1. Create view in `apps/campaigns/views/` (use `APIView` — this project prefers explicit `APIView` over `ViewSet`)
2. Add URL pattern to `apps/campaigns/urls.py` in the relevant section
3. Add serializer in `apps/campaigns/serializers/` if needed
4. Run migrations if models changed: `python manage.py makemigrations && python manage.py migrate`

### Adding a New Model

1. Inherit from `BaseModel` (soft delete, timestamps)
2. Use `UUIDField(primary_key=True, ...)` for PK
3. Always include an `organization` ForeignKey for multi-tenant scoping
4. Add `db_table` in Meta for explicit table naming
5. Add `indexes` in Meta for expected query patterns

### Adding a Frontend Page

1. Create page file in the appropriate `app/dashboard/` subdirectory
2. Use the axios instance from `config/axios.ts` (never use `fetch` directly)
3. Add form validation with React Hook Form + Zod
4. Use UI components from `components/ui/` (Radix-based)
5. Use `sonner` toast for success/error notifications

### Running the Full Stack Locally

```bash
# 1. Create the Docker network (first time only)
docker network create ecmp_network

# 2. Start backend services
cd backend
cp .env.example .env  # Fill in values
docker compose up -d --build

# 3. Run migrations
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py create_superuser

# 4. Start frontend
cd ../frontend
cp .env.local.example .env.local  # If exists, or create manually
npm install
npm run dev  # Runs on http://localhost:3001

# 5. Start mobile (optional)
cd ../mobile
npm install
npx expo start
```

### Encryption Key Setup

For encrypted email provider credentials:
```bash
cd backend
python manage.py generate_encryption_key
# Copy output to EMAIL_CONFIG_ENCRYPTION_KEY in .env
```

---

## Testing Strategy

### Backend Tests

- Location: `apps/<app>/tests/`
- Uses `django.test.TestCase` + `pytest`
- Test data created in `setUp()` — no fixtures
- Mock external services (email, SMS) with `unittest.mock.patch`
- Run: `pytest` from `backend/` directory

### Frontend Tests

- No test framework currently configured (test runner not in `package.json` scripts)
- Manual testing via Swagger UI at `/api/v1/schemas/swagger-ui/`

---

## Important Conventions

1. **API responses**: Use custom response helpers from `apps/utils/responses.py` (not raw DRF Response)
2. **Permissions**: Check `request.user.organization` before any data access; use `apps/authentication/permissions.py`
3. **Pagination**: Default 10 items/page via `PageNumberPagination`
4. **Soft delete vs hard delete**: Always use soft delete unless explicitly requested
5. **Organization filtering**: Every queryset for org-scoped resources must be filtered by `organization=request.user.organization`
6. **UUID URLs**: All detail views use `<uuid:pk>/` in URL patterns
7. **Celery tasks**: Import inside functions (`from ..tasks import ...`) to avoid circular imports
8. **Timezone**: Server timezone is `Asia/Dhaka` (`USE_TZ = False` — naive datetimes)
9. **Frontend tokens**: `access_token` and `refresh_token` stored as cookies; `user` object in `localStorage`
10. **Mobile tokens**: Use `expo-secure-store` for all token storage (SecureStore is async — await all calls)
