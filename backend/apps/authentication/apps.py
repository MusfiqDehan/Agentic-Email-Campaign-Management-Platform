from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.authentication'
    
    def ready(self):
        """Import signals when app is ready."""
        try:
            import apps.authentication.signals  # noqa: F401
        except ImportError:
            pass