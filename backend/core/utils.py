"""Core utilities module."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters


class UniversalAutoFilterMixin:
    """
    Mixin that automatically applies standard filtering, searching, and ordering
    to list views. This is used to reduce boilerplate in views.
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = []
    ordering_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_filterset_fields(self):
        """Override this method to dynamically set filterset_fields based on model fields"""
        return getattr(self, 'filterset_fields', '__all__')


__all__ = ['UniversalAutoFilterMixin']
