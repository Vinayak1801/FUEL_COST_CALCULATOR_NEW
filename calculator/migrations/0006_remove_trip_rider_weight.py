# Generated by Django 5.1.1 on 2024-10-15 14:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('calculator', '0005_trip_rider_weight'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trip',
            name='rider_weight',
        ),
    ]
