"""
Django management command for quick development setup.
This command creates a superuser and runs initial setup tasks.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model


User = get_user_model()


class Command(BaseCommand):
    help = 'Quick development setup: Create superuser and run initial setup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-superuser',
            action='store_true',
            help='Skip superuser creation'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.HTTP_INFO('🚀 Starting development setup...\n')
        )

        # Run migrations
        self.stdout.write('📁 Applying database migrations...')
        call_command('migrate', verbosity=0)
        self.stdout.write(self.style.SUCCESS('✅ Migrations applied\n'))

        # Create superuser if not skipped
        if not options['skip_superuser']:
            self.stdout.write('👤 Creating superuser...')
            if User.objects.filter(username='admin').exists():
                self.stdout.write(
                    self.style.WARNING('⚠️  Superuser "admin" already exists\n')
                )
            else:
                call_command('create_superuser')
                self.stdout.write('')

        # Collect static files
        self.stdout.write('📦 Collecting static files...')
        try:
            call_command('collectstatic', interactive=False, verbosity=0)
            self.stdout.write(self.style.SUCCESS('✅ Static files collected\n'))
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Static files collection failed: {str(e)}\n')
            )

        self.stdout.write(
            self.style.SUCCESS('🎉 Development setup complete!')
        )
        self.stdout.write(
            self.style.HTTP_INFO('🌐 Visit http://localhost:28000/admin/ to access the admin panel')
        )