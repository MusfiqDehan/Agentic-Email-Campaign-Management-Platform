#!/bin/bash
# Development setup script for Email Campaign Management Platform

set -e

echo "🚀 Setting up Email Campaign Management Platform for development..."

# Check if Python 3.8+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📋 Installing development requirements..."
pip install -r requirements/dev.txt

# Set up environment file
if [ ! -f ".env.local" ]; then
    echo "⚙️ Creating local environment file..."
    cp .env.example .env.local
    echo "📝 Please edit .env.local with your local database credentials"
fi

# Set DJANGO_ENV
export DJANGO_ENV=development

echo "✅ Development setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env.local with your database credentials"
echo "2. Run 'python manage.py migrate' to set up the database"
echo "3. Run 'python manage.py createsuperuser' to create an admin user"
echo "4. Run 'python manage.py runserver' to start the development server"