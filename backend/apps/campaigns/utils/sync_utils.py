"""
Configuration synchronization utilities for global and tenant-specific email configurations.

This module provides utilities to:
- Sync global email provider settings with tenant-specific overrides
- Validate configuration hierarchy
- Check rate limits across all configuration layers
- Ensure consistency between TenantEmailConfiguration and EmailProvider
"""

import logging
from typing import Dict, Tuple, Optional, List
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)


class ConfigurationHierarchy:
    """Manages the hierarchy of email configuration precedence."""
    
    @staticmethod
    def get_effective_provider(tenant_id: str = None, rule=None, preferred_provider_id: str = None):
        """
        Get the effective email provider following the hierarchy:
        1. Manually specified preferred provider (via API request)
        2. Rule-specific preferred provider
        3. Tenant's primary provider
        4. Global default provider
        
        Args:
            tenant_id: Tenant UUID
            rule: AutomationRule instance
            preferred_provider_id: Optional UUID of preferred EmailProvider to use (manual override)
            
        Returns:
            Tuple of (EmailProvider, TenantEmailProvider or None, config_dict)
        """
        from ..models import EmailProvider, TenantEmailProvider
        
        logger.info(f"[ConfigHierarchy] Getting effective provider - tenant_id={tenant_id}, rule_id={getattr(rule, 'id', None)}, preferred_provider_id={preferred_provider_id}")
        
        # HIGHEST PRIORITY: Manually specified provider via API request
        if preferred_provider_id:
            try:
                # Try to get as EmailProvider first
                email_provider = EmailProvider.objects.filter(
                    id=preferred_provider_id,
                    activated_by_root=True,
                    activated_by_tmd=True
                ).first()
                
                if email_provider:
                    # Check if there's a tenant-specific configuration for this provider
                    tenant_provider = None
                    if tenant_id:
                        tenant_provider = TenantEmailProvider.objects.filter(
                            tenant_id=tenant_id,
                            provider=email_provider,
                            is_enabled=True
                        ).first()
                    
                    if tenant_provider:
                        config = tenant_provider.get_effective_config()
                        logger.info(f"[ConfigHierarchy] Using manually specified provider with tenant config: {email_provider.name}")
                        return (email_provider, tenant_provider, config)
                    else:
                        # Use global provider config
                        config = email_provider.decrypt_config()
                        logger.info(f"[ConfigHierarchy] Using manually specified global provider: {email_provider.name}")
                        return (email_provider, None, config)
                else:
                    logger.warning(f"Preferred provider {preferred_provider_id} not found or not active, falling back to hierarchy")
            except Exception as e:
                logger.warning(f"Failed to get preferred provider {preferred_provider_id}: {e}, falling back to hierarchy")
        
        # Check rule-specific provider
        if rule and hasattr(rule, 'get_effective_email_provider'):
            try:
                tenant_provider = rule.get_effective_email_provider()
                if tenant_provider and tenant_provider.is_enabled:
                    config = tenant_provider.get_effective_config()
                    logger.info(f"[ConfigHierarchy] Using rule-specific provider: {tenant_provider.provider.name}, config_keys={list(config.keys())}")
                    return (
                        tenant_provider.provider,
                        tenant_provider,
                        config
                    )
            except Exception as e:
                logger.warning(f"Failed to get rule-specific provider: {e}")
        
        # Check rule's preferred_global_provider (for global rules)
        if rule and hasattr(rule, 'preferred_global_provider') and rule.preferred_global_provider:
            try:
                global_provider = rule.preferred_global_provider
                if global_provider.activated_by_root and global_provider.activated_by_tmd:
                    # Check if there's a tenant-specific config for this provider
                    tenant_provider = None
                    if tenant_id:
                        tenant_provider = TenantEmailProvider.objects.filter(
                            tenant_id=tenant_id,
                            provider=global_provider,
                            is_enabled=True
                        ).first()
                    
                    if tenant_provider:
                        config = tenant_provider.get_effective_config()
                        logger.info(f"[ConfigHierarchy] Using rule's preferred_global_provider with tenant config: {global_provider.name}")
                        return (global_provider, tenant_provider, config)
                    else:
                        # Use global provider config
                        config = global_provider.decrypt_config()
                        logger.info(f"[ConfigHierarchy] Using rule's preferred_global_provider: {global_provider.name}")
                        return (global_provider, None, config)
            except Exception as e:
                logger.warning(f"Failed to get rule's preferred_global_provider: {e}")
        
        # Check tenant's primary provider
        if tenant_id:
            tenant_provider = TenantEmailProvider.objects.filter(
                tenant_id=tenant_id,
                is_primary=True,
                is_enabled=True,
                provider__activated_by_root=True,
                provider__activated_by_tmd=True
            ).select_related('provider').first()
            
            if tenant_provider:
                config = tenant_provider.get_effective_config()
                logger.info(f"[ConfigHierarchy] Using tenant primary provider: {tenant_provider.provider.name}, config_keys={list(config.keys())}")
                return (
                    tenant_provider.provider,
                    tenant_provider,
                    config
                )
        
        # Fallback to global default provider (prioritise explicitly flagged default)
        fallback_provider = EmailProvider.objects.filter(
            tenant_id__isnull=True,
            activated_by_root=True,
            activated_by_tmd=True,
            is_default=True
        ).first()

        if not fallback_provider:
            # Gracefully fall back to the highest-priority active global provider
            fallback_provider = EmailProvider.objects.filter(
                tenant_id__isnull=True,
                activated_by_root=True,
                activated_by_tmd=True
            ).order_by('priority', 'name').first()

        if fallback_provider:
            try:
                config = fallback_provider.decrypt_config()
            except Exception as e:
                logger.warning(
                    f"[ConfigHierarchy] Failed to decrypt config for provider {fallback_provider.name}: {e}. Using empty config.")
                config = {}

            logger.info(
                f"[ConfigHierarchy] Using fallback provider: {fallback_provider.name}, config_keys={list(config.keys())}")
            return (
                fallback_provider,
                None,
                config
            )

        logger.error("[ConfigHierarchy] No active provider found after evaluating hierarchy")
        return None, None, {}
    
    @staticmethod
    def get_effective_rate_limits(tenant_id: str = None, provider=None, tenant_provider=None) -> Dict:
        """
        Get effective rate limits following the hierarchy:
        1. TenantEmailProvider custom limits (most restrictive)
        2. TenantEmailConfiguration limits
        3. EmailProvider limits (global)
        
        Returns the MOST RESTRICTIVE limit at each level.
        
        Args:
            tenant_id: Tenant UUID
            provider: EmailProvider instance
            tenant_provider: TenantEmailProvider instance
            
        Returns:
            Dict with emails_per_minute, emails_per_hour, emails_per_day
        """
        from ..models import TenantEmailConfiguration
        
        # Start with global provider limits (least restrictive baseline)
        limits = {
            'emails_per_minute': float('inf'),
            'emails_per_hour': float('inf'),
            'emails_per_day': float('inf'),
        }
        
        # Apply global provider limits if available
        if provider:
            limits['emails_per_minute'] = min(limits['emails_per_minute'], provider.max_emails_per_minute)
            limits['emails_per_hour'] = min(limits['emails_per_hour'], provider.max_emails_per_hour)
            limits['emails_per_day'] = min(limits['emails_per_day'], provider.max_emails_per_day)
        
        # Apply tenant provider custom limits (more restrictive)
        if tenant_provider:
            tenant_limits = tenant_provider.get_rate_limits()
            limits['emails_per_minute'] = min(limits['emails_per_minute'], tenant_limits.get('emails_per_minute', float('inf')))
            limits['emails_per_hour'] = min(limits['emails_per_hour'], tenant_limits.get('emails_per_hour', float('inf')))
            limits['emails_per_day'] = min(limits['emails_per_day'], tenant_limits.get('emails_per_day', float('inf')))
        
        # Apply tenant configuration limits (most restrictive)
        if tenant_id:
            try:
                tenant_config = TenantEmailConfiguration.objects.get(tenant_id=tenant_id)
                # TenantEmailConfiguration has per_minute, per_day, and per_month
                limits['emails_per_minute'] = min(limits['emails_per_minute'], tenant_config.emails_per_minute)
                limits['emails_per_day'] = min(limits['emails_per_day'], tenant_config.emails_per_day)
                # Note: per_month is only in tenant config, not in provider
            except TenantEmailConfiguration.DoesNotExist:
                pass
        
        # Convert infinity back to reasonable defaults
        limits = {k: (v if v != float('inf') else 0) for k, v in limits.items()}
        
        return limits
    
    @staticmethod
    def get_effective_from_email(tenant_id: str = None, provider_config: Dict = None, rule=None) -> str:
        """
        Get the effective from_email following the hierarchy:
        1. Tenant custom verified domain
        2. Tenant default domain
        3. Provider from_email
        4. Fallback email
        
        Args:
            tenant_id: Tenant UUID
            provider_config: Decrypted provider configuration dict
            rule: AutomationRule instance (unused, kept for backward compatibility)
            
        Returns:
            Email address string (guaranteed to return a value)
        """
        from ..models import TenantEmailConfiguration
        
        try:
            # Check tenant configuration for custom domain
            if tenant_id:
                try:
                    tenant_config = TenantEmailConfiguration.objects.get(tenant_id=tenant_id)
                    # Only use tenant domain if explicitly configured (not default fallback)
                    if tenant_config.custom_domain_allowed and tenant_config.custom_domain and tenant_config.custom_domain_verified:
                        return f"noreply@{tenant_config.custom_domain}"
                    elif tenant_config.default_from_domain:
                        return f"noreply@{tenant_config.default_from_domain}"
                    # If no domain configured, fall through to provider config
                except TenantEmailConfiguration.DoesNotExist:
                    pass
            
            # Check provider configuration (this should be your verified email)
            # Support multiple field name variations for compatibility
            if provider_config:
                from_email = (
                    provider_config.get('from_email')
                    or provider_config.get('default_from_email')
                    or provider_config.get('source_email')
                    or provider_config.get('smtp_username')  # Sometimes username is the from email
                )
                if from_email:
                    return from_email
            
            # Last resort fallback (should be avoided in production)
            logger.warning(
                f"No from_email configured in provider or tenant (tenant_id={tenant_id}). "
                f"Using hardcoded fallback. Provider config keys: {list(provider_config.keys()) if provider_config else 'None'}"
            )
            return 'noreply@techforing.com'
        
        except Exception as e:
            logger.error(f"Error in get_effective_from_email: {e}", exc_info=True)
            # Always return a fallback, never None
            return 'noreply@techforing.com'


