if [ -f .env ]; then
   source .env
fi

python manage.py makemigrations --noinput
python manage.py migrate
python manage.py collectstatic --noinput

$@