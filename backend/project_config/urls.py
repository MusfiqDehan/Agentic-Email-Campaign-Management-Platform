"""
URL configuration for Email Campaign Management Platform.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.authentication.api.v1.urls')),
    path('api/', include('apps.authentication.urls')),  # Keep old paths for backward compatibility
    path('api/v1/campaigns/', include('apps.campaigns.api.v1.urls')),
]