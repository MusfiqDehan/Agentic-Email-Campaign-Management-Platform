"""
URL configuration for Email Campaign Management Platform.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/campaigns/', include('apps.campaigns.urls')),

    # DRF Spectacular URLs for API documentation
    path(f"api/v1/schemas/swagger.json", SpectacularAPIView.as_view(), name="schema-json"),
    path(f"api/v1/schemas/", SpectacularAPIView.as_view(), name="schema"),
    path(f"api/v1/schemas/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path(f"api/v1/schemas/redoc", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

]