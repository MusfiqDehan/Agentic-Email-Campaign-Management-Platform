"""
Management command to create organizations for users without them.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from apps.authentication.models import Organization, OrganizationMembership

User = get_user_model()


class Command(BaseCommand):
    help = 'Create organizations for users without them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Specific user email to create organization for (optional)',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        
        if email:
            try:
                user = User.objects.get(email=email)
                self.create_org_for_user(user)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
        else:
            # Find all users without organization
            users_without_org = User.objects.filter(organization__isnull=True)
            
            for user in users_without_org:
                self.create_org_for_user(user)
    
    def create_org_for_user(self, user):
        """Create organization and membership for a user."""
        # Generate organization name from username or email
        org_name = f"{user.username.title()}'s Organization"
        
        # Create unique slug
        base_slug = slugify(org_name)
        slug = base_slug
        i = 1
        while Organization.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{i}"
            i += 1
        
        # Create organization
        org = Organization.objects.create(
            name=org_name,
            slug=slug,
            owner=user
        )
        
        # Create membership
        OrganizationMembership.objects.create(
            user=user,
            organization=org,
            role='owner',
            is_active=True
        )
        
        # Assign organization to user
        user.organization = org
        user.save(update_fields=['organization'])
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Created organization "{org.name}" for {user.email} and assigned as owner'
            )
        )
