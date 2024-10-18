# Generated by Django 5.0.6 on 2024-10-15 09:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0039_rename_garrage_garage'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='carplate',
            options={'verbose_name': 'Maşın nömrəsi', 'verbose_name_plural': 'Maşın nömrələri'},
        ),
        migrations.AlterModelOptions(
            name='garage',
            options={'verbose_name': 'Qaraj', 'verbose_name_plural': 'Qarajlar'},
        ),
        migrations.RemoveField(
            model_name='garage',
            name='owner',
        ),
        migrations.AddField(
            model_name='garage',
            name='building',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='buildings.building'),
            preserve_default=False,
        ),
    ]