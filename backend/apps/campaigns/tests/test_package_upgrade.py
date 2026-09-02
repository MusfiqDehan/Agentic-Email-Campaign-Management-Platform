"""
Self-service package catalog / upgrade, and race-safe usage counters /
campaign status transitions.
"""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.authentication.models import Organization, OrganizationMembership
from apps.campaigns.models import Campaign, OrganizationEmailConfiguration, Package
from apps.campaigns.services.package_service import (
    assign_package,
    build_catalog,
    is_starter_plan,
    upgrade_organization,
)

User = get_user_model()


def make_org(name, email=None, role='owner'):
    email = email or f'owner@{name.lower()}.test'
    owner = User.objects.create_user(username=email, email=email, password='x')
    org = Organization.objects.create(name=name, slug=name.lower(), owner=owner)
    owner.organization = org
    owner.save(update_fields=['organization'])
    OrganizationMembership.objects.create(user=owner, organization=org, role=role)
    return org, owner


def make_package(name, sort_order, **kwargs):
    defaults = {
        'display_name': name.title(),
        'sort_order': sort_order,
        'is_default': False,
        'emails_per_day': 100 * (sort_order + 1),
        'emails_per_month': 1000 * (sort_order + 1),
        'contacts_limit': 500 * (sort_order + 1),
        'campaigns_per_month': 5 * (sort_order + 1),
    }
    defaults.update(kwargs)
    package, _ = Package.objects.get_or_create(name=name, defaults=defaults)
    return package


class PackageUpgradeLogicTests(TestCase):
    def setUp(self):
        self.free = make_package('free', 0)
        self.trial = make_package('trial', 0)
        self.basic = make_package('basic', 1)
        self.pro = make_package('professional', 2)
        self.ent = make_package('enterprise', 3)
        self.org, self.owner = make_org('Acme')
        self.config = OrganizationEmailConfiguration.objects.create(
            organization=self.org, package=self.free
        )

    def test_starter_detection(self):
        self.assertTrue(is_starter_plan(package=self.free))
        self.assertTrue(is_starter_plan(package=self.trial))
        self.assertFalse(is_starter_plan(package=self.basic))
        self.assertTrue(is_starter_plan(plan_type='TRIAL'))
        self.assertFalse(is_starter_plan(plan_type='PROFESSIONAL'))
        self.assertTrue(self.config.is_starter_plan)

    def test_catalog_for_free_lists_higher_tiers_only(self):
        catalog = build_catalog(self.org)
        self.assertTrue(catalog['can_upgrade'])
        names = [p.name for p in catalog['available_upgrades']]
        self.assertEqual(names, ['basic', 'professional', 'enterprise'])
        self.assertNotIn('free', names)
        self.assertNotIn('trial', names)

    def test_catalog_for_paid_plan_hides_upgrades(self):
        self.config.package = self.pro
        self.config.save()
        catalog = build_catalog(self.org)
        self.assertFalse(catalog['is_starter'])
        self.assertFalse(catalog['can_upgrade'])
        self.assertEqual(catalog['available_upgrades'], [])

    def test_trial_org_can_upgrade(self):
        self.config.package = self.trial
        self.config.save()
        catalog = build_catalog(self.org)
        self.assertTrue(catalog['can_upgrade'])
        names = [p.name for p in catalog['available_upgrades']]
        self.assertEqual(names, ['basic', 'professional', 'enterprise'])

    def test_self_service_upgrade_assigns_package(self):
        config, changed = upgrade_organization(
            self.org, self.basic.pk, actor=self.owner
        )
        self.assertTrue(changed)
        self.assertEqual(config.package, self.basic)
        self.assertEqual(config.plan_type, 'BASIC')

    def test_self_service_upgrade_is_idempotent(self):
        upgrade_organization(self.org, self.basic.pk, actor=self.owner)
        config, changed = upgrade_organization(
            self.org, self.basic.pk, actor=self.owner
        )
        self.assertFalse(changed)
        self.assertEqual(config.package, self.basic)

    def test_self_service_rejects_downgrade_and_lateral(self):
        upgrade_organization(self.org, self.basic.pk, actor=self.owner)
        with self.assertRaises(ValidationError):
            upgrade_organization(self.org, self.free.pk, actor=self.owner)
        with self.assertRaises(ValidationError):
            upgrade_organization(self.org, self.pro.pk, actor=self.owner)

    def test_admin_assign_can_downgrade(self):
        assign_package(self.org, self.pro, actor=self.owner, allow_downgrade=True)
        config, changed = assign_package(
            self.org, self.free, actor=self.owner, allow_downgrade=True
        )
        self.assertTrue(changed)
        self.assertEqual(config.package, self.free)

    def test_inactive_package_cannot_be_assigned(self):
        self.basic.is_active = False
        self.basic.save(update_fields=['is_active'])
        with self.assertRaises(ValidationError):
            upgrade_organization(self.org, self.basic.pk, actor=self.owner)


