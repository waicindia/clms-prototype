# Generated by Django 3.1.2 on 2021-01-27 08:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('child_management', '0003_auto_20210113_0854'),
    ]

    operations = [
        migrations.AddField(
            model_name='childshelterhomerelation',
            name='date_of_exit',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='child',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active')], db_index=True, default=2),
        ),
        migrations.AlterField(
            model_name='childshelterhomerelation',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active')], db_index=True, default=2),
        ),
        migrations.AlterField(
            model_name='familyvisit',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active')], db_index=True, default=2),
        ),
        migrations.AlterField(
            model_name='guardian',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'Inactive'), (2, 'Active')], db_index=True, default=2),
        ),
    ]
