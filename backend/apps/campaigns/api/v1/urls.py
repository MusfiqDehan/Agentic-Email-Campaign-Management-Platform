from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'campaigns_api_v1'

router = DefaultRouter()
# Register your API viewsets here
# router.register(r'items', views.YourViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
