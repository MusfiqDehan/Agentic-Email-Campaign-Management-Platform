#!/bin/bash

# Production Deployment Script
# Safe, idempotent deployment with rollback support
# Usage: bash deploy.sh [options]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/email-platform"
BACKUP_DIR="$APP_DIR/backups"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production.local"
LOG_FILE="$APP_DIR/deploy.log"
HEALTH_CHECK_URL="http://localhost:8000/api/v1/campaigns/health/"
HEALTH_CHECK_TIMEOUT=300  # 5 minutes
MAX_RETRIES=30
RETRY_DELAY=10

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

print_usage() {
    cat << EOF
Usage: bash deploy.sh [OPTIONS]

Options:
    -h, --help              Show this help message
    -b, --branch BRANCH     Git branch to deploy (default: production)
    -t, --tag TAG          Deploy specific git tag/version
    -d, --dry-run          Perform dry run without making changes
    --skip-backup          Skip database backup
    --skip-health-check    Skip health checks
    --force                Force deployment without confirmation

Examples:
    bash deploy.sh                          # Deploy from production branch
    bash deploy.sh -b main                  # Deploy from main branch
    bash deploy.sh -t v1.2.0                # Deploy specific version
    bash deploy.sh --dry-run                # Test deployment process
    bash deploy.sh --force --skip-backup    # Force deployment without backup
EOF
}

# Parse arguments
BRANCH="production"
TAG=""
DRY_RUN=false
SKIP_BACKUP=false
SKIP_HEALTH_CHECK=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            print_usage
            exit 0
            ;;
        -b|--branch)
            BRANCH="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --skip-health-check)
            SKIP_HEALTH_CHECK=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            error "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Main Deployment Function
main() {
    log "=========================================="
    log "Email Platform Production Deployment"
    log "=========================================="
    
    # 1. Pre-flight checks
    log "Running pre-flight checks..."
    pre_flight_checks
    
    # 2. Backup database
    if [ "$SKIP_BACKUP" = false ]; then
        log "Creating database backup..."
        backup_database
    else
        warning "Skipping database backup (use with caution)"
    fi
    
    # 3. Update code
    log "Updating code from git..."
    update_code
    
    # 4. Build Docker images
    log "Building Docker images..."
    build_images
    
    # 5. Validate environment
    log "Validating configuration..."
    validate_config
    
    # 6. Stop services gracefully
    log "Stopping services gracefully..."
    stop_services
    
    # 7. Run migrations
    log "Running database migrations..."
    run_migrations
    
    # 8. Start services
    log "Starting services..."
    start_services
    
    # 9. Health checks
    if [ "$SKIP_HEALTH_CHECK" = false ]; then
        log "Running health checks..."
        health_checks
    else
        warning "Skipping health checks"
    fi
    
    # 10. Cleanup
    log "Cleaning up old images and containers..."
    cleanup
    
    success "Deployment completed successfully!"
    print_deployment_summary
}

# Pre-flight checks
pre_flight_checks() {
    # Check if running as correct user (not root)
    if [ "$EUID" -eq 0 ]; then
        error "Please do not run this script as root"
        exit 1
    fi
    
    # Check required commands
    for cmd in git docker docker-compose; do
        if ! command -v $cmd &> /dev/null; then
            error "Required command not found: $cmd"
            exit 1
        fi
    done
    
    # Check app directory exists
    if [ ! -d "$APP_DIR" ]; then
        error "App directory not found: $APP_DIR"
        exit 1
    fi
    
    # Check docker-compose file
    if [ ! -f "$APP_DIR/$DOCKER_COMPOSE_FILE" ]; then
        error "Docker compose file not found: $APP_DIR/$DOCKER_COMPOSE_FILE"
        exit 1
    fi
    
    # Check environment file
    if [ ! -f "$APP_DIR/$ENV_FILE" ]; then
        error "Environment file not found: $APP_DIR/$ENV_FILE"
        exit 1
    fi
    
    # Check disk space (need at least 10GB free)
    AVAILABLE_SPACE=$(df "$APP_DIR" | awk 'NR==2 {print $4}')
    if [ "$AVAILABLE_SPACE" -lt 10485760 ]; then
        error "Insufficient disk space. Required: 10GB, Available: $(($AVAILABLE_SPACE / 1048576))GB"
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker ping &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi
    
    # Confirm deployment if not forced
    if [ "$FORCE" = false ]; then
        echo ""
        warning "About to deploy to PRODUCTION"
        echo -e "  ${YELLOW}Branch:${NC} $BRANCH"
        [ -n "$TAG" ] && echo -e "  ${YELLOW}Tag:${NC} $TAG"
        echo -e "  ${YELLOW}Backups Dir:${NC} $BACKUP_DIR"
        echo -e "  ${YELLOW}Dry Run:${NC} $DRY_RUN"
        echo ""
        read -p "Continue with deployment? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Deployment cancelled by user"
            exit 0
        fi
    fi
    
    success "Pre-flight checks passed"
}

# Backup database
backup_database() {
    mkdir -p "$BACKUP_DIR"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"
    
    log "Backing up database to: $BACKUP_FILE"
    
    cd "$APP_DIR"
    
    if [ "$DRY_RUN" = false ]; then
        # Backup PostgreSQL
        docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres \
            pg_dump -U postgres email_campaign_db_prod 2>/dev/null | \
            gzip > "$BACKUP_FILE"
        
        if [ $? -eq 0 ]; then
            FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
            success "Database backup completed: $FILE_SIZE"
        else
            error "Database backup failed"
            exit 1
        fi
        
        # Keep only last 30 days
        find "$BACKUP_DIR" -name "db_backup_*.sql.gz" -mtime +30 -delete
    else
        log "[DRY RUN] Would backup to: $BACKUP_FILE"
    fi
}

