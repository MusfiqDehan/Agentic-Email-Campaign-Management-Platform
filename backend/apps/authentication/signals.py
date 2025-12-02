"""
Django signals for authentication app.

Handles organization onboarding and related setup tasks.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import Organization


@receiver(post_save, sender=Organization)
def on_organization_created(sender, instance, created, **kwargs):
    """
    Signal handler for new organization creation.
    
    Sets up:
    - OrganizationEmailConfiguration with FREE plan defaults
    - Links shared email providers to the organization (optional)
    """
    if not created:
        return
    
    # Import here to avoid circular imports
    try:
        from campaigns.models import (
            OrganizationEmailConfiguration,
            EmailProvider,
            OrganizationEmailProvider,
        )
        
        # Create default email configuration
        OrganizationEmailConfiguration.objects.get_or_create(
            organization=instance,
            defaults={
                'plan_type': 'FREE',
                'timezone': 'UTC',
            }
        )
        
        # Optionally link shared providers to the new organization
        # This makes shared providers available to the organization
        if getattr(settings, 'AUTO_LINK_SHARED_PROVIDERS', True):
            shared_providers = EmailProvider.objects.filter(
                is_shared=True,
                is_active=True,
                is_deleted=False
            )
            
            for provider in shared_providers:
                OrganizationEmailProvider.objects.get_or_create(
                    organization=instance,
                    provider=provider,
                    defaults={
                        'is_enabled': True,
                        'is_primary': provider.is_default,
                    }
                )
    
    except ImportError:
        # campaigns app may not be installed in all environments
        pass
    except Exception as e:
        # Log error but don't fail organization creation
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to setup email config for org {instance.id}: {e}")