class PackageCatalogApiTests(TestCase):
    def setUp(self):
        self.free = make_package('free', 0)
        self.basic = make_package('basic', 1)
        self.pro = make_package('professional', 2)
        self.org, self.owner = make_org('Acme')
        OrganizationEmailConfiguration.objects.create(
            organization=self.org, package=self.free
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

        member_email = 'member@acme.test'
        self.member = User.objects.create_user(
            username=member_email, email=member_email, password='x'
        )
        self.member.organization = self.org
        self.member.save(update_fields=['organization'])
        OrganizationMembership.objects.create(
            user=self.member, organization=self.org, role='member'
        )

    def test_catalog_endpoint(self):
        response = self.client.get('/api/v1/campaigns/packages/catalog/')
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()['data']
        self.assertTrue(data['can_upgrade'])
        self.assertTrue(data['is_starter'])
        self.assertEqual(data['current_package']['name'], 'free')
        self.assertEqual(
            [p['name'] for p in data['available_upgrades']],
            ['basic', 'professional', 'enterprise'],
        )

    def test_member_can_read_catalog_but_not_upgrade(self):
        client = APIClient()
        client.force_authenticate(user=self.member)
        response = client.get('/api/v1/campaigns/packages/catalog/')
        self.assertEqual(response.status_code, 200)
        response = client.post(
            '/api/v1/campaigns/packages/upgrade/',
            {'package_id': str(self.basic.pk)},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_upgrade_endpoint(self):
        response = self.client.post(
            '/api/v1/campaigns/packages/upgrade/',
            {'package_id': str(self.basic.pk)},
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()['data']
        self.assertTrue(data['changed'])
        self.assertEqual(data['current_package']['name'], 'basic')
        self.assertFalse(data['can_upgrade'])
        self.assertFalse(data['is_starter'])

    def test_paid_org_cannot_self_upgrade(self):
        assign_package(self.org, self.pro, actor=self.owner)
        response = self.client.post(
            '/api/v1/campaigns/packages/upgrade/',
            {'package_id': str(self.basic.pk)},
            format='json',
        )
        self.assertEqual(response.status_code, 400)


class UsageCounterRaceTests(TestCase):
    def setUp(self):
        self.org, self.owner = make_org('Acme')
        self.config = OrganizationEmailConfiguration.objects.create(
            organization=self.org,
            emails_per_day=100,
            emails_per_month=1000,
        )

    def test_increment_by_count(self):
        self.config.increment_email_usage(count=3)
        self.config.refresh_from_db()
        self.assertEqual(self.config.emails_sent_today, 3)
        self.assertEqual(self.config.emails_sent_this_month, 3)

    def test_period_reset_then_increment_does_not_keep_stale_count(self):
        yesterday = timezone.now().date() - timedelta(days=1)
        type(self.config).objects.filter(pk=self.config.pk).update(
            emails_sent_today=50,
            emails_sent_this_month=50,
            last_daily_reset=yesterday,
            last_monthly_reset=yesterday.replace(day=1) - timedelta(days=1),
        )
        self.config.refresh_from_db()
        self.config.increment_email_usage()
        self.config.refresh_from_db()
        self.assertEqual(self.config.emails_sent_today, 1)
        self.assertEqual(self.config.emails_sent_this_month, 1)
        self.assertEqual(self.config.last_daily_reset, timezone.now().date())


class CampaignLaunchRaceTests(TestCase):
    def setUp(self):
        self.org, self.owner = make_org('Acme')
        self.campaign = Campaign.objects.create(
            organization=self.org,
            name='Launch once',
            status='DRAFT',
        )

    @patch('apps.campaigns.tasks.launch_campaign_task.delay')
    def test_second_launch_is_rejected(self, _delay):
        self.campaign.launch()
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.status, 'SENDING')
        _delay.assert_called_once()
        with self.assertRaises(ValidationError):
            self.campaign.launch()
        self.assertEqual(_delay.call_count, 1)
