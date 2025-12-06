if [ -f .env ]; then
   source .env
fi

python manage.py makemigrations --noinput
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py create_superuser
python manage.py create_platform_admin admin@example.com --create --password MySecurePass123! --username customadmin

$@