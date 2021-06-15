# Generated by Django 3.1.2 on 2021-03-05 11:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('child_management', '0014_auto_20210305_1104'),
    ]

    operations = [
        migrations.AlterField(
            model_name='child',
            name='sex',
            field=models.IntegerField(choices=[(1, 'Male'), (2, 'Female'), (3, 'Transgender'), (4, 'Inter-sex'), (5, 'Other')]),
        ),
        migrations.AlterField(
            model_name='childshelterhomerelation',
            name='child',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='child_management.child', verbose_name='Case number'),
        ),
    ]
