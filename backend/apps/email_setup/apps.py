from django.apps import AppConfig


class NotifyHubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'automation_rule'

    def ready(self):  # pragma: no cover - side-effect import
        from . import ses_event_handlers  # noqa: F401
