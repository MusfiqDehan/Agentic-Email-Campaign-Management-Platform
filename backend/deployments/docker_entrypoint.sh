set -euo pipefail

if [ -f .env ]; then
    # shellcheck disable=SC1091
    source .env
fi

python manage.py makemigrations --noinput
python manage.py migrate
python manage.py collectstatic --noinput

# Optional bootstrap (recommended only for first deploy / controlled environments)
if [ "${DJANGO_SUPERUSER_USERNAME:-}" != "" ] && [ "${DJANGO_SUPERUSER_EMAIL:-}" != "" ] && [ "${DJANGO_SUPERUSER_PASSWORD:-}" != "" ]; then
    python manage.py create_superuser \
        --username "${DJANGO_SUPERUSER_USERNAME}" \
        --email "${DJANGO_SUPERUSER_EMAIL}" \
        --password "${DJANGO_SUPERUSER_PASSWORD}" \
        --first-name "${DJANGO_SUPERUSER_FIRST_NAME:-Admin}" \
        --last-name "${DJANGO_SUPERUSER_LAST_NAME:-User}" \
        --force
fi

if [ "${PLATFORM_ADMIN_EMAIL:-}" != "" ] && [ "${PLATFORM_ADMIN_PASSWORD:-}" != "" ] && [ "${PLATFORM_ADMIN_USERNAME:-}" != "" ]; then
    python manage.py create_platform_admin "${PLATFORM_ADMIN_EMAIL}" \
        --create \
        --password "${PLATFORM_ADMIN_PASSWORD}" \
        --username "${PLATFORM_ADMIN_USERNAME}" \
        ${PLATFORM_ADMIN_STAFF:+--staff}
fi

python manage.py create_user_organizations

exec "$@"
