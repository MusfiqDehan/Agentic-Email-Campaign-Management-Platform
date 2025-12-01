from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'email_setup'

router = DefaultRouter()
# Register your viewsets here
# router.register(r'items', YourViewSet)

urlpatterns = [
    path('api/v1/', include(router.urls)),
]
