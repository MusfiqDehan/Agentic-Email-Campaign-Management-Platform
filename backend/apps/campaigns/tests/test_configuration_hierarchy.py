import json

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.authentication.models import Organization
from ..models import EmailProvider, OrganizationEmailProvider
from ..utils.sync_utils import ConfigurationHierarchy

User = get_user_model()


def make_organization(name='Acme'):
    email = f'owner@{name.lower()}.test'
    owner = User.objects.create_user(username=email, email=email, password='x')
    return Organization.objects.create(name=name, slug=name.lower(), owner=owner)


class ConfigurationHierarchyFallbackTests(TestCase):
    def test_shared_default_provider_is_used_when_no_provider_selected(self):
        default_provider = EmailProvider.objects.create(
            name="Default SES",
            provider_type="AWS_SES",
            encrypted_config=json.dumps({"from_email": "noreply@example.com"}),
            is_default=True,
            is_shared=True,
        )

        # An organization-owned default must not win the shared fallback
        organization = make_organization('Acme')
        EmailProvider.objects.create(
            name="Org Specific",
            provider_type="AWS_SES",
            organization=organization,
            encrypted_config=json.dumps({"from_email": "org@example.com"}),
            is_default=True,
        )

        provider, org_provider, config = ConfigurationHierarchy.get_effective_provider()

        self.assertEqual(provider, default_provider)
        self.assertIsNone(org_provider)
        self.assertEqual(config.get("from_email"), "noreply@example.com")

    def test_fallback_to_highest_priority_when_no_default_provider(self):
        fallback_provider = EmailProvider.objects.create(
            name="Fallback SES",
            provider_type="AWS_SES",
            encrypted_config=json.dumps({"from_email": "fallback@example.com"}),
            is_shared=True,
            priority=2,
        )

        # An organization-owned provider must not be selected as shared fallback
        organization = make_organization('Rival')
        EmailProvider.objects.create(
            name="Org Scoped",
            provider_type="AWS_SES",
            organization=organization,
            encrypted_config=json.dumps({"from_email": "org@example.com"}),
            priority=1,
        )

        provider, org_provider, config = ConfigurationHierarchy.get_effective_provider()

        self.assertEqual(provider, fallback_provider)
        self.assertIsNone(org_provider)
        self.assertEqual(config.get("from_email"), "fallback@example.com")

    def test_organization_primary_provider_wins_over_shared_default(self):
        EmailProvider.objects.create(
            name="Shared Default",
            provider_type="AWS_SES",
            encrypted_config=json.dumps({"from_email": "shared@example.com"}),
            is_default=True,
            is_shared=True,
        )

        organization = make_organization('Acme')
        org_owned = EmailProvider.objects.create(
            name="Org Primary",
            provider_type="AWS_SES",
            organization=organization,
            encrypted_config=json.dumps({"from_email": "primary@example.com"}),
        )
        OrganizationEmailProvider.objects.create(
            organization=organization,
            provider=org_owned,
            is_enabled=True,
            is_primary=True,
        )

        provider, org_provider, config = ConfigurationHierarchy.get_effective_provider(
            organization_id=organization.id
        )

        self.assertEqual(provider, org_owned)
        self.assertIsNotNone(org_provider)
        self.assertEqual(config.get("from_email"), "primary@example.com")

    def test_preferred_provider_id_takes_highest_precedence(self):
        EmailProvider.objects.create(
            name="Shared Default",
            provider_type="AWS_SES",
            encrypted_config=json.dumps({"from_email": "shared@example.com"}),
            is_default=True,
            is_shared=True,
        )
        preferred = EmailProvider.objects.create(
            name="Preferred",
            provider_type="AWS_SES",
            encrypted_config=json.dumps({"from_email": "preferred@example.com"}),
            is_shared=True,
        )

        provider, _, config = ConfigurationHierarchy.get_effective_provider(
            preferred_provider_id=str(preferred.id)
        )

        self.assertEqual(provider, preferred)
        self.assertEqual(config.get("from_email"), "preferred@example.com")

    def test_returns_none_when_no_provider_configured(self):
        provider, org_provider, config = ConfigurationHierarchy.get_effective_provider()

        self.assertIsNone(provider)
        self.assertIsNone(org_provider)
        self.assertEqual(config, {})
