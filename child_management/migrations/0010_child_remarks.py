# Generated by Django 3.1.2 on 2021-02-03 10:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('child_management', '0009_auto_20210203_0556'),
    ]

    operations = [
        migrations.AddField(
            model_name='child',
            name='remarks',
            field=models.TextField(blank=True, null=True),
        ),
    ]
