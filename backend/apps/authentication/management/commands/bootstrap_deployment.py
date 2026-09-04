"""
One-shot deployment bootstrap: superuser, platform admin, and org assignment.

Runs in a single Django process to avoid repeated cold-start overhead during
container entrypoint (each manage.py invocation adds ~30-60s on modest hosts).
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Bootstrap admin user, platform admin flag, and org membership'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin')
        parser.add_argument('--email', default='admin@example.com')
        parser.add_argument('--password', default='changeme')
        parser.add_argument('--first-name', default='Admin')
        parser.add_argument('--last-name', default='User')

    def handle(self, *args, **options):
        call_command(
            'create_superuser',
            username=options['username'],
            email=options['email'],
            password=options['password'],
            first_name=options['first_name'],
            last_name=options['last_name'],
        )
        call_command(
            'create_platform_admin',
            options['email'],
            staff=True,
        )
        call_command('create_user_organizations')
