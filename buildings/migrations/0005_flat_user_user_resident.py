# Generated by Django 5.0.6 on 2024-08-19 12:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0004_remove_user_balance_flat_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='flat',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='user',
            name='resident',
            field=models.BooleanField(default=False),
        ),
    ]