class RateLimitChecker:
    """Unified rate limit checking across all configuration layers."""
    
    @staticmethod
    def can_send_email(tenant_id: str = None, provider=None, tenant_provider=None) -> Tuple[bool, str]:
        """
        Comprehensive check if email can be sent considering all rate limits.
        
        Args:
            tenant_id: Tenant UUID
            provider: EmailProvider instance
            tenant_provider: TenantEmailProvider instance
            
        Returns:
            Tuple of (can_send: bool, reason: str)
        """
        from ..models import TenantEmailConfiguration
        
        # Check tenant configuration status first
        if tenant_id:
            try:
                tenant_config = TenantEmailConfiguration.objects.get(tenant_id=tenant_id)
                can_send, reason = tenant_config.can_send_email()
                if not can_send:
                    return False, f"Tenant: {reason}"
            except TenantEmailConfiguration.DoesNotExist:
                logger.warning(f"No TenantEmailConfiguration found for tenant {tenant_id}")
        
        # Check tenant provider limits
        if tenant_provider:
            can_send, reason = tenant_provider.can_send_email()
            if not can_send:
                return False, f"Tenant Provider: {reason}"
        
        # Check global provider limits
        if provider:
            can_send, reason = provider.can_send_email()
            if not can_send:
                return False, f"Global Provider: {reason}"
        
        return True, "OK"
    
    @staticmethod
    def increment_usage_counters(tenant_id: str = None, provider=None, tenant_provider=None):
        """
        Increment usage counters across all applicable levels.
        
        Args:
            tenant_id: Tenant UUID
            provider: EmailProvider instance
            tenant_provider: TenantEmailProvider instance
        """
        from ..models import TenantEmailConfiguration
        
        now = timezone.now()
        
        # Increment tenant configuration counters
        if tenant_id:
            try:
                tenant_config = TenantEmailConfiguration.objects.get(tenant_id=tenant_id)
                tenant_config.increment_usage()
            except TenantEmailConfiguration.DoesNotExist:
                logger.warning(f"Cannot increment usage for tenant {tenant_id}: config not found")
        
        # Increment global provider counters
        if provider:
            provider.emails_sent_today += 1
            provider.emails_sent_this_hour += 1
            provider.last_used_at = now
            provider.save(update_fields=['emails_sent_today', 'emails_sent_this_hour', 'last_used_at'])
        
        # Increment tenant provider counters
        if tenant_provider:
            tenant_provider.emails_sent_today += 1
            tenant_provider.emails_sent_this_hour += 1
            tenant_provider.last_used_at = now
            tenant_provider.save(update_fields=['emails_sent_today', 'emails_sent_this_hour', 'last_used_at'])


