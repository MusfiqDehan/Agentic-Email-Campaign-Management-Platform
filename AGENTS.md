# AGENTS.md

## Cursor Cloud specific instructions

This repo is an **Email Campaign Management Platform**: a Django (DRF + Channels/ASGI) backend, a
Next.js admin dashboard, and a static newsletter page. The intended orchestration is Docker Compose,
but the Cloud Agent environment runs the services **natively** (no Docker). The update script only
refreshes dependencies — services and datastores must be started manually per the notes below.

### Services & how to run them (dev mode)

Datastores are installed but there is **no systemd**, so start them manually each fresh VM:

- PostgreSQL 16: `sudo pg_ctlcluster 16 main start` (listens on `localhost:5432`).
- Redis 7 (a password is required by Django settings): `sudo redis-server --daemonize yes --requirepass redis_password --port 6379`.

Backend (from `backend/`, venv at `backend/.venv`):

- Migrate / bootstrap admin user: `python manage.py migrate` then the commands in `backend/docker_entrypoint.sh` (`create_superuser`, `create_platform_admin`, `create_user_organizations`).
- Run the API with **Daphne (ASGI)** — do not use `runserver`, WebSockets/Channels need ASGI: `daphne -p 8001 -b 0.0.0.0 config.asgi:application`.
- Celery worker (required for campaigns to actually send): `celery -A config.celery worker --loglevel=info`.
- Celery Beat (only for scheduled/periodic tasks): `celery -A config.celery beat --loglevel=info`.

Frontend (from `frontend/`):

- `npm run dev -- -p 3001`. **Use port 3001**, not the default 3000 — only `:3001`/`:8001` origins are whitelisted in `backend/config/settings.py` (CORS/CSRF). The dev defaults already point the app at `http://localhost:8001/api/v1` and `ws://localhost:8001`, so no frontend `.env` is needed.

Default local admin login: `admin@example.com` / `changeme123`. Health check: `http://localhost:8001/api/v1/healthz/`. API docs: `http://localhost:8001/api/v1/schemas/swagger-ui/`.

### Non-obvious gotchas

- **`backend/.env` is required and gitignored.** Django uses `python-decouple`, which raises at import if `SECRET_KEY`, `SIGNING_KEY`, `REDIS_PASSWORD`, or the `POSTGRES_*` vars are missing. For native runs, `POSTGRES_HOST` and `REDIS_HOST` must be `localhost` (the committed `.env.example` uses the Docker service names `db-ecmp`/`redis-ecmp`, which do **not** resolve natively). If `backend/.env` is missing, recreate it from `backend/.env.example` with `POSTGRES_HOST=localhost`, `REDIS_HOST=localhost`, `REDIS_PASSWORD=redis_password`, real `SECRET_KEY`/`SIGNING_KEY` values, and (for local dev) `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` so campaign emails print to the Celery/backend logs instead of needing SMTP creds.
- The Postgres database name is `db-ecmp` (contains a hyphen — quote it in `createdb`/`psql`).
- `backend/docker-compose.yml`'s `backend` service passes `DB_NAME`/`DB_USER` env vars, but `settings.py` actually reads `POSTGRES_DB`/`POSTGRES_USER`/etc. — set the `POSTGRES_*` names in `.env`.
- External integrations (AWS SES/SMTP, Twilio, Gemini/DeepSeek, VAPID web push, Sentry) degrade gracefully with blank keys; only configure them to test those specific features.

### Testing

- Frontend lint: `npm run lint` in `frontend/`. It runs cleanly but reports **pre-existing** lint errors/warnings in the committed code (mostly `no-explicit-any`); these are not environment problems.
- Backend tests: `pytest`/`pytest-django` and `manage.py test` are installed but the committed suite under `apps/campaigns/tests/` is **pre-existing-broken** — modules import `campaigns.*` while `INSTALLED_APPS` uses `apps.campaigns`, the `tests/` dir lacks `__init__.py`, and `apps/authentication/tests.py` is empty. Fixing requires source changes; do not treat these collection errors as an environment issue.
