"""
Management command to create or promote a user to platform admin.

Usage:
    # Promote existing user
    python manage.py create_platform_admin admin@example.com

    # Create new admin user
    python manage.py create_platform_admin admin@example.com --create --password SecurePass123!

    # Revoke platform admin
    python manage.py create_platform_admin admin@example.com --revoke
"""
from django.core.management.base import BaseCommand, CommandError
from apps.authentication.models import User


class Command(BaseCommand):
    help = 'Create or promote a user to platform admin'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='User email address'
        )
        parser.add_argument(
            '--create',
            action='store_true',
            help='Create new user if not exists'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for new user (required with --create)'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username for new user (defaults to email prefix)'
        )
        parser.add_argument(
            '--revoke',
            action='store_true',
            help='Revoke platform admin status instead of granting'
        )
        parser.add_argument(
            '--staff',
            action='store_true',
            help='Also grant Django admin (is_staff) access'
        )

    def handle(self, *args, **options):
        email = options['email'].lower().strip()
        revoke = options['revoke']
        
        try:
            user = User.objects.get(email=email)
            
            if revoke:
                user.is_platform_admin = False
                user.save(update_fields=['is_platform_admin'])
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Revoked platform admin from: {email}')
                )
            else:
                user.is_platform_admin = True
                if options['staff']:
                    user.is_staff = True
                    user.save(update_fields=['is_platform_admin', 'is_staff'])
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ User {email} is now a platform admin with Django admin access')
                    )
                else:
                    user.save(update_fields=['is_platform_admin'])
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ User {email} is now a platform admin')
                    )
                    
        except User.DoesNotExist:
            if options['create']:
                password = options.get('password')
                if not password:
                    raise CommandError('--password is required when creating a new user')
                
                username = options.get('username') or email.split('@')[0]
                
                # Check if username already exists
                if User.objects.filter(username=username).exists():
                    username = f"{username}_{User.objects.count()}"
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_platform_admin=True,
                    is_staff=options['staff'],
                    is_active=True,
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created platform admin:\n'
                        f'  Email: {email}\n'
                        f'  Username: {username}\n'
                        f'  is_platform_admin: True\n'
                        f'  is_staff: {user.is_staff}'
                    )
                )
            else:
                raise CommandError(
                    f'User with email {email} not found. '
                    f'Use --create to create a new user.'
                )