class ConfigurationValidator:
    """Validate configuration consistency and identify issues."""
    
    @staticmethod
    def validate_tenant_configuration(tenant_id: str) -> Dict:
        """
        Validate all configuration layers for a tenant.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Dict with validation results and issues
        """
        from ..models import (
            TenantEmailConfiguration, TenantEmailProvider,
            EmailProvider
        )
        
        issues = []
        warnings = []
        info = {}
        
        # Check if tenant configuration exists
        try:
            tenant_config = TenantEmailConfiguration.objects.get(tenant_id=tenant_id)
            info['tenant_config'] = {
                'exists': True,
                'activated_by_root': tenant_config.activated_by_root,
                'activated_by_tmd': tenant_config.activated_by_tmd,
                'is_suspended': tenant_config.is_suspended,
                'plan_type': tenant_config.plan_type,
                'emails_per_day': tenant_config.emails_per_day,
            }
        except TenantEmailConfiguration.DoesNotExist:
            issues.append("No TenantEmailConfiguration found")
            info['tenant_config'] = {'exists': False}
        
        # Check tenant providers
        tenant_providers = TenantEmailProvider.objects.filter(
            tenant_id=tenant_id
        ).select_related('provider')
        
        info['tenant_providers'] = {
            'count': tenant_providers.count(),
            'enabled_count': tenant_providers.filter(is_enabled=True).count(),
            'primary_count': tenant_providers.filter(is_primary=True).count(),
        }
        
        if tenant_providers.count() == 0:
            warnings.append("No TenantEmailProvider configured, will fallback to global")
        
        primary_providers = tenant_providers.filter(is_primary=True)
        if primary_providers.count() > 1:
            issues.append(f"Multiple primary providers found: {primary_providers.count()}")
        elif primary_providers.count() == 0 and tenant_providers.count() > 0:
            warnings.append("No primary provider set among configured providers")
        
        # Check for inactive global providers being used
        for tp in tenant_providers.filter(is_enabled=True):
            if not tp.provider.activated_by_root or not tp.provider.activated_by_tmd:
                issues.append(f"Tenant provider '{tp.provider.name}' is enabled but global provider is not activated")
        
        # Check global default provider exists
        default_provider = EmailProvider.objects.filter(
            is_default=True,
            activated_by_root=True,
            activated_by_tmd=True
        ).first()
        if not default_provider:
            issues.append("No global default provider configured (required for fallback)")
        else:
            info['global_default_provider'] = default_provider.name
        
        return {
            'tenant_id': str(tenant_id),
            'is_valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'info': info,
        }
    
    @staticmethod
    def validate_all_configurations() -> List[Dict]:
        """
        Validate all tenant configurations in the system.
        
        Returns:
            List of validation results for each tenant
        """
        from ..models import TenantEmailConfiguration
        
        results = []
        
        # Validate each tenant
        for tenant_config in TenantEmailConfiguration.objects.all():
            result = ConfigurationValidator.validate_tenant_configuration(
                tenant_config.tenant_id
            )
            results.append(result)
        
        return results
    
    @staticmethod
    def find_orphaned_configurations() -> Dict:
        """
        Find configurations that are orphaned or inconsistent.
        
        Returns:
            Dict with lists of orphaned entities
        """
        from ..models import (
            TenantEmailProvider,
            TenantEmailConfiguration, EmailProvider
        )
        
        orphaned = {
            'tenant_providers_with_inactive_global': [],
            'duplicate_primary_providers': [],
            'inactive_default_providers': [],
        }
        
        # Find tenant providers with inactive global providers
        for tp in TenantEmailProvider.objects.filter(is_enabled=True):
            if not tp.provider.activated_by_root or not tp.provider.activated_by_tmd:
                orphaned['tenant_providers_with_inactive_global'].append({
                    'tenant_id': str(tp.tenant_id),
                    'provider_name': tp.provider.name,
                })
        
        # Find tenants with multiple primary providers
        from django.db.models import Count
        duplicates = TenantEmailProvider.objects.filter(
            is_primary=True
        ).values('tenant_id').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        for dup in duplicates:
            orphaned['duplicate_primary_providers'].append({
                'tenant_id': str(dup['tenant_id']),
                'count': dup['count'],
            })
        
        # Find inactive default providers
        inactive_defaults = EmailProvider.objects.filter(
            is_default=True
        ).exclude(
            activated_by_root=True,
            activated_by_tmd=True
        )
        for provider in inactive_defaults:
            orphaned['inactive_default_providers'].append({
                'provider_name': provider.name,
                'provider_type': provider.provider_type,
            })
        
        return orphaned


