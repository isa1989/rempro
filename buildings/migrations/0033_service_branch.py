# Generated by Django 5.0.6 on 2024-09-25 11:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0032_service_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='branch',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='service', to='buildings.branch'),
            preserve_default=False,
        ),
    ]
