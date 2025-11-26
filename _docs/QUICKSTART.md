````markdown
# 🚀 Quick Start Guide

Get your Email Campaign Management Platform up and running in minutes!

## Prerequisites

- Docker & Docker Compose installed
- Git (optional, for cloning)

## Step 1: Choose Your Environment

We have three environment configurations:

- **local** - For day-to-day development
- **dev** - For development/staging server
- **prod** - For production deployment

## Step 2: Start the Local Environment

```bash
# Using the management script (recommended)
../docker-manage.sh local up --build

# Or using docker-compose directly
docker-compose -f ../docker-compose.local.yml up --build
```

This will:
- Build the Docker images
- Start PostgreSQL database
- Start Django development server
- Apply migrations automatically

## Step 3: Access the Application

Open your browser and navigate to:
```
http://localhost:8000
```

## Step 4: Create a Superuser

In a new terminal, run:

```bash
../docker-manage.sh local createsuperuser
```

Or:

```bash
docker-compose -f ../docker-compose.local.yml exec web python manage.py createsuperuser
```

## 🎯 Common Commands

### Using the Management Script

```bash
# Start environment
../docker-manage.sh local up --build

# View logs
../docker-manage.sh local logs web

# Run migrations
../docker-manage.sh local migrate

# Open Django shell
../docker-manage.sh local shell

# Open database shell
../docker-manage.sh local dbshell

# Run tests
../docker-manage.sh local test

# Stop environment
../docker-manage.sh local down
```

### Using Docker Compose Directly

```bash
# Start services
docker-compose -f ../docker-compose.local.yml up

# Start in background
docker-compose -f ../docker-compose.local.yml up -d

# View logs
docker-compose -f ../docker-compose.local.yml logs -f web

# Execute Django commands
docker-compose -f ../docker-compose.local.yml exec web python manage.py <command>

# Stop services
docker-compose -f ../docker-compose.local.yml down

# Stop and remove volumes (⚠️ deletes database)
docker-compose -f ../docker-compose.local.yml down -v
```

## 🔧 Configuration

### Environment Variables

Each environment has its own `.env` file:

- `../.env.local` - Already configured for local use
- `../.env.dev` - Update for dev server
- `../.env.prod` - Update for production

### Database Connection

The PostgreSQL database is accessible at:

- **Host**: localhost
- **Port**: 5432
- **Database**: email_campaign_db
- **Username**: postgres
- **Password**: postgres (local only, change for dev/prod!)

## 📝 Next Steps

1. ✅ Environment is running
2. ✅ Create your superuser
3. 📖 Check out `DOCKER_SETUP.md` for detailed documentation
4. 🎨 Access admin panel at http://localhost:8000/admin
5. 🚀 Start building your email campaigns!

## 🆘 Troubleshooting

### Port 8000 already in use?

Change the port mapping in `../docker-compose.local.yml`:
```yaml
ports:
  - "8001:8000"  # Access via http://localhost:8001
```

### Database connection errors?

Wait for the database to be fully initialized:
```bash
docker-compose -f ../docker-compose.local.yml logs db
```

Look for: `database system is ready to accept connections`

### Need to reset everything?

```bash
# Stop and remove everything including volumes
../docker-manage.sh local down -v

# Rebuild from scratch
../docker-manage.sh local up --build
```

## 📚 More Information

- See `DOCKER_SETUP.md` for comprehensive documentation
- Run `../docker-manage.sh` without arguments to see all available commands

---

**Happy Coding! 🎉**

````