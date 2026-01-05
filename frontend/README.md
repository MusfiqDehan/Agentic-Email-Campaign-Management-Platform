# 📧 Email Campaign Management Platform

A comprehensive platform for managing email marketing campaigns, featuring a Django REST Framework backend and a Next.js frontend.

## 🏗️ Architecture

- **Backend**: Django REST Framework, Celery, Redis, PostgreSQL
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Shadcn/ui

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed on your machine.

### Running with Docker (Recommended)

1. **Create Environment File**
   Create a `.env` file in the root directory (or use the defaults in `docker-compose.yml`):

   ```bash
   # .env
   POSTGRES_DB=ecmp_db
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   REDIS_PASSWORD=redis_password
   SECRET_KEY=your_secret_key
   DEBUG=True
   ```

2. **Build and Start Services**

   ```bash
   docker-compose up --build
   ```

   This will start:
   - **Frontend**: http://localhost:3001
   - **Backend API**: http://localhost:8001
   - **PostgreSQL**: Port 5441
   - **Redis**: Port 6391
   - **Celery Worker & Beat**: Background tasks

3. **Access the Application**
   - Open http://localhost:3001 in your browser.
   - Sign up for a new organization account.
   - Configure your email provider (SMTP or SES) in Settings.
   - Create templates and contact lists.
   - Launch your campaign!

### Manual Setup (Development)

#### Backend

1. Navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. Start the server:
   ```bash
   python manage.py runserver 8001
   ```
   *Note: You need a running Redis and PostgreSQL instance.*

#### Frontend

1. Navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install --legacy-peer-deps
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
   The app will be available at http://localhost:3001.

## 🌟 Features

- **Organization Management**: Multi-tenant support.
- **Email Providers**: Support for SMTP and AWS SES.
- **Contact Management**: Bulk import (CSV/Excel), list management, and segmentation.
- **Campaign Wizard**: Step-by-step guide to launch campaigns.
- **Rich Text Editor**: Create beautiful email templates.
- **Analytics**: Track opens, clicks, and bounces (Backend support ready).

## 📁 Project Structure

```
├── backend/          # Django REST API
├── frontend/         # Next.js Application
├── docker-compose.yml # Docker orchestration
└── README.md         # This file
```
