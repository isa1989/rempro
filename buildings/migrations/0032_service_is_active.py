# Generated by Django 5.0.6 on 2024-09-25 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0031_alter_user_phone_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='aktiv'),
        ),
    ]
