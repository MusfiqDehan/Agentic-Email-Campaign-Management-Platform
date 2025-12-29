import json
import uuid

from django.test import TestCase

from ..models import EmailProvider
from ..utils.sync_utils import ConfigurationHierarchy


class ConfigurationHierarchyFallbackTests(TestCase):
    def test_global_default_provider_is_used_when_no_provider_selected(self):
        default_provider = EmailProvider.objects.create(
            name="Default SES",
            provider_type="AWS_SES",
            encrypted_config=json.dumps({"from_email": "noreply@example.com"}),
            is_default=True,
            is_global=True,
            activated_by_tmd=True,
        )

        # Add a tenant-scoped default to ensure the global fallback ignores it
        EmailProvider.objects.create(
            name="Tenant Specific",
            provider_type="AWS_SES",
            tenant_id=uuid.uuid4(),
            encrypted_config=json.dumps({"from_email": "tenant@example.com"}),
            is_default=True,
            is_global=False,
            activated_by_tmd=True,
        )

        provider, tenant_provider, config = ConfigurationHierarchy.get_effective_provider()

        self.assertEqual(provider, default_provider)
        self.assertIsNone(tenant_provider)
        self.assertIn("from_email", config)
        self.assertEqual(config.get("from_email"), "noreply@example.com")

    def test_fallback_to_highest_priority_when_no_default_provider(self):
        fallback_provider = EmailProvider.objects.create(
            name="Fallback SES",
            provider_type="AWS_SES",
            encrypted_config=json.dumps({"from_email": "fallback@example.com"}),
            is_global=True,
            activated_by_tmd=True,
            priority=2,
        )

        # Add a tenant provider to ensure it is not selected for global fallback
        EmailProvider.objects.create(
            name="Tenant Scoped",
            provider_type="AWS_SES",
            tenant_id=uuid.uuid4(),
            encrypted_config=json.dumps({"from_email": "tenant@example.com"}),
            is_global=False,
            activated_by_tmd=True,
            priority=1,
        )

        provider, tenant_provider, config = ConfigurationHierarchy.get_effective_provider()

        self.assertEqual(provider, fallback_provider)
        self.assertIsNone(tenant_provider)
        self.assertIn("from_email", config)
        self.assertEqual(config.get("from_email"), "fallback@example.com")
