# Generated by Django 5.0.6 on 2024-09-03 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0017_alter_flat_balance_alter_flat_is_rent_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flat',
            name='square_metres',
            field=models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Sahəsi'),
        ),
    ]
