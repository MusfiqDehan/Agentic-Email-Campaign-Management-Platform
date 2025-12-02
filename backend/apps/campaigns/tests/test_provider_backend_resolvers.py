from django.test import SimpleTestCase

from ..backends import ProviderBackendResolver


class ProviderBackendResolverTests(SimpleTestCase):
	def test_resolve_aws_ses_backend_builds_expected_kwargs(self):
		config = {
			"aws_access_key_id": "AKIA-test",
			"aws_secret_access_key": "secret",
			"region_name": "us-east-1",
			"from_email": "noreply@example.com",
			"return_path": "bounce@example.com",
			"use_ses_v2": True,
			"aws_auto_throttle": 1,
		}

		with self.settings(AWS_SES_FROM_EMAIL=None, AWS_SES_RETURN_PATH=None):
			backend_path, kwargs, metadata = ProviderBackendResolver.resolve("AWS_SES", config)

		self.assertEqual(backend_path, "django_ses.SESBackend")
		self.assertEqual(kwargs["aws_access_key"], "AKIA-test")
		self.assertEqual(kwargs["aws_secret_key"], "secret")
		self.assertEqual(kwargs["aws_region_name"], "us-east-1")
		self.assertTrue(kwargs["use_ses_v2"])
		self.assertEqual(metadata["from_email"], "noreply@example.com")

	def test_resolve_aws_ses_missing_values_raises_value_error(self):
		with self.assertRaises(ValueError):
			ProviderBackendResolver.resolve("AWS_SES", {})
