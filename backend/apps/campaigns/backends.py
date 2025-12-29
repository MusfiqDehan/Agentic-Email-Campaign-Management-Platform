import logging
from typing import Any, Dict, Tuple
from urllib.parse import urlparse

from django.conf import settings
from django.core.mail import get_connection
from django.core.mail.backends.smtp import EmailBackend
from django_ses import settings as django_ses_settings


def _clean_kwargs(raw_kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Remove keys with empty values so Django's backend constructors stay happy."""

    return {
        key: value
        for key, value in raw_kwargs.items()
        if value not in (None, "")
    }


logger = logging.getLogger(__name__)


class ProviderBackendResolver:
    """Maps provider types to Django email backend implementations."""

    DEFAULT_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

    @classmethod
    def resolve(cls, provider_type: str, config: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        provider_key = (provider_type or "").upper()

        if provider_key == "AWS_SES":
            return cls._build_ses_backend(config)

        if provider_key in {"SMTP", "GMAIL_SMTP", "OUTLOOK_SMTP"}:
            return cls._build_smtp_backend(config)

        if provider_key == "INTERNAL":
            return "django.core.mail.backends.console.EmailBackend", {}, {
                "from_email": config.get("from_email") or config.get("default_from_email")
            }

        # Fallback to SMTP for any other provider if host credentials are supplied.
        return cls._build_smtp_backend(config)

    @staticmethod
    def _build_ses_backend(config: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        access_key = config.get("aws_access_key") or config.get("aws_access_key_id")
        secret_key = config.get("aws_secret_key") or config.get("aws_secret_access_key")
        region = (
            config.get("aws_region_name")
            or config.get("region_name")
            or config.get("region")
        )

        missing = [
            label
            for label, value in {
                "aws_access_key": access_key,
                "aws_secret_key": secret_key,
                "aws_region_name": region,
            }.items()
            if not value
        ]

        if missing:
            raise ValueError(
                "Missing required AWS SES configuration keys: " + ", ".join(missing)
            )

        # Default auto throttle to 0 to avoid GetSendQuota unless explicitly requested
        auto_throttle = config.get("aws_auto_throttle") or config.get("auto_throttle")
        if auto_throttle is None:
            auto_throttle = 0

        # Respect explicit endpoint if provided; normalise to a full URL expected by django-ses.
        # If a bare hostname like "email.eu-north-1.amazonaws.com" (or just a region) is supplied,
        # coerce it to "https://email.<region>.amazonaws.com" to avoid "Invalid endpoint" errors.
        raw_endpoint = config.get("aws_region_endpoint") or config.get("endpoint_url")

        def _normalise_endpoint_url(region_name: str, value: str | None) -> str | None:
            if not value:
                return None
            v = str(value).strip()
            # If the user accidentally provided just a region, build the standard SES endpoint.
            if v and "." not in v and "-" in v:
                return f"https://email.{v}.amazonaws.com"
            # If it's already a URL, keep as-is.
            if v.startswith("http://") or v.startswith("https://"):
                return v
            # If it's a bare hostname, prefix https://
            return f"https://{v}"

        region_endpoint = _normalise_endpoint_url(region, raw_endpoint)
        if raw_endpoint and region_endpoint and region_endpoint.startswith("https://") is False:
            logger.warning(
                "AWS SES endpoint provided without scheme; normalised to %s (from %s)",
                region_endpoint,
                raw_endpoint,
            )
        resolved_endpoint_url = region_endpoint or f"https://email.{region}.amazonaws.com"
        parsed_endpoint = urlparse(resolved_endpoint_url)
        resolved_endpoint_host = parsed_endpoint.netloc or resolved_endpoint_url.replace("https://", "")
        try:
            setattr(settings, "AWS_SES_REGION_NAME", region)
            setattr(settings, "AWS_SES_REGION_ENDPOINT", resolved_endpoint_host)
            setattr(settings, "AWS_SES_REGION_ENDPOINT_URL", resolved_endpoint_url)
            django_ses_settings.AWS_SES_REGION_NAME = region
            django_ses_settings.AWS_SES_REGION_ENDPOINT = resolved_endpoint_host
            django_ses_settings.AWS_SES_REGION_ENDPOINT_URL = resolved_endpoint_url
        except Exception:
            # Settings may be locked in some contexts; ignore if we can't set them.
            pass

        # Default to SES v2 unless explicitly disabled
        use_ses_v2 = config.get("use_ses_v2")
        if use_ses_v2 is None:
            use_ses_v2 = True

        # Ensure global django-ses settings reflect our preferences to avoid internal fallbacks
        try:
            # Disable auto-throttle to prevent GetAccount/GetSendQuota calls that can fail with
            # region-scoping errors when using temporary credentials or cross-region configs.
            setattr(settings, "AWS_SES_AUTO_THROTTLE", 0)
            # Prefer SESv2 at the global level as well for consistency
            setattr(settings, "USE_SES_V2", True)
            django_ses_settings.AWS_SES_AUTO_THROTTLE = 0
            django_ses_settings.USE_SES_V2 = True
        except Exception:
            pass

        kwargs = _clean_kwargs(
            {
                "aws_access_key": access_key,
                "aws_secret_key": secret_key,
                "aws_session_token": config.get("aws_session_token"),
                "aws_session_profile": config.get("aws_session_profile"),
                "aws_region_name": region,
                "aws_region_endpoint": region_endpoint,
                "aws_auto_throttle": auto_throttle,
                "aws_config": config.get("aws_config"),
                "ses_source_arn": config.get("ses_source_arn"),
                "ses_from_arn": config.get("ses_from_arn"),
                "ses_return_path_arn": config.get("ses_return_path_arn"),
                "use_ses_v2": use_ses_v2,
                "fail_silently": config.get("fail_silently", False),
            }
        )

        # Optionally prime runtime settings used by django-ses if values are provided per provider.
        from_email = (
            config.get("from_email")
            or config.get("default_from_email")
            or config.get("source_email")
        )
        return_path = config.get("return_path") or config.get("bounce_email")

        if from_email:
            setattr(settings, "AWS_SES_FROM_EMAIL", from_email)
        if return_path:
            setattr(settings, "AWS_SES_RETURN_PATH", return_path)

        return "django_ses.SESBackend", kwargs, {"from_email": from_email}

    @staticmethod
    def _build_smtp_backend(config: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        host = (
            config.get("host")
            or config.get("smtp_host")
            or config.get("smtp_server")
            or config.get("email_host")
            or config.get("email_host_url")
        )
        port = config.get("port") or config.get("smtp_port") or config.get("email_port")
        username = (
            config.get("username")
            or config.get("smtp_username")
            or config.get("email_host_user")
        )
        password = config.get("password") or config.get("smtp_password")
        use_tls = config.get("use_tls")
        use_ssl = config.get("use_ssl")
        timeout = config.get("timeout")

        logger.info(
            f"[ProviderBackendResolver] Building SMTP backend - "
            f"host={host}, port={port}, username={username}, "
            f"use_tls={use_tls}, use_ssl={use_ssl}, "
            f"config_keys={list(config.keys())}"
        )

        kwargs = _clean_kwargs(
            {
                "host": host,
                "port": port,
                "username": username,
                "password": password,
                "use_tls": use_tls,
                "use_ssl": use_ssl,
                "timeout": timeout,
                "fail_silently": config.get("fail_silently", False),
            }
        )
        return ProviderBackendResolver.DEFAULT_BACKEND, kwargs, {
            "from_email": config.get("from_email")
            or config.get("default_from_email")
            or username
        }


class DynamicEmailBackend(EmailBackend):
    """Utility helpers to build email backend instances on the fly."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool | None = None,
        use_ssl: bool | None = None,
        fail_silently: bool = False,
        **kwargs: Any,
    ) -> None:
        # Preserve backwards compatibility for callers instantiating this class directly.
        super().__init__(
            host=host,
            port=port,
            username=username,
            password=password,
            use_tls=use_tls,
            use_ssl=use_ssl,
            fail_silently=fail_silently,
            **kwargs,
        )

    @staticmethod
    def build_smtp_connection(
        host: str,
        port: int,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool | None = None,
        use_ssl: bool | None = None,
        timeout: int | None = None,
        fail_silently: bool = False,
    ):
        return get_connection(
            backend=ProviderBackendResolver.DEFAULT_BACKEND,
            host=host,
            port=port,
            username=username,
            password=password,
            use_tls=use_tls,
            use_ssl=use_ssl,
            timeout=timeout,
            fail_silently=fail_silently,
        )

    @staticmethod
    def build_provider_connection(
        provider_type: str,
        config: Dict[str, Any],
        fail_silently: bool = False,
    ) -> Tuple[Any, Dict[str, Any]]:
        backend_path, backend_kwargs, metadata = ProviderBackendResolver.resolve(provider_type, config)
        backend_kwargs = {**backend_kwargs, "fail_silently": fail_silently or backend_kwargs.get("fail_silently", False)}
        connection = get_connection(backend=backend_path, **backend_kwargs)
        return connection, metadata