"""
Configuration synchronization utilities for shared and organization-specific
email configurations.

This module provides utilities to:
- Resolve the effective email provider across the organization → shared hierarchy
- Validate configuration hierarchy
- Check rate limits across all configuration layers
- Ensure consistency between OrganizationEmailConfiguration and EmailProvider

Terminology note: "tenant" is the legacy name for what the schema now calls an
Organization. Public helpers take `organization_id`; the model aliases
TenantEmailProvider / TenantEmailConfiguration remain for compatibility.
"""

import logging
from typing import Dict, Tuple, List

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class ConfigurationHierarchy:
    """Manages the hierarchy of email configuration precedence."""

    @staticmethod
    def get_effective_provider(organization_id: str = None, rule=None, preferred_provider_id: str = None):
        """
        Get the effective email provider following the hierarchy:
        1. Manually specified preferred provider (via API request)
        2. Rule-specific preferred provider
        3. Organization's primary provider
        4. Shared default provider

        Args:
            organization_id: Organization UUID
            rule: AutomationRule instance
            preferred_provider_id: Optional UUID of preferred EmailProvider to use (manual override)

        Returns:
            Tuple of (EmailProvider, OrganizationEmailProvider or None, config_dict)
        """
        from ..models import EmailProvider, TenantEmailProvider

        logger.info(
            f"[ConfigHierarchy] Getting effective provider - organization_id={organization_id}, "
            f"rule_id={getattr(rule, 'id', None)}, preferred_provider_id={preferred_provider_id}"
        )

        # HIGHEST PRIORITY: Manually specified provider via API request
        if preferred_provider_id:
            try:
                email_provider = EmailProvider.objects.filter(
                    id=preferred_provider_id,
                    is_active=True,
                ).first()

                if email_provider:
                    # Check if there's an organization-specific configuration for this provider
                    org_provider = None
                    if organization_id:
                        org_provider = TenantEmailProvider.objects.filter(
                            organization_id=organization_id,
                            provider=email_provider,
                            is_enabled=True
                        ).first()

                    if org_provider:
                        config = org_provider.get_effective_config()
                        logger.info(f"[ConfigHierarchy] Using manually specified provider with organization config: {email_provider.name}")
                        return (email_provider, org_provider, config)

                    config = email_provider.decrypt_config()
                    logger.info(f"[ConfigHierarchy] Using manually specified provider: {email_provider.name}")
                    return (email_provider, None, config)

                logger.warning(f"Preferred provider {preferred_provider_id} not found or not active, falling back to hierarchy")
            except Exception as e:
                logger.warning(f"Failed to get preferred provider {preferred_provider_id}: {e}, falling back to hierarchy")

        # Check rule-specific provider
        if rule and hasattr(rule, 'get_effective_email_provider'):
            try:
                org_provider = rule.get_effective_email_provider()
                if org_provider and org_provider.is_enabled:
                    config = org_provider.get_effective_config()
                    logger.info(f"[ConfigHierarchy] Using rule-specific provider: {org_provider.provider.name}")
                    return (org_provider.provider, org_provider, config)
            except Exception as e:
                logger.warning(f"Failed to get rule-specific provider: {e}")

        # Check rule's preferred_global_provider (a shared EmailProvider)
        if rule and getattr(rule, 'preferred_global_provider', None):
            try:
                shared_provider = rule.preferred_global_provider
                if shared_provider.is_active:
                    org_provider = None
                    if organization_id:
                        org_provider = TenantEmailProvider.objects.filter(
                            organization_id=organization_id,
                            provider=shared_provider,
                            is_enabled=True
                        ).first()

                    if org_provider:
                        config = org_provider.get_effective_config()
                        logger.info(f"[ConfigHierarchy] Using rule's preferred_global_provider with organization config: {shared_provider.name}")
                        return (shared_provider, org_provider, config)

                    config = shared_provider.decrypt_config()
                    logger.info(f"[ConfigHierarchy] Using rule's preferred_global_provider: {shared_provider.name}")
                    return (shared_provider, None, config)
            except Exception as e:
                logger.warning(f"Failed to get rule's preferred_global_provider: {e}")

        # Check organization's primary provider
        if organization_id:
            org_provider = TenantEmailProvider.objects.filter(
                organization_id=organization_id,
                is_primary=True,
                is_enabled=True,
                provider__is_active=True,
            ).select_related('provider').first()

            if org_provider:
                config = org_provider.get_effective_config()
                logger.info(f"[ConfigHierarchy] Using organization primary provider: {org_provider.provider.name}")
                return (org_provider.provider, org_provider, config)

            # Organization-owned provider flagged as its default
            owned_provider = EmailProvider.objects.filter(
                organization_id=organization_id,
                is_active=True,
                is_default=True,
            ).first()
            if owned_provider:
                config = owned_provider.decrypt_config()
                logger.info(f"[ConfigHierarchy] Using organization-owned default provider: {owned_provider.name}")
                return (owned_provider, None, config)

        # Fallback to the shared default provider (prioritise explicitly flagged default)
        fallback_provider = EmailProvider.objects.filter(
            organization__isnull=True,
            is_shared=True,
            is_active=True,
            is_default=True,
        ).first()

        if not fallback_provider:
            # Gracefully fall back to the highest-priority active shared provider
            fallback_provider = EmailProvider.objects.filter(
                organization__isnull=True,
                is_shared=True,
                is_active=True,
            ).order_by('priority', 'name').first()

        if fallback_provider:
            try:
                config = fallback_provider.decrypt_config()
            except Exception as e:
                logger.warning(
                    f"[ConfigHierarchy] Failed to decrypt config for provider {fallback_provider.name}: {e}. Using empty config.")
                config = {}

            logger.info(f"[ConfigHierarchy] Using fallback provider: {fallback_provider.name}")
            return (fallback_provider, None, config)

        logger.error("[ConfigHierarchy] No active provider found after evaluating hierarchy")
        return None, None, {}

    @staticmethod
    def get_effective_rate_limits(organization_id: str = None, provider=None, tenant_provider=None) -> Dict:
        """
        Get effective rate limits following the hierarchy:
        1. OrganizationEmailProvider custom limits (most restrictive)
        2. OrganizationEmailConfiguration limits
        3. EmailProvider limits (shared)

        Returns the MOST RESTRICTIVE limit at each level.

        Returns:
            Dict with emails_per_minute, emails_per_hour, emails_per_day
        """
        from ..models import TenantEmailConfiguration

        limits = {
            'emails_per_minute': float('inf'),
            'emails_per_hour': float('inf'),
            'emails_per_day': float('inf'),
        }

        # Apply provider limits if available
        if provider:
            limits['emails_per_minute'] = min(limits['emails_per_minute'], provider.max_emails_per_minute)
            limits['emails_per_hour'] = min(limits['emails_per_hour'], provider.max_emails_per_hour)
            limits['emails_per_day'] = min(limits['emails_per_day'], provider.max_emails_per_day)

        # Apply organization provider custom limits (more restrictive)
        if tenant_provider:
            org_limits = tenant_provider.get_rate_limits()
            limits['emails_per_minute'] = min(limits['emails_per_minute'], org_limits.get('emails_per_minute', float('inf')))
            limits['emails_per_hour'] = min(limits['emails_per_hour'], org_limits.get('emails_per_hour', float('inf')))
            limits['emails_per_day'] = min(limits['emails_per_day'], org_limits.get('emails_per_day', float('inf')))

        # Apply organization configuration limits (most restrictive)
        if organization_id:
            try:
                org_config = TenantEmailConfiguration.objects.get(organization_id=organization_id)
                limits['emails_per_minute'] = min(limits['emails_per_minute'], org_config.emails_per_minute)
                limits['emails_per_day'] = min(limits['emails_per_day'], org_config.emails_per_day)
            except TenantEmailConfiguration.DoesNotExist:
                pass

        # Convert infinity back to reasonable defaults
        return {k: (v if v != float('inf') else 0) for k, v in limits.items()}

    @staticmethod
    def get_effective_from_email(organization_id: str = None, provider_config: Dict = None, rule=None) -> str:
        """
        Get the effective from_email following the hierarchy:
        1. The organization's own verified sender email (sending-domains feature)
        2. Provider config from_email
        3. Legacy default_from_domain on the organization config
        4. settings.DEFAULT_FROM_EMAIL

        Preferring a registered SenderEmail keeps automation sends compatible
        with utils.sender_validation.validate_sender, which rejects addresses
        on a registered domain that are not active sender identities.

        Returns:
            Email address string (guaranteed to return a value)
        """
        from ..models import SenderEmail, TenantEmailConfiguration

        try:
            if organization_id:
                sender = (
                    SenderEmail.objects
                    .filter(
                        organization_id=organization_id,
                        status=SenderEmail.STATUS_ACTIVE,
                        is_active=True,
                    )
                    .select_related('domain')
                    .order_by('created_at')
                    .first()
                )
                if sender and sender.is_usable:
                    return sender.email_address

            # Provider configuration (typically the verified SES identity)
            if provider_config:
                from_email = (
                    provider_config.get('from_email')
                    or provider_config.get('default_from_email')
                    or provider_config.get('source_email')
                    or provider_config.get('smtp_username')
                )
                if from_email:
                    return from_email

            if organization_id:
                try:
                    org_config = TenantEmailConfiguration.objects.get(organization_id=organization_id)
                    if org_config.default_from_domain:
                        return f"noreply@{org_config.default_from_domain}"
                except TenantEmailConfiguration.DoesNotExist:
                    pass

            logger.warning(
                f"No from_email configured for organization {organization_id}; "
                f"falling back to settings.DEFAULT_FROM_EMAIL"
            )
            return settings.DEFAULT_FROM_EMAIL

        except Exception as e:
            logger.error(f"Error in get_effective_from_email: {e}", exc_info=True)
            return settings.DEFAULT_FROM_EMAIL


