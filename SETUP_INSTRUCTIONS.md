# Email Campaign Management Platform - Setup Instructions

## Overview
This is a full-stack email campaign management platform with:
- **Backend**: Django 4.2 + Django REST Framework
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS

## Prerequisites
- Python 3.8 or higher
- Node.js 18 or higher
- npm (comes with Node.js)

## Quick Start Guide

### Step 1: Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate

   # On Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (optional, for admin panel):**
   ```bash
   python manage.py createsuperuser
   ```
   Follow the prompts to set username, email, and password.

6. **Start the Django development server:**
   ```bash
   python manage.py runserver
   ```
   
   The backend API will be available at: **http://localhost:8000**

### Step 2: Frontend Setup

1. **Open a new terminal and navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Create environment file:**
   ```bash
   cp .env.example .env.local
   ```
   
   The `.env.local` file should contain:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Start the Next.js development server:**
   ```bash
   npm run dev
   ```
   
   The frontend will be available at: **http://localhost:3000**

### Step 3: Access the Application

1. **Landing Page**: http://localhost:3000
2. **Dashboard**: http://localhost:3000/dashboard
3. **Django Admin Panel**: http://localhost:8000/admin (use superuser credentials)
4. **API Documentation**: http://localhost:8000/api/

## Application Structure

### Backend (Django)
```
backend/
├── apps/
│   ├── campaigns/      # Campaign management
│   ├── contacts/       # Contact management
│   └── templates/      # Email template management
├── project_config/     # Django settings
└── manage.py          # Django management script
```

### Frontend (Next.js)
```
frontend/
├── app/
│   ├── campaigns/     # Campaign pages
│   ├── contacts/      # Contact pages
│   ├── dashboard/     # Dashboard page
│   └── templates/     # Template pages
├── components/        # Reusable components
├── lib/              # API client
└── types/            # TypeScript types
```

## Features

### 1. Campaign Management
- Create and manage email campaigns
- Add contacts to campaigns
- Send campaigns (simulated)
- Track campaign statistics

### 2. Contact Management
- Add and manage contacts
- Organize contacts into lists
- Store contact information (email, name, company, phone)

### 3. Template Management
- Create custom email templates
- HTML and plain text support
- Variable substitution support
- Preview templates before use

### 4. Dashboard
- View statistics at a glance
- Quick action buttons
- Real-time data updates

## API Endpoints

### Campaigns
- `GET /api/campaigns/` - List all campaigns
- `POST /api/campaigns/` - Create campaign
- `GET /api/campaigns/{id}/` - Get campaign details
- `PUT/PATCH /api/campaigns/{id}/` - Update campaign
- `DELETE /api/campaigns/{id}/` - Delete campaign
- `POST /api/campaigns/{id}/add_contacts/` - Add contacts
- `POST /api/campaigns/{id}/send/` - Send campaign
- `GET /api/campaigns/{id}/stats/` - Get statistics

### Contacts
- `GET /api/contacts/` - List all contacts
- `POST /api/contacts/` - Create contact
- `GET /api/contacts/{id}/` - Get contact details
- `PUT/PATCH /api/contacts/{id}/` - Update contact
- `DELETE /api/contacts/{id}/` - Delete contact

### Contact Lists
- `GET /api/contacts/lists/` - List all contact lists
- `POST /api/contacts/lists/` - Create list
- `GET /api/contacts/lists/{id}/` - Get list details
- `GET /api/contacts/lists/{id}/contacts/` - Get contacts in list

### Templates
- `GET /api/templates/` - List all templates
- `POST /api/templates/` - Create template
- `GET /api/templates/{id}/` - Get template details
- `PUT/PATCH /api/templates/{id}/` - Update template
- `DELETE /api/templates/{id}/` - Delete template

## Building for Production

### Backend
```bash
cd backend
pip install -r requirements.txt
python manage.py collectstatic
python manage.py migrate

# Use a production WSGI server like Gunicorn
pip install gunicorn
gunicorn project_config.wsgi:application
```

### Frontend
```bash
cd frontend
npm run build
npm start
```

## Troubleshooting

### Backend Issues

**Problem**: `ModuleNotFoundError: No module named 'django'`
- **Solution**: Make sure you've activated the virtual environment and installed dependencies

**Problem**: Database errors
- **Solution**: Run `python manage.py migrate` to ensure all migrations are applied

### Frontend Issues

**Problem**: `Error: Cannot find module 'axios'`
- **Solution**: Run `npm install` in the frontend directory

**Problem**: API connection errors
- **Solution**: Ensure the backend is running on port 8000 and check the `.env.local` file

**Problem**: CORS errors
- **Solution**: The backend is configured to allow requests from localhost:3000. If using a different port, update `CORS_ALLOWED_ORIGINS` in `backend/project_config/settings.py`

## Development Tips

1. **Hot Reload**: Both servers support hot reload. Changes will be reflected automatically.
2. **API Testing**: Use the Django REST Framework browsable API at http://localhost:8000/api/
3. **Database**: SQLite is used by default. The database file is `backend/db.sqlite3`
4. **Logging**: Check the terminal for both backend and frontend logs

## Technology Stack

### Backend
- Django 4.2.7
- Django REST Framework 3.14.0
- django-cors-headers 4.3.1
- SQLite (development)

### Frontend
- Next.js 14
- React 19
- TypeScript 5
- Tailwind CSS 4
- Axios
- Lucide React (icons)

## Next Steps

1. Add user authentication
2. Integrate with real email service (SendGrid, Mailgun, etc.)
3. Add email template editor
4. Implement scheduled sending
5. Add advanced analytics
6. Support for email attachments
7. A/B testing features

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the API documentation
3. Check Django and Next.js official documentation

## License

MIT License - See LICENSE file for details
