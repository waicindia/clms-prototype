# Generated by Django 3.1.2 on 2021-02-01 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0008_auto_20210129_1343'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shelterhome',
            name='latitude',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='shelterhome',
            name='longitude',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
