# Generated by Django 5.1.1 on 2024-10-15 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calculator', '0002_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='trip',
            name='rider_weight',
            field=models.FloatField(default=60),
        ),
        migrations.DeleteModel(
            name='UserProfile',
        ),
    ]