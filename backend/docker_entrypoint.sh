if [ -f .env ]; then
   source .env
fi

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Bootstrapping admin user and organization..."
python manage.py bootstrap_deployment \
    --username "${DJANGO_SUPERUSER_USERNAME:-admin}" \
    --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" \
    --password "${DJANGO_SUPERUSER_PASSWORD:-changeme}" \
    --first-name "${DJANGO_SUPERUSER_FIRST_NAME:-Admin}" \
    --last-name "${DJANGO_SUPERUSER_LAST_NAME:-User}"

echo "==> Starting application..."
exec "$@"