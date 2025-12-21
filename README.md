# Email Campaign Management Platform

A modern, full-stack email campaign management platform built with Django REST Framework (backend) and Next.js 14 with TypeScript (frontend). This platform allows you to manage email campaigns, contacts, and email templates with an intuitive and responsive user interface.

## 🚀 Features

- **Campaign Management**: Create, schedule, and send email campaigns
- **Contact Management**: Organize contacts and manage contact lists
- **Email Templates**: Design custom email templates with variable support
- **Analytics Dashboard**: Track campaign performance with real-time statistics
- **Modern UI**: Responsive design built with Tailwind CSS
- **RESTful API**: Well-structured API endpoints for all operations
- **Type Safety**: Full TypeScript support on the frontend

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8+ (for backend)
- Node.js 18+ and npm (for frontend)
- pip (Python package manager)

## 🛠️ Installation & Setup

### Backend Setup (Django)

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Run database migrations:
```bash
python manage.py migrate
```

5. Create a superuser (optional, for admin access):
```bash
python manage.py createsuperuser
```

6. Start the Django development server:
```bash
python manage.py runserver
```

The backend API will be available at `http://localhost:8000`

### Frontend Setup (Next.js)

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Copy the environment example file:
```bash
cp .env.example .env.local
```

4. Start the development server:
```bash
npm run dev
```

The frontend application will be available at `http://localhost:3000`

## 🎯 Usage

### Accessing the Application

1. **Landing Page**: Visit `http://localhost:3000` to see the modern landing page
2. **Dashboard**: Click "Get Started" or navigate to `http://localhost:3000/dashboard`
3. **Admin Panel**: Access Django admin at `http://localhost:8000/admin` (requires superuser)

### Managing Campaigns

1. Navigate to the **Campaigns** page
2. Click "New Campaign" to create a campaign
3. Fill in campaign details (name, subject, from email, from name)
4. Add contacts to your campaign
5. Send the campaign when ready

### Managing Contacts

1. Navigate to the **Contacts** page
2. Click "New Contact" to add contacts
3. Fill in contact information (name, email, company, phone)
4. Organize contacts into lists for targeted campaigns

### Managing Templates

1. Navigate to the **Templates** page
2. Click "New Template" to create an email template
3. Design your template using HTML
4. Use variables like `{{name}}` for personalization
5. Preview templates before using them in campaigns

## 📁 Project Structure

```
Email-Campaign-Management-Platform/
├── backend/                    # Django backend
│   ├── apps/
│   │   ├── campaigns/         # Campaign management app
│   │   ├── contacts/          # Contact management app
│   │   └── templates/         # Template management app
│   ├── project_config/        # Django project settings
│   ├── manage.py              # Django management script
│   └── requirements.txt       # Python dependencies
│
└── frontend/                  # Next.js frontend
    ├── app/                   # Next.js 14 App Router
    │   ├── campaigns/        # Campaign pages
    │   ├── contacts/         # Contact pages
    │   ├── dashboard/        # Dashboard page
    │   └── templates/        # Template pages
    ├── components/           # Reusable React components
    ├── lib/                  # API client and utilities
    ├── types/                # TypeScript type definitions
    └── package.json          # Node.js dependencies
```

## 🔌 API Endpoints

### Campaigns
- `GET /api/campaigns/` - List all campaigns
- `POST /api/campaigns/` - Create a new campaign
- `GET /api/campaigns/{id}/` - Get campaign details
- `PUT /api/campaigns/{id}/` - Update campaign
- `DELETE /api/campaigns/{id}/` - Delete campaign
- `POST /api/campaigns/{id}/add_contacts/` - Add contacts to campaign
- `POST /api/campaigns/{id}/send/` - Send campaign
- `GET /api/campaigns/{id}/stats/` - Get campaign statistics

### Contacts
- `GET /api/contacts/` - List all contacts
- `POST /api/contacts/` - Create a new contact
- `GET /api/contacts/{id}/` - Get contact details
- `PUT /api/contacts/{id}/` - Update contact
- `DELETE /api/contacts/{id}/` - Delete contact

### Contact Lists
- `GET /api/contacts/lists/` - List all contact lists
- `POST /api/contacts/lists/` - Create a new list
- `GET /api/contacts/lists/{id}/` - Get list details
- `GET /api/contacts/lists/{id}/contacts/` - Get contacts in list

### Templates
- `GET /api/templates/` - List all templates
- `POST /api/templates/` - Create a new template
- `GET /api/templates/{id}/` - Get template details
- `PUT /api/templates/{id}/` - Update template
- `DELETE /api/templates/{id}/` - Delete template

## 🧪 Development

### Running in Development Mode

**Backend:**
```bash
cd backend
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### Building for Production

**Frontend:**
```bash
cd frontend
npm run build
npm start
```

## 🎨 Technologies Used

### Backend
- Django 4.2
- Django REST Framework 3.14
- django-cors-headers (for CORS support)
- SQLite (default database)

### Frontend
- Next.js 14 (App Router)
- React 19
- TypeScript 5
- Tailwind CSS 4
- Axios (API client)
- Lucide React (icons)

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🐛 Known Issues

- Email sending is simulated (not actually sending emails). Integrate with an email service provider (e.g., SendGrid, Mailgun) for production use.
- Authentication is not implemented. Add user authentication for production deployment.

## 🔮 Future Enhancements

- User authentication and authorization
- Real email sending integration
- Advanced analytics and reporting
- Email template editor with drag-and-drop
- A/B testing for campaigns
- Scheduled campaign sending
- Email tracking (opens, clicks)
- Contact import/export (CSV)
- Multi-language support

