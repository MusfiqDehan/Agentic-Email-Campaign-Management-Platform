from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)


class CampaignsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.campaigns'
    label = 'campaigns'

    def ready(self):  # pragma: no cover - side-effect import
        from django.conf import settings
        from . import ses_event_handlers  # noqa: F401
        
        # Import signals to register them
        from . import signals  # noqa: F401
        
        # Verify encryption key is configured for provider credentials
        self._verify_encryption_key(settings)
    
    def _verify_encryption_key(self, settings):
        """
        Verify that encryption key is properly configured for email provider credentials.
        
        Raises ImproperlyConfigured if no encryption key is available, which would
        prevent secure storage of provider credentials.
        """
        encryption_key = getattr(settings, 'EMAIL_CONFIG_ENCRYPTION_KEY', None)
        secret_key = getattr(settings, 'SECRET_KEY', None)
        
        if not encryption_key and not secret_key:
            raise ImproperlyConfigured(
                "Either EMAIL_CONFIG_ENCRYPTION_KEY or SECRET_KEY must be set in settings "
                "to enable encryption of email provider credentials. "
                "Generate a key using: python manage.py generate_encryption_key"
            )
        
        if not encryption_key:
            logger.warning(
                "EMAIL_CONFIG_ENCRYPTION_KEY is not set. Using SECRET_KEY for encryption. "
                "For production, set a dedicated EMAIL_CONFIG_ENCRYPTION_KEY for better security."
            )
        else:
            # Validate encryption key format (should be valid for Fernet)
            try:
                import base64
                key_bytes = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
                # Try to decode as base64 to verify it's a valid Fernet key
                decoded = base64.urlsafe_b64decode(key_bytes)
                if len(decoded) != 32:
                    logger.warning(
                        f"EMAIL_CONFIG_ENCRYPTION_KEY should be 32 bytes when decoded. "
                        f"Current key decodes to {len(decoded)} bytes."
                    )
            except Exception as e:
                logger.warning(
                    f"EMAIL_CONFIG_ENCRYPTION_KEY format validation warning: {e}. "
                    "Ensure it's a valid Fernet-compatible key."
                )
        
        logger.debug("Encryption key verification completed for campaigns app.")
