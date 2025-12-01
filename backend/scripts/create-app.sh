#!/bin/bash

# Script to create a new Django app inside backend/apps with predefined structure
# Usage: ./scripts/create-app.sh <app_name>

set -e

if [ $# -eq 0 ]; then
    echo "Error: Please provide an app name"
    echo "Usage: ./scripts/create-app.sh <app_name>"
    exit 1
fi

APP_NAME=$1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
APPS_DIR="$BACKEND_DIR/apps"
APP_DIR="$APPS_DIR/$APP_NAME"

echo "Creating Django app '$APP_NAME' in apps directory..."

# Check if app already exists
if [ -d "$APP_DIR" ]; then
    echo "Error: App '$APP_NAME' already exists in apps directory"
    exit 1
fi

# Create app directory structure
mkdir -p "$APP_DIR"/{migrations,management/commands,services,tests,models,api/v1}

# Create __init__.py files
find "$APP_DIR" -type d -exec touch {}/__init__.py \;

# Create apps.py
cat > "$APP_DIR/apps.py" << EOF
from django.apps import AppConfig


class ${APP_NAME^}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.$APP_NAME'
EOF

# Create models/__init__.py
cat > "$APP_DIR/models/__init__.py" << EOF
from django.db import models
from apps.utils.base_models import BaseModel

# Import your models here
# from .your_model import YourModel

__all__ = [
    # Add your model names here
    # 'YourModel',
]
EOF

# Create models/base.py
cat > "$APP_DIR/models/base.py" << EOF
from django.db import models
from apps.utils.base_models import BaseModel


class ${APP_NAME^}BaseModel(BaseModel):
    """
    Base model for $APP_NAME app with common fields.
    """
    
    class Meta:
        abstract = True
EOF

# Create views.py
cat > "$APP_DIR/views.py" << EOF
from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from apps.utils.view_mixins import BaseViewMixin

# Create your views here.
EOF

# Create admin.py
cat > "$APP_DIR/admin.py" << EOF
from django.contrib import admin

# Register your models here.
EOF

# Create tests/__init__.py
cat > "$APP_DIR/tests/__init__.py" << EOF
from django.test import TestCase
from rest_framework.test import APITestCase

# Import your test classes here
# from .test_models import YourModelTests
# from .test_views import YourViewTests
# from .test_api import YourAPITests

__all__ = [
    # Add your test class names here
    # 'YourModelTests',
    # 'YourViewTests', 
    # 'YourAPITests',
]
EOF

# Create tests/test_models.py
cat > "$APP_DIR/tests/test_models.py" << EOF
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class ${APP_NAME^}ModelTests(TestCase):
    """
    Test cases for $APP_NAME models.
    """
    
    def setUp(self):
        """Set up test data."""
        pass
    
    def test_model_creation(self):
        """Test model creation."""
        # Add your model tests here
        pass
EOF

# Create tests/test_views.py
cat > "$APP_DIR/tests/test_views.py" << EOF
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class ${APP_NAME^}ViewTests(TestCase):
    """
    Test cases for $APP_NAME views.
    """
    
    def setUp(self):
        """Set up test data."""
        pass
    
    def test_view_response(self):
        """Test view response."""
        # Add your view tests here
        pass


class ${APP_NAME^}APITests(APITestCase):
    """
    Test cases for $APP_NAME API views.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_api_endpoint(self):
        """Test API endpoint."""
        # Add your API tests here
        pass
EOF

# Create urls.py
cat > "$APP_DIR/urls.py" << EOF
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = '$APP_NAME'

router = DefaultRouter()
# Register your viewsets here
# router.register(r'items', YourViewSet)

urlpatterns = [
    path('api/v1/', include(router.urls)),
]
EOF

# Create permissions.py
cat > "$APP_DIR/permissions.py" << EOF
from rest_framework import permissions

# Create your custom permissions here.
EOF

# Create API files
cat > "$APP_DIR/api/v1/serializers.py" << EOF
from rest_framework import serializers

# Create your serializers here.
EOF

cat > "$APP_DIR/api/v1/views.py" << EOF
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.utils.view_mixins import BaseViewMixin
from apps.utils.responses import success_response, error_response

# Create your API views here.
EOF

cat > "$APP_DIR/api/v1/urls.py" << EOF
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = '${APP_NAME}_api_v1'

router = DefaultRouter()
# Register your API viewsets here
# router.register(r'items', views.YourViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
EOF

# Create service file
cat > "$APP_DIR/services/${APP_NAME}_service.py" << EOF
from typing import Any, Dict, List, Optional
from django.db import transaction
from django.core.exceptions import ValidationError


class Base${APP_NAME^}Service:
    """
    Base service class for $APP_NAME operations.
    """
    
    @staticmethod
    def validate_data(data: Dict[str, Any]) -> None:
        """
        Validate incoming data.
        """
        pass
    
    @staticmethod
    @transaction.atomic
    def create_item(data: Dict[str, Any]) -> Any:
        """
        Create a new item.
        """
        # Implement your creation logic here
        pass
    
    @staticmethod
    @transaction.atomic
    def update_item(item_id: int, data: Dict[str, Any]) -> Any:
        """
        Update an existing item.
        """
        # Implement your update logic here
        pass
    
    @staticmethod
    @transaction.atomic
    def delete_item(item_id: int) -> bool:
        """
        Delete an item.
        """
        # Implement your deletion logic here
        pass
EOF

# Create management command
cat > "$APP_DIR/management/commands/setup_dev.py" << EOF
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Setup development data for $APP_NAME app'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing data before setup',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        clean = options['clean']
        
        if clean:
            self.stdout.write('Cleaning existing $APP_NAME data...')
            # Add your cleanup logic here
        
        self.stdout.write('Setting up development data for $APP_NAME...')
        # Add your setup logic here
        
        self.stdout.write(
            self.style.SUCCESS(
                'Successfully setup development data for $APP_NAME'
            )
        )
EOF

# Add app to INSTALLED_APPS in settings/base.py
SETTINGS_FILE="$BACKEND_DIR/project_config/settings/base.py"
if [ -f "$SETTINGS_FILE" ]; then
    # Check if app is already in INSTALLED_APPS
    if ! grep -q "\"apps.$APP_NAME\"" "$SETTINGS_FILE"; then
        # Find the line with "apps.utils", and add the new app after it
        sed -i "/\"apps\.utils\",/a\\    \"apps.$APP_NAME\"," "$SETTINGS_FILE"
        echo "✅ Added 'apps.$APP_NAME' to INSTALLED_APPS in settings/base.py"
    else
        echo "ℹ️  'apps.$APP_NAME' already exists in INSTALLED_APPS"
    fi
else
    echo "⚠️  Could not find settings/base.py file"
fi

# Add app URLs to project_config/urls.py
URLS_FILE="$BACKEND_DIR/project_config/urls.py"
if [ -f "$URLS_FILE" ]; then
    # Check if app URL is already included
    if ! grep -q "path('api/v1/$APP_NAME/'," "$URLS_FILE"; then
        # Find the line with the last path() entry and add the new URL pattern after it
        sed -i "/path('api\/', include('apps\.authentication\.urls')),/a\\    path('api/v1/$APP_NAME/', include('apps.$APP_NAME.api.v1.urls'))," "$URLS_FILE"
        echo "✅ Added 'api/v1/$APP_NAME/' URL pattern to project_config/urls.py"
    else
        echo "ℹ️  'api/v1/$APP_NAME/' URL pattern already exists in urls.py"
    fi
else
    echo "⚠️  Could not find project_config/urls.py file"
fi

echo ""
echo "✅ Successfully created app '$APP_NAME' in apps directory!"
echo ""
echo "📝 Next steps:"
echo "1. ✅ Added 'apps.$APP_NAME' to INSTALLED_APPS"
echo "2. ✅ Added URL patterns to project_config/urls.py"
echo "3. Create your models and run migrations"
echo ""
echo "🗂️  App structure created:"
echo "   apps/$APP_NAME/"
echo "   ├── __init__.py"
echo "   ├── admin.py"
echo "   ├── apps.py"
echo "   ├── models/"
echo "   │   ├── __init__.py"
echo "   │   └── base.py"
echo "   ├── permissions.py"
echo "   ├── tests/"
echo "   │   ├── __init__.py"
echo "   │   ├── test_models.py"
echo "   │   └── test_views.py"
echo "   ├── urls.py"
echo "   ├── views.py"
echo "   ├── api/"
echo "   │   ├── __init__.py"
echo "   │   └── v1/"
echo "   │       ├── __init__.py"
echo "   │       ├── serializers.py"
echo "   │       ├── urls.py"
echo "   │       └── views.py"
echo "   ├── management/"
echo "   │   ├── __init__.py"
echo "   │   └── commands/"
echo "   │       ├── __init__.py"
echo "   │       └── setup_dev.py"
echo "   ├── migrations/"
echo "   │   └── __init__.py"
echo "   ├── services/"
echo "   │   ├── __init__.py"
echo "   │   └── ${APP_NAME}_service.py"
echo "   └── tests/"
echo "       └── __init__.py"