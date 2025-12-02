from django.apps import AppConfig


class CampaignsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'campaigns'

    def ready(self):  # pragma: no cover - side-effect import
        from . import ses_event_handlers  # noqa: F401
