#!/bin/bash
# Docker management script for Email Campaign Management Platform

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
COMPOSE_DIR="$SCRIPT_DIR/../compose"

cd "$PROJECT_ROOT"

# Default environment
ENV=${ENV:-local}
COMPOSE_FILE="$COMPOSE_DIR/docker-compose.$ENV.yml"

# Check if compose file exists
if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "❌ Docker Compose file not found: $COMPOSE_FILE"
    echo "Available environments: local, dev, prod"
    exit 1
fi

# Load environment file
ENV_FILE=".env.$ENV"
if [[ -f "$ENV_FILE" ]]; then
    set -a
    source "$ENV_FILE"
    set +a
    echo "📋 Loaded environment from $ENV_FILE"
else
    echo "⚠️ Environment file $ENV_FILE not found, using defaults"
fi

case "$1" in
    "up")
        echo "🚀 Starting services for $ENV environment..."
        docker compose -f "$COMPOSE_FILE" up
        echo "✅ Services started!"
        echo "🌐 Web application: http://localhost:28000"
        ;;
    "detach")
        echo "🚀 Starting services for $ENV environment..."
        docker compose -f "$COMPOSE_FILE" up -d
        echo "✅ Services started!"
        echo "🌐 Web application: http://localhost:28000"
        ;;
    "down")
        echo "🛑 Stopping services for $ENV environment..."
        docker compose -f "$COMPOSE_FILE" down
        echo "✅ Services stopped!"
        ;;
    "build")
        echo "🔨 Building images for $ENV environment..."
        docker compose -f "$COMPOSE_FILE" build --no-cache
        ;;
    "logs")
        service=${2:-web}
        echo "📋 Showing logs for $service in $ENV environment..."
        docker compose -f "$COMPOSE_FILE" logs -f "$service"
        ;;
    "shell")
        echo "🐚 Starting shell in web container..."
        docker compose -f "$COMPOSE_FILE" exec web bash
        ;;
    "manage")
        shift
        echo "🔧 Running Django management command: $@"
        docker compose -f "$COMPOSE_FILE" exec web python manage.py "$@"
        ;;
    "superuser")
        echo "👤 Creating superuser..."
        docker compose -f "$COMPOSE_FILE" exec web python manage.py create_superuser
        ;;
    "setup")
        echo "🚀 Running development setup..."
        docker compose -f "$COMPOSE_FILE" exec web python manage.py setup_dev
        ;;
    "restart")
        echo "🔄 Restarting services for $ENV environment..."
        docker compose -f "$COMPOSE_FILE" restart
        ;;
    "ps")
        echo "📊 Service status for $ENV environment:"
        docker compose -f "$COMPOSE_FILE" ps
        ;;
    *)
        echo "🐳 Docker Management Script"
        echo ""
        echo "Usage: ENV=[local|dev|prod] $0 [command]"
        echo ""
        echo "Available commands:"
        echo "  up              - Start all services"
        echo "  down            - Stop all services"
        echo "  build           - Build images"
        echo "  logs [service]  - Show logs (default: web)"
        echo "  shell           - Start bash shell in web container"
        echo "  manage [cmd]    - Run Django management command"
        echo "  superuser       - Create superuser with default credentials"
        echo "  setup           - Run complete development setup"
        echo "  restart         - Restart all services"
        echo "  ps              - Show service status"
        echo ""
        echo "Examples:"
        echo "  $0 up                           # Start local environment"
        echo "  ENV=dev $0 up                  # Start dev environment"
        echo "  $0 manage migrate               # Run migrations"
        echo "  $0 superuser                    # Create superuser (admin/admin123)"
        echo "  $0 setup                        # Complete dev setup"
        echo "  $0 logs web                     # Show web logs"
        ;;
esac