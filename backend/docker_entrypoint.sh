if [ -f .env ]; then
   source .env
fi

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser from environment variables (idempotent with --force)
echo "==> Creating superuser..."
python manage.py create_superuser \
    --username "${DJANGO_SUPERUSER_USERNAME:-admin}" \
    --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" \
    --password "${DJANGO_SUPERUSER_PASSWORD:-changeme}" \
    --first-name "${DJANGO_SUPERUSER_FIRST_NAME:-Admin}" \
    --last-name "${DJANGO_SUPERUSER_LAST_NAME:-User}" \
    --force

# Create platform admin
echo "==> Creating platform admin..."
python manage.py create_platform_admin "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" \
    --create \
    --password "${DJANGO_SUPERUSER_PASSWORD:-changeme}" \
    --username "${DJANGO_SUPERUSER_USERNAME:-platformadmin}" \
    --staff

# Ensure all users have organizations
python manage.py create_user_organizations

echo "==> Starting application..."
exec "$@"