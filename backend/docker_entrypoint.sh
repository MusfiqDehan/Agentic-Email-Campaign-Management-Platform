if [ -f .env ]; then
   source .env
fi

python manage.py makemigrations --noinput
python manage.py migrate
python manage.py collectstatic --noinput

# Create superuser using the correct command from authentication app
python manage.py create_superuser \
    --username admin \
    --email superadmin@example.com \
    --password MySecurePass123! \
    --first-name Admin \
    --last-name User \
    --force

# Create platform admin (if needed separately)
python manage.py create_platform_admin admin@example.com \
    --create \
    --password MySecurePass123! \
    --username platformadmin \
    --staff

# Ensure all users have organizations
python manage.py create_user_organizations

$@