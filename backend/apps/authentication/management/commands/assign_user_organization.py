"""
Management command to assign users to their organizations.
This fixes users who don't have their organization field set.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.authentication.models import OrganizationMembership

User = get_user_model()


class Command(BaseCommand):
    help = 'Assign users to their organizations based on membership'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Specific user email to fix (optional)',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        
        if email:
            # Fix specific user
            try:
                user = User.objects.get(email=email)
                self.fix_user_organization(user)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
        else:
            # Fix all users without organization
            users_without_org = User.objects.filter(organization__isnull=True)
            count = users_without_org.count()
            
            if count == 0:
                self.stdout.write(self.style.SUCCESS('All users already have organizations assigned'))
                return
            
            self.stdout.write(f'Found {count} users without organization')
            
            for user in users_without_org:
                self.fix_user_organization(user)
    
    def fix_user_organization(self, user):
        """Fix organization for a single user."""
        # Check if user owns an organization
        owned_org = user.owned_organizations.first()
        if owned_org:
            user.organization = owned_org
            user.save(update_fields=['organization'])
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Assigned {user.email} to owned organization: {owned_org.name}'
                )
            )
            return
        
        # Check if user is a member of any organization
        membership = OrganizationMembership.objects.filter(
            user=user,
            is_active=True
        ).first()
        
        if membership:
            user.organization = membership.organization
            user.save(update_fields=['organization'])
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Assigned {user.email} to organization: {membership.organization.name} (role: {membership.role})'
                )
            )
            return
        
        self.stdout.write(
            self.style.WARNING(
                f'⚠ User {user.email} has no organization membership - skipped'
            )
        )
