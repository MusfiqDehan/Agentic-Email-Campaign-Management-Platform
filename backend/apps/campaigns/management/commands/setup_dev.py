from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Setup development data for campaigns app'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing data before setup',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        clean = options['clean']
        
        if clean:
            self.stdout.write('Cleaning existing campaigns data...')
            # Add your cleanup logic here
        
        self.stdout.write('Setting up development data for campaigns...')
        # Add your setup logic here
        
        self.stdout.write(
            self.style.SUCCESS(
                'Successfully setup development data for campaigns'
            )
        )
