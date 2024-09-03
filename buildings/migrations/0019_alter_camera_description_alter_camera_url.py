# Generated by Django 5.0.6 on 2024-09-03 12:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0018_alter_flat_square_metres'),
    ]

    operations = [
        migrations.AlterField(
            model_name='camera',
            name='description',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Məzmunu'),
        ),
        migrations.AlterField(
            model_name='camera',
            name='url',
            field=models.URLField(verbose_name='Kamera linki'),
        ),
    ]
