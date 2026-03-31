Run Django database migrations for the backend.

Step 1 — create migration files (if models changed):
  python manage.py makemigrations $ARGUMENTS

Step 2 — apply migrations:
  python manage.py migrate

Step 3 — verify:
  python manage.py showmigrations

Docker alternative:
  docker compose exec backend python manage.py makemigrations
  docker compose exec backend python manage.py migrate

Never squash migrations already deployed to production.
Working directory: `/home/musfiqdehan/Products/Email-Campaign-Management-Platform/backend`
