# Generated migration - manually created to avoid circular dependencies

import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('django_celery_beat', '0019_alter_periodictasks_options'),
    ]

    operations = [
        # Core provider models - no service_integration references
        migrations.CreateModel(
            name='EmailProviderModel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('updated_by', models.UUIDField(blank=True, null=True)),
                ('activated_by_td', models.BooleanField(default=False)),
                ('activated_by_tmd', models.BooleanField(default=False)),
                ('activated_by_root', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('provider_name', models.CharField(max_length=100, unique=True)),
                ('provider_type', models.CharField(choices=[('SES', 'Amazon SES'), ('SENDGRID', 'SendGrid'), ('MAILGUN', 'Mailgun'), ('SMTP', 'SMTP')], default='SES', max_length=20)),
                ('is_shared', models.BooleanField(default=False, help_text='Is this a shared/global provider?')),
                ('organization_id', models.UUIDField(blank=True, null=True, help_text='Tenant ID if not shared')),
                ('access_key_id', models.CharField(blank=True, max_length=255)),
                ('secret_access_key', models.CharField(blank=True, max_length=255)),
                ('region', models.CharField(blank=True, default='us-east-1', max_length=50)),
                ('from_email', models.EmailField(blank=True, max_length=254)),
                ('from_name', models.CharField(blank=True, max_length=255)),
                ('reply_to_email', models.EmailField(blank=True, max_length=254)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Email Provider',
                'verbose_name_plural': 'Email Providers',
            },
        ),
        # Email configuration
        migrations.CreateModel(
            name='TenantEmailProviderModel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('updated_by', models.UUIDField(blank=True, null=True)),
                ('activated_by_td', models.BooleanField(default=False)),
                ('activated_by_tmd', models.BooleanField(default=False)),
                ('activated_by_root', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('organization_id', models.UUIDField(db_index=True)),
                ('is_active', models.BooleanField(default=True)),
                ('daily_limit', models.PositiveIntegerField(default=10000)),
                ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tenant_configs', to='campaigns.emailprovidermodel')),
            ],
            options={
                'verbose_name': 'Tenant Email Provider',
                'verbose_name_plural': 'Tenant Email Providers',
            },
        ),
        # SMS configuration
        migrations.CreateModel(
            name='SMSConfigurationModel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('updated_by', models.UUIDField(blank=True, null=True)),
                ('activated_by_td', models.BooleanField(default=False)),
                ('activated_by_tmd', models.BooleanField(default=False)),
                ('activated_by_root', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('name_or_type', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('organization_id', models.UUIDField(blank=True, null=True)),
                ('endpoint_url', models.CharField(blank=True, max_length=255, null=True)),
                ('account_ssid', models.CharField(blank=True, max_length=255, null=True)),
                ('auth_token', models.CharField(blank=True, max_length=255, null=True)),
                ('default_from_number', models.CharField(blank=True, max_length=20, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'SMS Configuration',
                'verbose_name_plural': 'SMS Configurations',
            },
        ),
        # Email templates
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('updated_by', models.UUIDField(blank=True, null=True)),
                ('activated_by_td', models.BooleanField(default=False)),
                ('activated_by_tmd', models.BooleanField(default=False)),
                ('activated_by_root', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('template_name', models.CharField(max_length=255)),
                ('organization_id', models.UUIDField(blank=True, null=True)),
                ('template_type', models.CharField(choices=[('TENANT', 'Tenant Specific'), ('GLOBAL', 'Global Organization')], default='TENANT', max_length=100)),
                ('category', models.CharField(default='OTHER', max_length=100)),
                ('email_subject', models.CharField(max_length=255)),
                ('email_body', models.TextField()),
            ],
            options={
                'verbose_name': 'Email Template',
                'verbose_name_plural': 'Email Templates',
            },
        ),
        # Email queue for batch processing
        migrations.CreateModel(
            name='EmailQueueModel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('updated_by', models.UUIDField(blank=True, null=True)),
                ('activated_by_td', models.BooleanField(default=False)),
                ('activated_by_tmd', models.BooleanField(default=False)),
                ('activated_by_root', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('organization_id', models.UUIDField(blank=True, null=True)),
                ('recipient_email', models.EmailField(db_index=True, max_length=254)),
                ('subject', models.CharField(max_length=255)),
                ('html_content', models.TextField()),
                ('text_content', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('SENT', 'Sent'), ('FAILED', 'Failed')], db_index=True, default='PENDING', max_length=20)),
                ('scheduled_at', models.DateTimeField(db_index=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('retry_count', models.PositiveIntegerField(default=0)),
                ('error_message', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Email Queue Item',
                'verbose_name_plural': 'Email Queue',
            },
        ),
        # Email delivery log for tracking
        migrations.CreateModel(
            name='EmailDeliveryLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('updated_by', models.UUIDField(blank=True, null=True)),
                ('activated_by_td', models.BooleanField(default=False)),
                ('activated_by_tmd', models.BooleanField(default=False)),
                ('activated_by_root', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('organization_id', models.UUIDField(blank=True, null=True)),
                ('recipient_email', models.EmailField(db_index=True, max_length=254)),
                ('subject', models.CharField(max_length=255, blank=True)),
                ('delivery_status', models.CharField(choices=[('PENDING', 'Pending'), ('SENT', 'Sent'), ('FAILED', 'Failed'), ('BOUNCED', 'Bounced')], default='PENDING', max_length=20, db_index=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True, db_index=True)),
                ('provider', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='campaigns.emailprovidermodel')),
            ],
            options={
                'verbose_name': 'Email Delivery Log',
                'verbose_name_plural': 'Email Delivery Logs',
            },
        ),
        # SMS logs
        migrations.CreateModel(
            name='SMSLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.UUIDField(blank=True, null=True)),
                ('updated_by', models.UUIDField(blank=True, null=True)),
                ('activated_by_td', models.BooleanField(default=False)),
                ('activated_by_tmd', models.BooleanField(default=False)),
                ('activated_by_root', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('organization_id', models.UUIDField(blank=True, null=True)),
                ('phone_number', models.CharField(db_index=True, max_length=20)),
                ('message', models.TextField()),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('SENT', 'Sent'), ('FAILED', 'Failed')], default='PENDING', max_length=20)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('provider', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='campaigns.smsconfigurationmodel')),
            ],
            options={
                'verbose_name': 'SMS Log',
                'verbose_name_plural': 'SMS Logs',
            },
        ),
    ]
