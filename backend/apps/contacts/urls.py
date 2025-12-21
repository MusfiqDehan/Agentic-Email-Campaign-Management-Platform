from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContactViewSet, ContactListViewSet

router = DefaultRouter()
router.register(r'lists', ContactListViewSet, basename='contactlist')
router.register(r'', ContactViewSet, basename='contact')

urlpatterns = [
    path('', include(router.urls)),
]
