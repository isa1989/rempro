# Generated by Django 5.0.6 on 2024-10-04 07:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0036_alter_camera_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='news',
            name='building',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='news', to='buildings.building', verbose_name='Bina'),
            preserve_default=False,
        ),
    ]
