"""
Core module for shared utilities and mixins.
This module provides compatibility for legacy imports referencing 'core'.
"""

from apps.utils.view_mixins import ResponseMixin

# Alias for backward compatibility - old code uses CustomResponseMixin
# but the actual implementation is ResponseMixin in apps.utils
CustomResponseMixin = ResponseMixin

__all__ = ['CustomResponseMixin', 'ResponseMixin']
