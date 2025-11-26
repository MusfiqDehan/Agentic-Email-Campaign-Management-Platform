"""
Django management command to create a superuser for the Email Campaign Management Platform.
This command creates a superuser with predefined credentials for easy development setup.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError


User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser for the Email Campaign Management Platform'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for the superuser (default: admin)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@emailcampaign.com',
            help='Email for the superuser (default: admin@emailcampaign.com)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Password for the superuser (default: admin123)'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='Admin',
            help='First name for the superuser (default: Admin)'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='User',
            help='Last name for the superuser (default: User)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force create superuser even if one already exists with the same username'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        force = options['force']

        self.stdout.write(
            self.style.HTTP_INFO(f'Creating superuser with username: {username}')
        )

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            if not force:
                self.stdout.write(
                    self.style.WARNING(
                        f'User with username "{username}" already exists. '
                        'Use --force to replace the existing user.'
                    )
                )
                return
            else:
                # Delete existing user
                User.objects.filter(username=username).delete()
                self.stdout.write(
                    self.style.WARNING(f'Deleted existing user with username "{username}"')
                )

        try:
            # Create the superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                gender='Other',  # Default gender
                occupation='Administrator',
                country='Unknown',
                city='Unknown',
                address='Unknown',
                phone_number='+1234567890'
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created superuser "{username}" with email "{email}"'
                )
            )
            
            self.stdout.write(
                self.style.HTTP_INFO('\n' + '='*50)
            )
            self.stdout.write(
                self.style.HTTP_INFO('SUPERUSER CREDENTIALS')
            )
            self.stdout.write(
                self.style.HTTP_INFO('='*50)
            )
            self.stdout.write(f'Username: {username}')
            self.stdout.write(f'Email: {email}')
            self.stdout.write(f'Password: {password}')
            self.stdout.write(f'Admin URL: http://localhost:28000/admin/')
            self.stdout.write(
                self.style.HTTP_INFO('='*50 + '\n')
            )
            
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error creating superuser: {str(e)}'
                )
            )
        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Validation error: {str(e)}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Unexpected error creating superuser: {str(e)}'
                )
            )