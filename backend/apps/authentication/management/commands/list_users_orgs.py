"""
Management command to list all users and their organizations.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.authentication.models import Organization, OrganizationMembership

User = get_user_model()


class Command(BaseCommand):
    help = 'List all users and their organization status'

    def handle(self, *args, **options):
        users = User.objects.all()
        
        self.stdout.write(self.style.SUCCESS('\n=== Users ==='))
        for user in users:
            self.stdout.write(f'\nEmail: {user.email}')
            self.stdout.write(f'  Username: {user.username}')
            self.stdout.write(f'  Is Active: {user.is_active}')
            self.stdout.write(f'  Organization: {user.organization.name if user.organization else "None"}')
            
            # Check owned organizations
            owned = user.owned_organizations.all()
            if owned:
                self.stdout.write(f'  Owns: {", ".join([o.name for o in owned])}')
            
            # Check memberships
            memberships = user.memberships.all()
            if memberships:
                for m in memberships:
                    self.stdout.write(f'  Member of: {m.organization.name} (role: {m.role}, active: {m.is_active})')
        
        self.stdout.write(self.style.SUCCESS('\n\n=== Organizations ==='))
        orgs = Organization.objects.all()
        for org in orgs:
            self.stdout.write(f'\n{org.name} (slug: {org.slug})')
            self.stdout.write(f'  Owner: {org.owner.email}')
            members = org.memberships.filter(is_active=True)
            self.stdout.write(f'  Members: {members.count()}')
