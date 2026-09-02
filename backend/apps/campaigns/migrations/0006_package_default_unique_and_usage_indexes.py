from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campaigns', '0005_seed_packages_and_migrate_domains'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='package',
            constraint=models.UniqueConstraint(
                condition=models.Q(('is_default', True), ('is_deleted', False)),
                fields=('is_default',),
                name='uniq_one_default_active_package',
            ),
        ),
    ]
