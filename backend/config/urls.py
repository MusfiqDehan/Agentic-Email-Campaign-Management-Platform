"""
URL configuration for Email Campaign Management Platform.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from django.http import JsonResponse
from django.shortcuts import redirect
from health_check.views import HealthCheckView


def liveness(request):
    """Fast liveness probe for Docker/Traefik — no DB/cache/storage checks."""
    return JsonResponse({"status": "ok"})

# django-health-check 4.x dropped `health_check.urls`; checks are now chosen
# per-view. Keep the same three checks the per-backend apps used to provide.
# DNS and Mail are intentionally excluded from the defaults: this endpoint
# backs the Docker/Traefik healthcheck poll, and Mail would open a live SMTP
# connection to the configured provider on every hit.
health_check_view = HealthCheckView.as_view(
    checks=(
        "health_check.checks.Database",
        "health_check.checks.Cache",
        "health_check.checks.Storage",
    )
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/campaigns/', include('apps.campaigns.urls')),

    # DRF Spectacular URLs for API documentation
    path(f"api/v1/schemas/swagger.json", SpectacularAPIView.as_view(), name="schema-json"),
    path(f"api/v1/schemas/", SpectacularAPIView.as_view(), name="schema"),
    path(f"api/v1/schemas/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path(f"api/v1/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui-legacy"),
    path(f"api/v1/schemas/redoc", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # Liveness probe (Docker/Traefik — must respond quickly, no dependency checks)
    path('api/v1/live/', liveness, name='liveness'),
    # Full health check endpoint (monitoring — DB, cache, storage)
    path('api/v1/healthz/', health_check_view, name='health-check'),
]

# Media files served by Nginx in production, Django fallback in development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)