class ConfigurationSync:
    """Synchronize configurations between global and tenant levels."""
    
    @staticmethod
    def sync_tenant_from_global(tenant_id: str, global_provider_id: str = None) -> Tuple[bool, str]:
        """
        Sync tenant configuration from global provider settings.
        
        Args:
            tenant_id: Tenant UUID
            global_provider_id: Optional specific provider to sync from
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        from ..models import EmailProvider, TenantEmailProvider, TenantEmailConfiguration
        
        try:
            # Get or create tenant email configuration
            tenant_config, created = TenantEmailConfiguration.objects.get_or_create(
                tenant_id=tenant_id,
                defaults={
                    'plan_type': 'FREE',
                    'emails_per_day': 100,
                    'emails_per_month': 1000,
                    'emails_per_minute': 10,
                    'activated_by_tmd': True
                }
            )
            
            # Get global provider to sync from
            if global_provider_id:
                global_provider = EmailProvider.objects.get(id=global_provider_id)
            else:
                global_provider = EmailProvider.objects.filter(
                    is_default=True,
                    activated_by_root=True,
                    activated_by_tmd=True
                ).first()
            
            if not global_provider:
                return False, "No global provider found to sync from"
            
            # Get or create tenant provider binding
            tenant_provider, tp_created = TenantEmailProvider.objects.get_or_create(
                tenant_id=tenant_id,
                provider=global_provider,
                defaults={
                    'is_enabled': True,
                    'is_primary': True,
                }
            )
            
            # Ensure rate limits in tenant config don't exceed provider limits
            tenant_config.emails_per_minute = min(
                tenant_config.emails_per_minute,
                global_provider.max_emails_per_minute
            )
            tenant_config.emails_per_day = min(
                tenant_config.emails_per_day,
                global_provider.max_emails_per_day
            )
            tenant_config.save()
            
            action = "created and synced" if created or tp_created else "synced"
            return True, f"Tenant configuration {action} from global provider '{global_provider.name}'"
            
        except Exception as e:
            logger.error(f"Failed to sync tenant {tenant_id}: {e}")
            return False, f"Sync failed: {str(e)}"
