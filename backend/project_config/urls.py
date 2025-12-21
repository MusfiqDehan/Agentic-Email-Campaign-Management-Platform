"""
URL configuration for Email Campaign Management Platform project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/campaigns/', include('apps.campaigns.urls')),
    path('api/contacts/', include('apps.contacts.urls')),
    path('api/templates/', include('apps.templates.urls')),
]