class RateLimitChecker:
    """Unified rate limit checking across all configuration layers."""

    @staticmethod
    def can_send_email(organization_id: str = None, provider=None, tenant_provider=None) -> Tuple[bool, str]:
        """
        Comprehensive check if email can be sent considering all rate limits.

        Returns:
            Tuple of (can_send: bool, reason: str)
        """
        from ..models import TenantEmailConfiguration

        # Check organization configuration status first
        if organization_id:
            try:
                org_config = TenantEmailConfiguration.objects.get(organization_id=organization_id)
                can_send, reason = org_config.can_send_email()
                if not can_send:
                    return False, f"Organization: {reason}"
            except TenantEmailConfiguration.DoesNotExist:
                logger.warning(f"No OrganizationEmailConfiguration found for organization {organization_id}")

        # Check organization provider limits
        if tenant_provider:
            can_send, reason = tenant_provider.can_send_email()
            if not can_send:
                return False, f"Organization Provider: {reason}"

        # Check provider limits
        if provider:
            can_send, reason = provider.can_send_email()
            if not can_send:
                return False, f"Provider: {reason}"

        return True, "OK"

    @staticmethod
    def increment_usage_counters(organization_id: str = None, provider=None, tenant_provider=None):
        """Increment usage counters across all applicable levels."""
        from ..models import TenantEmailConfiguration
        from .atomic_counters import increment_provider_send_counters

        if organization_id:
            try:
                org_config = TenantEmailConfiguration.objects.get(organization_id=organization_id)
                org_config.increment_email_usage()
            except TenantEmailConfiguration.DoesNotExist:
                logger.warning(f"Cannot increment usage for organization {organization_id}: config not found")

        increment_provider_send_counters(
            provider=provider, organization_provider=tenant_provider
        )


