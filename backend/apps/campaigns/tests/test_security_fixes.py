"""
Regression tests for the security fixes shipped with the sending-domains
feature: signup privilege escalation, throttle imports, the fake
verify-domain stub, admin provider endpoint permissions, and org-config
serializer field lockdown.
"""
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.authentication.models import Organization, OrganizationMembership
from apps.authentication.serializers import SignupSerializer
from apps.campaigns.models import OrganizationEmailConfiguration

User = get_user_model()


def make_org(name='Acme', email='owner@acme.test'):
    owner = User.objects.create_user(username=email, email=email, password='x')
    org = Organization.objects.create(name=name, slug=name.lower(), owner=owner)
    owner.organization = org
    owner.save(update_fields=['organization'])
    OrganizationMembership.objects.create(user=owner, organization=org, role='owner')
    return org, owner


class SignupPrivilegeEscalationTests(TestCase):
    def test_signup_ignores_is_platform_admin(self):
        serializer = SignupSerializer(
            data={
                'email': 'evil@example.com',
                'password': 'S3cure-pass!',
                'organization_name': 'Evil Co',
                'is_platform_admin': True,
            },
            context={'email_service': MagicMock()},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertFalse(user.is_platform_admin)


class ThrottleImportTests(TestCase):
    def test_org_rate_limit_reads_config(self):
        from apps.utils.throttles import OrganizationRateThrottle

        org, owner = make_org()
        config = OrganizationEmailConfiguration.objects.create(organization=org)
        config.limit_overrides = {'api_requests_per_minute': 123}
        config.save()

        throttle = OrganizationRateThrottle()
        request = MagicMock()
        request.user = owner
        rate, duration = throttle._get_rate_limit(request)
        self.assertEqual(rate, 123)
        self.assertEqual(duration, 60)


class VerifyDomainStubTests(TestCase):
    def test_old_verify_domain_endpoint_is_gone(self):
        org, owner = make_org()
        config = OrganizationEmailConfiguration.objects.create(
            organization=org, custom_domain='spoofed.example.com'
        )
        client = APIClient()
        client.force_authenticate(user=owner)
        response = client.post(f'/api/v1/campaigns/config/{config.pk}/verify-domain/')
        self.assertEqual(response.status_code, 410)
        config.refresh_from_db()
        self.assertFalse(config.custom_domain_verified)


class AdminProviderPermissionTests(TestCase):
    def setUp(self):
        self.org, self.owner = make_org()
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

    def test_admin_provider_list_requires_platform_admin(self):
        response = self.client.get('/api/v1/campaigns/admin/providers/')
        self.assertEqual(response.status_code, 403)

    def test_admin_provider_list_allows_platform_admin(self):
        self.owner.is_platform_admin = True
        self.owner.save(update_fields=['is_platform_admin'])
        response = self.client.get('/api/v1/campaigns/admin/providers/')
        self.assertEqual(response.status_code, 200)


class ConfigSerializerLockdownTests(TestCase):
    def test_org_admin_cannot_self_upgrade_plan(self):
        org, owner = make_org()
        config = OrganizationEmailConfiguration.objects.create(organization=org)
        client = APIClient()
        client.force_authenticate(user=owner)
        response = client.patch(
            f'/api/v1/campaigns/config/{config.pk}/',
            {'plan_type': 'ENTERPRISE', 'is_suspended': False},
            format='json',
        )
        self.assertIn(response.status_code, (200, 202))
        config.refresh_from_db()
        self.assertEqual(config.plan_type, 'FREE')
