"""
Management command to sync email providers with service integration system.

This command ensures all EmailProviders are properly registered in the
ServiceDefinition system for consistent microservice architecture.
"""

from django.core.management.base import BaseCommand
from automation_rule.models.service_integration_bridge import sync_email_providers_with_service_integration


class Command(BaseCommand):
    help = 'Sync email providers with service integration system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sync even for providers that are already synced',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write("Starting email provider synchronization...")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))
        
        try:
            if not dry_run:
                result = sync_email_providers_with_service_integration()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Synchronization completed: {result['synced']} providers synced, "
                        f"{result['errors']} errors"
                    )
                )
                
                if result['errors'] > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            "Some providers had errors. Check logs for details."
                        )
                    )
            else:
                from automation_rule.models import EmailProvider
                providers = EmailProvider.objects.filter(is_active=True)
                
                self.stdout.write(f"Would sync {providers.count()} active email providers:")
                for provider in providers:
                    self.stdout.write(f"  - {provider.name} ({provider.provider_type})")
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Synchronization failed: {e}")
            )
            raise