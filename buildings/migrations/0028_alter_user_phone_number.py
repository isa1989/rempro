# Generated by Django 5.0.6 on 2024-09-24 13:13

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0027_flat_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, max_length=13, null=True, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+994709021220'.", regex='^\\+994\\d{9}$')]),
        ),
    ]
