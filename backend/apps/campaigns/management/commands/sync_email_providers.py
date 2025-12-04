"""
Management command to sync email providers with service integration system.

This command ensures all EmailProviders are properly registered in the
ServiceDefinition system for consistent microservice architecture.
"""

from django.core.management.base import BaseCommand
# from automation_rule.models.service_integration_bridge import sync_email_providers_with_service_integration
# Legacy module - service_integration_bridge no longer exists


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
        
        self.stdout.write("Email provider synchronization command (legacy - not implemented)...")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))
        
        self.stdout.write(
            self.style.WARNING(
                "This command references a deprecated service_integration_bridge module. "
                "Email provider synchronization should be refactored with new architecture."
            )
        )