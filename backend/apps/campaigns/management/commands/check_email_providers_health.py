"""
Management command to perform health checks on all email providers.
Usage: python manage.py check_email_providers_health
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from automation_rule.models import EmailProvider
from automation_rule.utils.email_providers import EmailProviderFactory
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Perform health checks on all email providers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--provider-id',
            type=str,
            help='Check specific provider by ID'
        )
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Only check active providers'
        )
        parser.add_argument(
            '--update-status',
            action='store_true',
            default=True,
            help='Update provider health status (default: True)'
        )

    def handle(self, *args, **options):
        provider_id = options.get('provider_id')
        active_only = options.get('active_only')
        update_status = options.get('update_status')
        
        # Get providers to check
        if provider_id:
            providers = EmailProvider.objects.filter(id=provider_id)
            if not providers.exists():
                self.stdout.write(
                    self.style.ERROR(f'Provider with ID {provider_id} not found')
                )
                return
        else:
            providers = EmailProvider.objects.all()
            if active_only:
                providers = providers.filter(is_active=True)
        
        self.stdout.write(f'Checking health of {providers.count()} provider(s)...\n')
        
        healthy_count = 0
        unhealthy_count = 0
        error_count = 0
        
        for provider in providers:
            self.stdout.write(f'Checking: {provider.name} ({provider.provider_type})')
            
            try:
                # Decrypt config and create provider instance
                config = provider.decrypt_config()
                provider_instance = EmailProviderFactory.create_provider(
                    provider.provider_type, config
                )
                
                # Perform health check
                is_healthy, message = provider_instance.health_check()
                
                # Update status if requested
                if update_status:
                    provider.health_status = 'HEALTHY' if is_healthy else 'UNHEALTHY'
                    provider.health_details = message
                    provider.last_health_check = timezone.now()
                    provider.save()
                
                # Display results
                status_color = self.style.SUCCESS if is_healthy else self.style.WARNING
                self.stdout.write(
                    f'  Status: {status_color(provider.health_status)}'
                )
                self.stdout.write(f'  Message: {message}')
                
                if is_healthy:
                    healthy_count += 1
                else:
                    unhealthy_count += 1
                    
            except Exception as e:
                # Handle errors
                error_message = f"Health check failed: {str(e)}"
                
                if update_status:
                    provider.health_status = 'UNHEALTHY'
                    provider.health_details = error_message
                    provider.last_health_check = timezone.now()
                    provider.save()
                
                self.stdout.write(
                    f'  Status: {self.style.ERROR("ERROR")}'
                )
                self.stdout.write(f'  Error: {error_message}')
                error_count += 1
                logger.error(f"Health check error for {provider.name}: {e}")
            
            self.stdout.write('')  # Empty line for readability
        
        # Summary
        self.stdout.write(self.style.SUCCESS('Health Check Summary:'))
        self.stdout.write(f'  Healthy providers: {healthy_count}')
        self.stdout.write(f'  Unhealthy providers: {unhealthy_count}')
        self.stdout.write(f'  Errors: {error_count}')
        
        if update_status:
            self.stdout.write('\n✅ Provider health statuses have been updated')
        else:
            self.stdout.write('\n⚠️  Health statuses were NOT updated (use --update-status)')
            
        # Recommendations
        if unhealthy_count > 0 or error_count > 0:
            self.stdout.write('\n' + self.style.WARNING('Recommendations:'))
            self.stdout.write('1. Check provider configurations')
            self.stdout.write('2. Verify network connectivity')
            self.stdout.write('3. Check authentication credentials')
            self.stdout.write('4. Review provider documentation')
            
        self.stdout.write(f'\nCompleted health check at {timezone.now()}')