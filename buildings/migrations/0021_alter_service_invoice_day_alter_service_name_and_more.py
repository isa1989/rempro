# Generated by Django 5.0.6 on 2024-09-04 11:02

import buildings.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buildings', '0020_alter_camera_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='service',
            name='invoice_day',
            field=models.IntegerField(help_text='Enter the day of the month when the invoice is issued', validators=[buildings.models.validate_day], verbose_name='Ödəniş günü'),
        ),
        migrations.AlterField(
            model_name='service',
            name='name',
            field=models.CharField(help_text='Enter the name of the service', max_length=255, verbose_name='Xidmətin adı'),
        ),
        migrations.AlterField(
            model_name='service',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Enter the price of the service', max_digits=10, verbose_name='Qiymət'),
        ),
    ]
