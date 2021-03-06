# Generated by Django 3.1.2 on 2021-02-23 10:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('child_management', '0012_auto_20210223_1033'),
    ]

    operations = [
        migrations.AlterField(
            model_name='childflaggedhistory',
            name='flagged_status',
            field=models.IntegerField(blank=True, choices=[(1, 'Child recommended for adoption enquiry'), (2, 'Legally free for adoption'), (3, 'Not applicable')], default=0, null=True),
        ),
    ]