class ConfigurationValidator:
    """Validate configuration consistency and identify issues."""

    @staticmethod
    def validate_tenant_configuration(organization_id: str) -> Dict:
        """
        Validate all configuration layers for an organization.

        Returns:
            Dict with validation results and issues
        """
        from ..models import EmailProvider, TenantEmailConfiguration, TenantEmailProvider

        issues = []
        warnings = []
        info = {}

        # Check if organization configuration exists
        try:
            org_config = TenantEmailConfiguration.objects.get(organization_id=organization_id)
            info['organization_config'] = {
                'exists': True,
                'is_active': org_config.is_active,
                'is_suspended': org_config.is_suspended,
                'plan_type': org_config.plan_type,
                'package': org_config.package.name if org_config.package else None,
                'emails_per_day': org_config.emails_per_day,
            }
        except TenantEmailConfiguration.DoesNotExist:
            issues.append("No OrganizationEmailConfiguration found")
            info['organization_config'] = {'exists': False}

        # Check organization providers
        org_providers = TenantEmailProvider.objects.filter(
            organization_id=organization_id
        ).select_related('provider')

        info['organization_providers'] = {
            'count': org_providers.count(),
            'enabled_count': org_providers.filter(is_enabled=True).count(),
            'primary_count': org_providers.filter(is_primary=True).count(),
        }

        if org_providers.count() == 0:
            warnings.append("No OrganizationEmailProvider configured, will fallback to shared providers")

        primary_providers = org_providers.filter(is_primary=True)
        if primary_providers.count() > 1:
            issues.append(f"Multiple primary providers found: {primary_providers.count()}")
        elif primary_providers.count() == 0 and org_providers.count() > 0:
            warnings.append("No primary provider set among configured providers")

        # Check for inactive providers being used
        for op in org_providers.filter(is_enabled=True):
            if not op.provider.is_active:
                issues.append(f"Organization provider '{op.provider.name}' is enabled but the provider is inactive")

        # Check shared default provider exists
        default_provider = EmailProvider.objects.filter(
            is_default=True,
            is_shared=True,
            is_active=True,
        ).first()
        if not default_provider:
            issues.append("No shared default provider configured (required for fallback)")
        else:
            info['shared_default_provider'] = default_provider.name

        return {
            'organization_id': str(organization_id),
            'is_valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'info': info,
        }

    @staticmethod
    def validate_all_configurations() -> List[Dict]:
        """Validate every organization's configuration."""
        from ..models import TenantEmailConfiguration

        return [
            ConfigurationValidator.validate_tenant_configuration(org_config.organization_id)
            for org_config in TenantEmailConfiguration.objects.all()
        ]

    @staticmethod
    def find_orphaned_configurations() -> Dict:
        """
        Find configurations that are orphaned or inconsistent.

        Returns:
            Dict with lists of orphaned entities
        """
        from django.db.models import Count
        from ..models import EmailProvider, TenantEmailProvider

        orphaned = {
            'organization_providers_with_inactive_provider': [],
            'duplicate_primary_providers': [],
            'inactive_default_providers': [],
        }

        # Organization providers pointing at an inactive provider
        for op in TenantEmailProvider.objects.filter(is_enabled=True).select_related('provider'):
            if not op.provider.is_active:
                orphaned['organization_providers_with_inactive_provider'].append({
                    'organization_id': str(op.organization_id),
                    'provider_name': op.provider.name,
                })

        # Organizations with multiple primary providers
        duplicates = TenantEmailProvider.objects.filter(
            is_primary=True
        ).values('organization_id').annotate(count=Count('id')).filter(count__gt=1)

        for dup in duplicates:
            orphaned['duplicate_primary_providers'].append({
                'organization_id': str(dup['organization_id']),
                'count': dup['count'],
            })

        # Default providers that are not active
        for provider in EmailProvider.objects.filter(is_default=True, is_active=False):
            orphaned['inactive_default_providers'].append({
                'provider_name': provider.name,
                'provider_type': provider.provider_type,
            })

        return orphaned


