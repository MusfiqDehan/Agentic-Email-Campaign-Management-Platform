#!/bin/bash
# Helper script to run common Django management commands

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./scripts/setup-dev.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Set Django environment
export DJANGO_ENV=${DJANGO_ENV:-development}

case "$1" in
    "migrate")
        echo "🔄 Running database migrations..."
        python manage.py migrate
        ;;
    "makemigrations")
        echo "📝 Creating new migrations..."
        python manage.py makemigrations
        ;;
    "superuser")
        echo "👤 Creating superuser..."
        python manage.py createsuperuser
        ;;
    "runserver")
        echo "🌐 Starting development server..."
        python manage.py runserver
        ;;
    "shell")
        echo "🐚 Starting Django shell..."
        python manage.py shell
        ;;
    "test")
        echo "🧪 Running tests..."
        python manage.py test
        ;;
    "collectstatic")
        echo "📦 Collecting static files..."
        python manage.py collectstatic --noinput
        ;;
    *)
        echo "Django Management Helper"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Available commands:"
        echo "  migrate         - Apply database migrations"
        echo "  makemigrations  - Create new migrations"
        echo "  superuser       - Create a superuser account"
        echo "  runserver       - Start development server"
        echo "  shell           - Start Django shell"
        echo "  test            - Run tests"
        echo "  collectstatic   - Collect static files"
        echo ""
        echo "Example: $0 runserver"
        ;;
esac