# Generated by Django 5.0.6 on 2024-09-23 07:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0026_alter_user_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='flat',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]