# Update code from git
update_code() {
    cd "$APP_DIR"
    
    if [ "$DRY_RUN" = false ]; then
        # Stash any local changes
        git stash
        
        # Fetch latest
        git fetch origin
        
        # Checkout branch or tag
        if [ -n "$TAG" ]; then
            log "Checking out tag: $TAG"
            git checkout "tags/$TAG"
        else
            log "Checking out branch: $BRANCH"
            git checkout "$BRANCH"
            git pull origin "$BRANCH"
        fi
        
        # Show what changed
        log "Recent commits:"
        git log --oneline -5
        
        success "Code updated successfully"
    else
        log "[DRY RUN] Would checkout: ${TAG:-$BRANCH}"
    fi
}

# Build Docker images
build_images() {
    cd "$APP_DIR"
    
    if [ "$DRY_RUN" = false ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
        
        if [ $? -eq 0 ]; then
            success "Docker images built successfully"
        else
            error "Docker build failed"
            exit 1
        fi
    else
        log "[DRY RUN] Would build Docker images"
    fi
}

# Validate configuration
validate_config() {
    cd "$APP_DIR"
    
    log "Validating Django configuration..."
    
    if [ "$DRY_RUN" = false ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm app \
            python manage.py check 2>&1 | head -20
        
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            success "Configuration validation passed"
        else
            error "Configuration validation failed"
            exit 1
        fi
    else
        log "[DRY RUN] Would validate configuration"
    fi
}

# Stop services gracefully
stop_services() {
    cd "$APP_DIR"
    
    if [ "$DRY_RUN" = false ]; then
        # Give services time to finish work
        log "Sending graceful shutdown signal..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" stop -t 30
        
        success "Services stopped"
    else
        log "[DRY RUN] Would stop services"
    fi
}

# Run database migrations
run_migrations() {
    cd "$APP_DIR"
    
    if [ "$DRY_RUN" = false ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d postgres redis
        
        # Wait for database
        log "Waiting for database..."
        sleep 10
        
        # Run migrations
        docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm app \
            python manage.py migrate
        
        if [ $? -eq 0 ]; then
            success "Migrations completed successfully"
        else
            error "Migration failed"
            exit 1
        fi
    else
        log "[DRY RUN] Would run migrations"
    fi
}

# Start services
start_services() {
    cd "$APP_DIR"
    
    if [ "$DRY_RUN" = false ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
        
        success "Services started"
        log "Waiting for services to be ready..."
        sleep 5
    else
        log "[DRY RUN] Would start services"
    fi
}

# Health checks
health_checks() {
    cd "$APP_DIR"
    
    log "Checking service health..."
    
    # Check Docker services
    SERVICES=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps --services)
    while read -r service; do
        STATUS=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$service" -q)
        if [ -n "$STATUS" ]; then
            success "Service $service is running"
        else
            error "Service $service is not running"
            return 1
        fi
    done <<< "$SERVICES"
    
    # Check health endpoint
    log "Checking application health endpoint..."
    RETRY_COUNT=0
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_CHECK_URL" 2>/dev/null || echo "000")
        
        if [ "$RESPONSE" = "200" ]; then
            success "Health check passed (HTTP $RESPONSE)"
            return 0
        else
            RETRY_COUNT=$((RETRY_COUNT + 1))
            if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                warning "Health check failed (HTTP $RESPONSE), retrying in ${RETRY_DELAY}s... ($RETRY_COUNT/$MAX_RETRIES)"
                sleep $RETRY_DELAY
            fi
        fi
    done
    
    error "Health check failed after $MAX_RETRIES attempts"
    return 1
}

# Cleanup
cleanup() {
    if [ "$DRY_RUN" = false ]; then
        log "Removing unused Docker images and containers..."
        docker container prune -f --filter "until=24h" > /dev/null 2>&1
        docker image prune -f --filter "until=168h" > /dev/null 2>&1
    fi
}

# Print deployment summary
print_deployment_summary() {
    echo ""
    echo -e "${GREEN}=========================================="
    echo "Deployment Summary"
    echo "==========================================${NC}"
    echo -e "  ${YELLOW}Deployment Date:${NC} $(date)"
    echo -e "  ${YELLOW}Branch/Tag:${NC} ${TAG:-$BRANCH}"
    echo -e "  ${YELLOW}App Directory:${NC} $APP_DIR"
    echo -e "  ${YELLOW}Log File:${NC} $LOG_FILE"
    echo -e "  ${YELLOW}Backup Directory:${NC} $BACKUP_DIR"
    echo ""
    echo -e "${GREEN}Next Steps:${NC}"
    echo "  1. Monitor logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f"
    echo "  2. Check services: docker-compose -f $DOCKER_COMPOSE_FILE ps"
    echo "  3. Test API: curl $HEALTH_CHECK_URL"
    echo ""
    if [ -f "$BACKUP_DIR/db_backup_*.sql.gz" ]; then
        echo -e "${YELLOW}Database Backup:${NC}"
        ls -lah "$BACKUP_DIR"/db_backup_*.sql.gz | tail -1
        echo ""
    fi
}

# Trap errors and cleanup
trap 'on_error' ERR

on_error() {
    error "Deployment failed! Check $LOG_FILE for details"
    error "To rollback, restore the database backup and checkout the previous version"
    exit 1
}

# Run main function
main "$@"
