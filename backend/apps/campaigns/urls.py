from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CampaignViewSet, CampaignContactViewSet

router = DefaultRouter()
router.register(r'', CampaignViewSet, basename='campaign')
router.register(r'contacts', CampaignContactViewSet, basename='campaign-contact')

urlpatterns = [
    path('', include(router.urls)),
]
