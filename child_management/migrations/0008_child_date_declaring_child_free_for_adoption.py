# Generated by Django 3.1.2 on 2021-02-01 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('child_management', '0007_auto_20210201_0711'),
    ]

    operations = [
        migrations.AddField(
            model_name='child',
            name='date_declaring_child_free_for_adoption',
            field=models.DateField(blank=True, null=True),
        ),
    ]
