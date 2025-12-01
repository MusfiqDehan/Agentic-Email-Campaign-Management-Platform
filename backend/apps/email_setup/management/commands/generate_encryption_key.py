"""
Management command to generate a proper Fernet encryption key for email configurations.
Run this command to generate a secure encryption key for production use.
"""

from django.core.management.base import BaseCommand
from cryptography.fernet import Fernet


class Command(BaseCommand):
    help = 'Generate a secure Fernet encryption key for email configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--show-env-var',
            action='store_true',
            help='Show as environment variable format'
        )

    def handle(self, *args, **options):
        # Generate a new Fernet key
        key = Fernet.generate_key()
        key_string = key.decode()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully generated encryption key!')
        )
        
        if options['show_env_var']:
            self.stdout.write('\nAdd this to your environment variables:')
            self.stdout.write(f'EMAIL_CONFIG_ENCRYPTION_KEY={key_string}')
        else:
            self.stdout.write('\nGenerated key:')
            self.stdout.write(key_string)
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('IMPORTANT SECURITY NOTES:')
        self.stdout.write('='*60)
        self.stdout.write('1. Store this key securely in your environment variables')
        self.stdout.write('2. Never commit this key to version control')
        self.stdout.write('3. Use the same key across all instances of your application')
        self.stdout.write('4. If you lose this key, encrypted data cannot be recovered')
        self.stdout.write('5. Add EMAIL_CONFIG_ENCRYPTION_KEY to your Django settings')
        
        # Show example Django settings
        self.stdout.write('\nExample Django settings.py:')
        self.stdout.write('import os')
        self.stdout.write('EMAIL_CONFIG_ENCRYPTION_KEY = os.environ.get("EMAIL_CONFIG_ENCRYPTION_KEY")')