# 📧 Email Campaign Management Platform

A comprehensive monorepo containing both backend (Django REST API) and frontend (React TypeScript) applications for managing email marketing campaigns. This platform helps you easily add your own email credentials, manage contact lists, create custom email variables, and design custom templates to launch effective email campaigns.

## 🏗️ Architecture

This project follows a **monorepo structure** with:

- **Backend**: Django REST API with PostgreSQL and Redis
- **Frontend**: React TypeScript application  
- **Shared**: Common types and utilities
- **Deployments**: Docker configurations and deployment scripts

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/MusfiqDehan/Email-Campaign-Management-Platform.git
cd Email-Campaign-Management-Platform

# Start with Docker (Recommended)
cp .env.example .env.local
./_deployments/docker/scripts/docker-manage.sh up

# Access applications
# Backend API: http://localhost:28000
# Frontend: http://localhost:3000 (coming soon)
```

## 📁 Repository Structure

```
├── _deployments/      # Docker and deployment configs
├── _docs/            # Documentation
├── _shared/          # Shared types and utilities
├── backend/          # Django REST API
└── frontend/         # React TypeScript App  
```

For detailed setup instructions, see [Monorepo Documentation](./_docs/monorepo/README.md).

## 🔧 Development

- **Backend Development**: See `backend/` directory
- **Frontend Development**: See `frontend/` directory
- **Docker Development**: Use `./_deployments/docker/scripts/docker-manage.sh`

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

# Email Campaign Management Platform - Monorepo

This project follows a monorepo structure with frontend and backend applications in the same repository.

## 📁 Repository Structure

```
Email-Campaign-Management-Platform/
├── .git/                          # Git repository
├── .github/                       # GitHub workflows and templates
├── README.md                      # This file
├── LICENSE                        # Project license
├── .env.example                   # Root-level environment template
├── .env.local                     # Root-level local environment
├── _docs/                         # Project documentation
│   └── monorepo/
├── _deployments/                  # Infrastructure & deployment configs
│   ├── docker/
│   │   ├── build/Dockerfile       # Backend Docker image
│   │   └── compose/              # Docker compose configurations
│   └── scripts/                  # Deployment scripts
├── _shared/                       # Shared code and types
│   ├── types/
│   ├── constants/
│   └── schemas/
├── backend/                       # Django REST API
│   ├── manage.py                 # Django management script
│   ├── project_config/           # Django project settings
│   ├── authentication/           # Authentication app
│   ├── utils/                    # Common utilities
│   ├── requirements/             # Python dependencies
│   ├── static/                   # Static files
│   ├── media/                    # Media uploads
│   └── .env.local               # Backend-specific environment
└── frontend/                     # React TypeScript application
    ├── src/                     # Source code
    ├── public/                  # Public assets
    ├── package.json             # Node.js dependencies
    └── .env.local               # Frontend-specific environment
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### 1. Clone and Setup
```bash
git clone https://github.com/MusfiqDehan/Email-Campaign-Management-Platform.git
cd Email-Campaign-Management-Platform

# Copy environment templates
cp .env.example .env.local
cp backend/.env.example backend/.env.local
cp frontend/.env.example frontend/.env.local  # (when created)
```

### 2. Start Development Environment
```bash
# Start all services with Docker
./_deployments/docker/scripts/docker-manage.sh up

# Or start services individually:
# Backend only
cd backend && python manage.py runserver

# Frontend only
cd frontend && npm start
```

### 3. Access Applications
- **Backend API**: http://localhost:28000
- **Frontend App**: http://localhost:3000 (when ready)
- **Database**: localhost:25432
- **Redis**: localhost:26379

## 🔧 Development Workflow

### Backend Development
```bash
cd backend/

# Install dependencies
pip install -r requirements/dev.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Frontend Development
```bash
cd frontend/

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

### Docker Development
```bash
# Start all services
./_deployments/docker/scripts/docker-manage.sh up

# View logs
./_deployments/docker/scripts/docker-manage.sh logs web

# Run Django commands
./_deployments/docker/scripts/docker-manage.sh manage migrate
./_deployments/docker/scripts/docker-manage.sh manage createsuperuser

# Stop services
./_deployments/docker/scripts/docker-manage.sh down
```

## 📝 Environment Configuration

### Root Level (.env.local)
Contains shared configuration between frontend and backend:
- Database connection details
- Redis connection details
- Application URLs
- Environment type

### Backend (backend/.env.local)
Contains Django-specific configuration:
- Django secret key
- Debug settings
- Email configuration
- Security settings

### Frontend (frontend/.env.local)
Contains React-specific configuration:
- API endpoints
- Feature flags
- External service keys

## 🏗️ Architecture

### Backend (Django REST API)
- **Authentication**: Custom user model with JWT authentication
- **Apps**: Modular Django apps for different features
- **Database**: PostgreSQL for data storage
- **Cache**: Redis for caching and sessions
- **API**: RESTful API with Django REST Framework

### Frontend (React TypeScript)
- **Framework**: React 18 with TypeScript
- **State Management**: React Query for API state
- **Styling**: TailwindCSS (to be added)
- **Build Tool**: Create React App (will migrate to Vite)

### Shared
- **Types**: Shared TypeScript definitions
- **Constants**: Shared application constants
- **Schemas**: API schema definitions

## 🚢 Deployment

### Development
```bash
# Docker Compose local environment
./_deployments/docker/scripts/docker-manage.sh up
```

### Production
```bash
# Production Docker setup (to be configured)
ENV=prod ./_deployments/docker/scripts/docker-manage.sh up
```

## 📚 Documentation

- [Backend API Documentation](./docs/API.md) - Coming soon
- [Frontend Development Guide](./docs/FRONTEND.md) - Coming soon
- [Deployment Guide](./docs/DEPLOYMENT.md) - Coming soon
- [Architecture Overview](./docs/ARCHITECTURE.md) - Coming soon

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes in the appropriate directory (backend/, frontend/, or shared/)
4. Test your changes locally
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
