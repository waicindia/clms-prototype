# Generated by Django 3.1.2 on 2021-01-06 12:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shelterhome',
            name='code',
        ),
    ]
