#!/bin/bash

# Quick Start Script for Email Campaign Management Platform
# Usage: bash docker-quickstart.sh [dev|prod]

set -e

MODE=${1:-dev}
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Email Campaign Management Platform - Docker Quick Start      ║"
echo "║  Mode: ${MODE^}                                               ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# Check prerequisites
echo ""
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker."
    exit 1
fi

# Check for docker-compose (both as standalone and as docker compose)
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi

# Set docker compose command (prefer 'docker compose' over 'docker-compose')
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    DOCKER_COMPOSE_CMD="docker-compose"
fi

echo "✓ Docker $(docker --version | grep -oP '\d+\.\d+\.\d+')"
echo "✓ Docker Compose $($DOCKER_COMPOSE_CMD version | grep -oP '\d+\.\d+\.\d+')"

# Setup environment
echo ""
echo "🔧 Setting up environment..."

if [ ! -f "$BACKEND_DIR/.env.local" ]; then
    echo "   Creating .env.local from .env.example..."
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env.local"
    echo "   ✓ .env.local created (update with your values)"
else
    echo "   ✓ .env.local already exists"
fi

# Build and start services
echo ""
echo "🐳 Building and starting Docker services..."
echo ""

if [ "$MODE" = "prod" ]; then
    echo "🏭 Starting in PRODUCTION mode..."
    docker build --target production -t email-platform:latest "$BACKEND_DIR"
    $DOCKER_COMPOSE_CMD -f "$BACKEND_DIR/docker-compose.yml" up -d
else
    echo "🔨 Starting in DEVELOPMENT mode..."
    $DOCKER_COMPOSE_CMD -f "$BACKEND_DIR/docker-compose.yml" up --build
fi

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Check service health
echo ""
echo "🏥 Checking service health..."

SERVICES=("postgres" "redis" "app")
FAILED=0

for service in "${SERVICES[@]}"; do
    if $DOCKER_COMPOSE_CMD -f "$BACKEND_DIR/docker-compose.yml" ps "$service" | grep -q "Up"; then
        echo "   ✓ $service is running"
    else
        echo "   ✗ $service is NOT running"
        FAILED=$((FAILED + 1))
    fi
done

if [ $FAILED -gt 0 ]; then
    echo ""
    echo "⚠️  Some services failed to start. Check logs:"
    echo "   $DOCKER_COMPOSE_CMD logs"
    exit 1
fi

# Initial setup
echo ""
echo "🚀 Performing initial setup..."

if [ "$MODE" = "dev" ]; then
    echo ""
    echo "   Creating superuser..."
    $DOCKER_COMPOSE_CMD -f "$BACKEND_DIR/docker-compose.yml" exec -T app python manage.py createsuperuser --noinput \
        --username admin \
        --email admin@example.com 2>/dev/null || true
    
    echo "   Creating platform admin user..."
    $DOCKER_COMPOSE_CMD -f "$BACKEND_DIR/docker-compose.yml" exec -T app python manage.py create_platform_admin admin@example.com --create --password admin123 --staff 2>/dev/null || true
fi

# Print summary
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✓ Setup Complete!                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 Services running:"
echo "   • Django API:     http://localhost:8000"
echo "   • Admin Panel:    http://localhost:8000/admin"
echo "   • Health Check:   http://localhost:8000/api/v1/campaigns/health/"
echo ""
echo "📊 Services:"
echo "   • Database:       PostgreSQL on localhost:5432"
echo "   • Cache:          Redis on localhost:6379"
if [ "$MODE" = "dev" ]; then
    echo "   • Workers:        Celery worker running"
    echo "   • Scheduler:      Celery Beat running"
fi
echo ""
echo "🔐 Credentials:"
echo "   • Admin User:     admin@example.com / admin123"
echo "   • DB User:        postgres / postgres"
echo "   • DB Name:        email_campaign_db"
echo ""
echo "📚 Useful Commands:"
echo "   • View logs:      docker-compose logs -f"
echo "   • Shell:          docker-compose exec app python manage.py shell"
echo "   • Migrations:     docker-compose exec app python manage.py migrate"
echo "   • Tests:          docker-compose exec app pytest"
echo "   • Stop services:  docker-compose down"
echo ""
echo "📖 For more info, see: DOCKER_SETUP.md"
echo ""
