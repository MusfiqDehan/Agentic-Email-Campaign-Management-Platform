# 📧 Email Campaign Management Platform

A multi-tenant, AI-assisted email (and SMS) campaign management platform. Organizations manage contacts, build reusable templates, run bulk campaigns across multiple providers (AWS SES, Gmail/Outlook SMTP), and get real-time delivery notifications — with generative AI template creation and an agentic, natural-language contact-management assistant built in.

**Live Demo:** https://emailcampaign.musfiqdehan.com

![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![Django](https://img.shields.io/badge/Django-5.2-092E20.svg)
![Next.js](https://img.shields.io/badge/Next.js-16-black.svg)
![React](https://img.shields.io/badge/React-19-61DAFB.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6.svg)

![Homepage of website](frontend/public/screenshot.png)

---

## 📑 Table of Contents

- [Project Overview](#-project-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
  - [Root Directory](#root-directory)
  - [Backend (`backend/`)](#backend-backend)
  - [Frontend (`frontend/`)](#frontend-frontend)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Variables](#environment-variables)
- [Running Locally (Manual Setup)](#-running-locally-manual-setup)
  - [1. Backend (Django)](#1-backend-django)
  - [2. Frontend (Next.js)](#2-frontend-nextjs)
  - [3. Background Workers (Celery)](#3-background-workers-celery)
- [Running with Docker](#-running-with-docker)
  - [Per-service Compose (local development)](#per-service-compose-local-development)
  - [Unified Production Compose](#unified-production-compose)
- [API Documentation](#-api-documentation)
- [Testing & Linting](#-testing--linting)
- [AI Tools Used](#-ai-tools-used)
- [Key Learnings](#-key-learnings)
- [Areas for Improvement](#-areas-for-improvement)
- [License](#-license)

---

## 🧭 Project Overview

This is an end-to-end **Email Campaign Management Platform** that allows organizations to manage contacts, create reusable templates, launch bulk email/SMS campaigns, and monitor delivery progress from a single system. It's built as a production-style **multi-tenant** application — each organization owns its own contacts, templates, providers, and campaigns, with role-based membership (owner/admin/member).

Beyond core campaign management, the platform includes:

- **Generative AI** support for email template creation (Gemini, with a DeepSeek fallback)
- An **agentic, natural-language contact-management** endpoint — manage contacts by describing what you want in plain English
- A **bidirectional mailbox** with first-party email open/click tracking
- **Multi-provider** sending (AWS SES, Gmail/Outlook SMTP) resolved per-organization at send time
- **Real-time** in-app and web-push notifications over WebSockets

---

## ✨ Features

### 🎯 Campaign Management
- Create, schedule, launch, pause, resume, cancel, and duplicate email campaigns
- Test-send and live preview before launch
- Per-campaign analytics with delivery/open/click stats and stat refresh

### 👥 Contact Management
- Contacts and contact lists with bulk CSV import
- Agentic, natural-language contact operations (create/update/search contacts via AI)
- Contact segmentation and list-level stats

### 📝 Templates
- Rich HTML template editor with dynamic personalization variables
- AI-generated template content (Gemini primary, DeepSeek fallback)
- Template categories, admin-curated templates, and previews

### 📬 Multi-Provider Email Delivery
- AWS SES and Gmail/Outlook SMTP, resolved per-organization via a config hierarchy
- Encrypted storage of provider credentials
- Provider health checks and rate/quota limiting (per-second/minute/hour/day)
- Delivery event webhooks from SES, SendGrid, and Brevo, plus a delivery log with resend/forward

### 📥 Mailbox & Tracking
- Bidirectional mailbox sync (send & receive) with a message inbox
- First-party open/click tracking pixels & redirect links

### 🔁 Automation
- Rule-based automation for triggered emails
- SMS and WhatsApp trigger campaigns (via Twilio)

### 🔔 Real-Time Notifications
- WebSocket-based in-app notifications (Django Channels)
- Web push notifications (VAPID)

### 🏢 Multi-Tenancy & Admin
- Organizations, membership roles (owner/admin/member), and per-org settings
- Platform-admin views for cross-tenant provider/organization management

### 🎨 Modern UI/UX
- Responsive dashboard with dark/light theme (system-aware)
- Animated, interactive landing page (SVG micro-interactions, pricing, growth/process visuals)

### 🔐 Security
- JWT authentication (access + refresh) with real DB-backed users
- Encrypted provider credentials, soft-delete on core models, org-scoped permissions

---

## 🛠 Tech Stack

### Backend

| Technology | Purpose |
|---|---|
| **Python 3.12** | Core language |
| **Django 5.2** + **DRF 3.15** | Web framework & REST API |
| **PostgreSQL** | Primary database |
| **Redis** | Celery broker/result backend & Channels layer |
| **Celery 5.3** + **Celery Beat** | Async & scheduled tasks (bulk email/SMS, automation) |
| **Django Channels** + **Daphne** | WebSocket notifications (ASGI) |
| **SimpleJWT** | JWT authentication |
| **drf-spectacular** | OpenAPI schema, Swagger UI, ReDoc |
| **django-ses**, **boto3** | AWS SES email provider |
| **Twilio** | SMS / WhatsApp sending |
| **SendGrid**, Brevo webhooks | Alternate delivery provider + inbound/event webhooks |
| **pywebpush** / **py-vapid** | Web push notifications |
| **google-genai** (Gemini) | AI template generation & the agentic contact assistant |
| **django-health-check** | `/api/v1/healthz/` liveness endpoint |
| **Gunicorn** / **Daphne** | Production servers (WSGI/ASGI) |
| **pytest**, **flake8**, **black** | Testing & code quality |

### Frontend

| Technology | Purpose |
|---|---|
| **Next.js 16** (App Router) | React framework |
| **React 19** + **TypeScript 5** | UI & type safety |
| **Tailwind CSS 4** | Styling |
| **Radix UI** + `class-variance-authority` | Accessible UI primitives (shadcn/ui-style) |
| **React Hook Form** + **Zod** | Forms & validation |
| **next-themes** | Dark/light theming |
| **Axios** | HTTP client |
| **React Quill (new)** | Rich text template editor |
| **Sonner** | Toast notifications |
| **Lucide React** | Icons |

### DevOps & Tooling

| Technology | Purpose |
|---|---|
| **Docker** / **Docker Compose** | Containerization (per-service & unified) |
| **Traefik** | Reverse proxy & TLS termination in production |
| **GitHub Actions** | CI (`check`, migration check, `manage.py test --parallel` against Postgres+Redis service containers) |
| **Nginx** | Static/reverse-proxy config for select deployments |

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                             │
│  Next.js 16 (React 19 + TypeScript)                               │
│  App Router · Tailwind + Radix UI · Axios · WebSocket hooks       │
└──────────────────────────────────────────────────────────────────┘
                               │  REST (JSON) + WebSocket
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                            API LAYER                               │
│  Django REST Framework · JWT Auth · Org-scoped permissions        │
│  Django Channels (ws/notifications/) served over Daphne (ASGI)    │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                       APPLICATION LAYER (apps.campaigns)           │
│  Campaigns · Contacts · Templates · Providers · Automation        │
│  Mailbox & Tracking · SMS/WhatsApp · Notifications · Admin         │
└──────────────────────────────────────────────────────────────────┘
                │                     │                     │
                ▼                     ▼                     ▼
      ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
      │   PostgreSQL     │   │      Redis       │   │      Celery      │
      │   (database)     │   │ (broker/cache/   │   │ (async & beat    │
      │                  │   │  channel layer)  │   │  scheduled tasks)│
      └─────────────────┘   └─────────────────┘   └─────────────────┘
                                                             │
                                                             ▼
                                          ┌───────────────────────────────┐
                                          │  AWS SES · Gmail/Outlook SMTP  │
                                          │  Twilio (SMS/WhatsApp)          │
                                          │  SendGrid / Brevo webhooks      │
                                          └───────────────────────────────┘
```

Email sending flow: organization config → `hierarchy_resolver` resolves the effective provider config → `ProviderBackendResolver` builds the right Django email backend → `unified_email_sender` sends it — one code path supporting SES, SMTP, or console/test sending interchangeably.

---

## 📁 Project Structure

### Root Directory

```
Email-Campaign-Management-Platform/
├── README.md                 # This file
├── DEPLOYMENT.md             # Full production/VPS deployment guide (Traefik + Cloudflare)
├── LICENSE                   # Apache 2.0
├── docker-compose.yml        # Unified production stack (Postgres, Redis, backend, Celery, frontend)
├── .env.example               # Environment variable reference for the unified compose
├── backend/                   # Django REST API
├── frontend/                  # Next.js dashboard & landing site
├── frontend-newsletter/       # Static embeddable newsletter signup widget
├── mobile/                    # Expo scaffold (minimal/unused)
└── nginx/                     # Reverse proxy config for select deployments
```

### Backend (`backend/`)

```
backend/
├── manage.py
├── requirements.txt
├── Dockerfile / docker-compose.yml / docker_entrypoint.sh
├── config/                    # Django project config
│   ├── settings.py
│   ├── urls.py                # /api/v1/auth, /api/v1/campaigns, /api/v1/healthz, /api/v1/schemas
│   ├── asgi.py                # Channels ProtocolTypeRouter (WebSocket)
│   ├── wsgi.py
│   └── celery.py
├── core/                       # Response envelope & centralized exception handling
│   ├── mixins.py               # ResponseMixin (aliased as CustomResponseMixin)
│   ├── exceptions.py           # custom_exception_handler (DRF EXCEPTION_HANDLER)
│   └── utils.py
├── apps/
│   ├── authentication/         # User, Organization, OrganizationMembership, JWT, permissions
│   │   ├── models.py / views.py / serializers.py / permissions.py / signals.py
│   │   ├── services/
│   │   └── management/commands/   # create_superuser, create_platform_admin,
│   │                                 create_user_organizations, assign_user_organization, list_users_orgs
│   ├── campaigns/               # Core app — the bulk of the business logic
│   │   ├── models/               # campaign, contact, email_config, provider, automation_rule,
│   │   │                            email_tracking, notification, push, sms_config, mailbox, org_email_config
│   │   ├── views/                 # campaign, admin, enhanced, template_operations, admin_templates,
│   │   │                            organization_admin, notification, push, sms_automation,
│   │   │                            email_automation, variable, ai_gen, contact_agent, mailbox,
│   │   │                            tracking, provider_webhooks, unsubscribe, debug
│   │   ├── serializers/           # campaign, admin, enhanced, push, mailbox, base
│   │   ├── utils/                  # email_providers, unified_email_sender, hierarchy_resolver,
│   │   │                            tenant_service, crypto, template_utils, variable_registry,
│   │   │                            ai_client, sms_utils, push_utils, mailbox_sync, email_tracking
│   │   ├── management/commands/   # generate_encryption_key, sync_email_providers,
│   │   │                            check_email_providers_health
│   │   ├── tasks.py                # Celery tasks for async/bulk sending
│   │   ├── backends.py             # ProviderBackendResolver (SES/SMTP/console)
│   │   ├── consumers.py / routing.py  # WebSocket notification consumer
│   │   ├── ses_event_handlers.py
│   │   └── migrations/
│   ├── notifications/, platform_admins/, template_managers/   # placeholder apps (not wired up)
│   └── utils/                   # BaseModel (soft-delete), pagination, filters, throttles, mixins
├── static/ · staticfiles/       # Collected static assets
└── media/ · media_files/        # User-uploaded assets (logos, profile images)
```

> `apps.notifications`, `apps.platform_admins`, and `apps.template_managers` are empty placeholder
> directories — notification and admin functionality actually lives inside `apps.campaigns`.

### Frontend (`frontend/`)

```
frontend/
├── package.json / tsconfig.json / next.config.ts / eslint.config.mjs
├── Dockerfile / docker-compose.yml
├── app/                          # Next.js App Router
│   ├── page.tsx                  # Marketing landing page
│   ├── layout.tsx / globals.css
│   ├── login/ · signup/ · reset-password/ · verify-email/ · unsubscribe/
│   └── dashboard/                # Authenticated app
│       ├── layout.tsx / page.tsx
│       ├── campaigns/ · contacts/ · templates/ · inbox/
│       ├── logs/ · notifications/ · team/ · admin/
│       └── settings/ · profile/
├── components/
│   ├── ui/                       # Radix-based primitives (button, dialog, table, tabs, ...)
│   ├── dashboard/                # sidebar, header, notification settings, floating AI agent input
│   ├── landing/                  # Animated SVG landing sections (hero, growth chart, network bg, ...)
│   ├── brand-logo.tsx / editor.tsx / providers.tsx
├── config/                       # axios client, constants, template & general utils
├── contexts/                     # AuthContext
├── hooks/                        # useNotifications, usePushNotifications, useRealtimeUpdates, ...
├── services/                     # auth.ts, campaigns.ts, notifications.ts — thin API wrappers
└── public/                       # Static assets (logo, icons, service worker)
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**
- **Node.js 20+** and npm
- **PostgreSQL** (14+) and **Redis** (7+) — locally installed, or run via Docker (see below)
- **Docker** + **Docker Compose** (optional, for the containerized workflow)

### Environment Variables

The backend and frontend each read from their own `.env` files, plus the repo root has a `.env.example` used by the unified Docker Compose stack. Copy the example and fill in values before running anything:

```bash
cp .env.example .env               # for the unified/root docker-compose.yml
cp backend/.env.example backend/.env
```

Key variable groups (see `.env.example` for the full list with comments):

| Group | Variables |
|---|---|
| Django core | `DEBUG`, `SECRET_KEY`, `SIGNING_KEY`, `EMAIL_CONFIG_ENCRYPTION_KEY`, `ALLOWED_HOSTS` |
| PostgreSQL | `POSTGRES_ENGINE`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` |
| Redis | `REDIS_HOST`, `REDIS_PASSWORD` |
| Frontend build args | `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL`, `NEXT_PUBLIC_VAPID_PUBLIC_KEY` |
| Email / SMTP / SES | `EMAIL_BACKEND`, `EMAIL_HOST(_USER/_PASSWORD)`, `EMAIL_PORT`, `EMAIL_USE_TLS/SSL`, `DEFAULT_FROM_EMAIL` |
| Web push (VAPID) | `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_CLAIM_EMAIL` |
| AI providers | `GEMINI_API_KEY`, `DEEPSEEK_API_KEY` (fallback) |
| Sending limits | `ORG_PROVIDER_MAX_RATE_PER_SECOND/MINUTE/HOUR`, `ORG_PROVIDER_MAX_DAILY_QUOTA` |
| Bootstrap superuser | `DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD/FIRST_NAME/LAST_NAME` |

Generate the required secrets with:

```bash
# EMAIL_CONFIG_ENCRYPTION_KEY
python manage.py generate_encryption_key

# SECRET_KEY / SIGNING_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# VAPID keys (web push)
python -c "from py_vapid import Vapid; v = Vapid(); v.generate_keys(); print(v.private_pem().decode()); print(v.public_key)"
```

---

## 💻 Running Locally (Manual Setup)

### 1. Backend (Django)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env               # then fill in DB/Redis/secret values

# Make sure PostgreSQL & Redis are running and reachable per your .env

python manage.py migrate
python manage.py create_superuser --username admin --email admin@example.com --password <password> --force
python manage.py create_user_organizations   # backfill an org for the new user, if needed

python manage.py runserver 8001    # plain dev server — fine for non-WebSocket work
# or, to exercise WebSocket notifications:
daphne -p 8001 -b 0.0.0.0 config.asgi:application
```

> The checked-in `frontend/.env.local` already points to `http://localhost:8001` — running the backend on
> port `8001` (as above) means the frontend works with zero extra config. Use plain `runserver` on its
> default port 8000 instead and the frontend just needs `NEXT_PUBLIC_API_URL`/`NEXT_PUBLIC_WS_URL` updated
> to match.

The API is now available at `http://localhost:8001/api/v1/`.

### 2. Frontend (Next.js)

```bash
cd frontend
npm install                        # use `npm ci --legacy-peer-deps` if npm complains (React 19 peer deps)
# frontend/.env.local already sets NEXT_PUBLIC_API_URL / NEXT_PUBLIC_WS_URL to http://localhost:8001 — edit if needed

npm run dev
```

The dashboard is now available at `http://localhost:3000`.

### 3. Background Workers (Celery)

Required for bulk email sending and scheduled automation — run these alongside the backend:

```bash
cd backend
celery -A config.celery worker --loglevel=info
celery -A config.celery beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## 🐳 Running with Docker

### Per-service Compose (local development)

Each app ships its own `docker-compose.yml` for spinning it up in isolation. Both reference an **external** Docker network, so create it once before the first run:

```bash
# Backend — Django, PostgreSQL, Redis, Celery worker & beat
cd backend
cp .env.example .env
docker network create dokploy-network      # skip if it already exists
docker compose up -d --build

docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py create_superuser --username admin --email admin@example.com --password <password> --force
docker compose logs -f backend
```

- API → `http://localhost:8001/api/v1/`
- PostgreSQL → `localhost:5441`, Redis → `localhost:6391`

```bash
# Frontend — Next.js (standalone build)
cd frontend
docker network create ecmp_network         # skip if it already exists
docker compose up -d --build
```

- App → `http://localhost:3001` (defaults to talking to the backend above via `NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1`)

Stop either stack with `docker compose down` from its directory.

### Unified Production Compose

The root [`docker-compose.yml`](docker-compose.yml) builds the **full stack** (PostgreSQL, Redis, backend on Daphne, Celery worker + beat, and the frontend) as it's actually deployed in production — fronted by **Traefik** on an external `traefik_proxy` network, with the app services only `expose`d (not published) to the host. It expects Cloudflare Origin TLS certs at `nginx/certs/` and a real reverse proxy in front of it, so it isn't meant to be run standalone on a laptop.

For the full VPS deployment walkthrough (DNS, certs, firewall, `docker compose up -d --build`, health checks, and troubleshooting), see **[DEPLOYMENT.md](DEPLOYMENT.md)**.

---

## 📚 API Documentation

Once the backend is running (adjust the port to match how you started it — `8001` in the examples above):

- **Swagger UI** — `http://localhost:8001/api/v1/schemas/swagger-ui/`
- **ReDoc** — `http://localhost:8001/api/v1/schemas/redoc`
- **OpenAPI schema (JSON)** — `http://localhost:8001/api/v1/schemas/swagger.json`
- **Health check** — `http://localhost:8001/api/v1/healthz/`

All application endpoints are namespaced under `/api/v1/auth/` (authentication) and `/api/v1/campaigns/` (campaigns, contacts, templates, providers, automation, SMS, mailbox, tracking, webhooks, admin).

---

## ✅ Testing & Linting

```bash
# Backend (Django's own test runner, not pytest, despite pytest-django being installed)
cd backend
python manage.py test
python manage.py test apps.campaigns.tests.test_email_logs
python manage.py check
python manage.py migrate --check --dry-run
flake8
black --check .

# Frontend
cd frontend
npm run lint
npx tsc --noEmit
```

CI (`.github/workflows/deploy.yml`) runs the same `check` → migration check → `manage.py test --verbosity=2 --parallel` sequence against Postgres + Redis service containers — mirror that locally before opening a PR.

---

## 🤖 AI Tools Used

- **Claude Code CLI** — code generation, problem-solving, and architectural guidance
- **GitHub Copilot** — real-time code suggestions and productivity improvements

---

## 📖 Key Learnings

During development, this project was an exercise in both system design and real-world production challenges:

**AI Integration**
- Integrated GenAI features across frontend and backend within an existing codebase
- Designed workflows for AI-assisted template generation and natural-language-driven operations

**Email Campaign System Design**
- Studied industry-standard email marketing platforms to understand campaign workflows and best practices
- Implemented dynamic email templates with variables and trigger-based campaign execution
- Built subscriber collection mechanisms using external APIs

**Email Infrastructure & Deliverability**
- Integrated **AWS SES** for scalable email automation
- Supported multiple email providers (SES, Gmail SMTP) with dynamic, per-organization provider selection
- Applied DNS-level configuration (SPF, DKIM, DMARC) to improve deliverability and avoid spam classification

**Backend Engineering & Scalability**
- Designed asynchronous email processing with **Celery** for bulk delivery
- Implemented real-time notifications using **WebSockets** for in-app and push notifications

**DevOps & Deployment**
- Deployed frontend and backend behind **Traefik**/**Nginx** on a cloud VPS
- Managed static assets and backups
- Built CI/CD pipelines with **GitHub Actions** for automated testing and deployment

**Security & Best Practices**
- Implemented unsubscribe mechanisms and email compliance standards
- Applied best practices for secure email template rendering, credential encryption, and campaign execution

---

## 🔭 Areas for Improvement

- Expanding support for additional email providers beyond AWS SES and Gmail/Outlook SMTP
- Extending agentic (AI-driven) capabilities across more workflows within the platform
- Enhancing analytics with additional metrics — bounce rate, deliverability scoring, cohort engagement, etc.
- Wiring up the currently-placeholder `apps.notifications`, `apps.platform_admins`, and `apps.template_managers` apps

---

## 📄 License

Licensed under the **Apache License 2.0** — see [LICENSE](LICENSE) for details.