class ConfigurationSync:
    """Synchronize configurations between shared and organization levels."""

    @staticmethod
    def sync_tenant_from_global(organization_id: str, global_provider_id: str = None) -> Tuple[bool, str]:
        """
        Sync an organization's configuration from a shared provider's settings.

        Returns:
            Tuple of (success: bool, message: str)
        """
        from ..models import EmailProvider, TenantEmailConfiguration, TenantEmailProvider

        try:
            org_config, created = TenantEmailConfiguration.objects.get_or_create(
                organization_id=organization_id,
            )

            # Get the shared provider to sync from
            if global_provider_id:
                shared_provider = EmailProvider.objects.get(id=global_provider_id)
            else:
                shared_provider = EmailProvider.objects.filter(
                    is_default=True,
                    is_shared=True,
                    is_active=True,
                ).first()

            if not shared_provider:
                return False, "No shared provider found to sync from"

            org_provider, op_created = TenantEmailProvider.objects.get_or_create(
                organization_id=organization_id,
                provider=shared_provider,
                defaults={
                    'is_enabled': True,
                    'is_primary': True,
                }
            )

            # Ensure rate limits in the organization config don't exceed provider limits
            org_config.emails_per_minute = min(
                org_config.emails_per_minute, shared_provider.max_emails_per_minute
            )
            org_config.emails_per_day = min(
                org_config.emails_per_day, shared_provider.max_emails_per_day
            )
            org_config.save()

            action = "created and synced" if created or op_created else "synced"
            return True, f"Organization configuration {action} from shared provider '{shared_provider.name}'"

        except Exception as e:
            logger.error(f"Failed to sync organization {organization_id}: {e}")
            return False, f"Sync failed: {str(e)}"
