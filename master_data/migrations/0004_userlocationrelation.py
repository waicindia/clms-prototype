# Generated by Django 3.1.2 on 2021-01-13 08:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('master_data', '0003_auto_20210108_0551'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserLocationRelation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.IntegerField(db_index=True, default=2)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('modified_on', models.DateTimeField(auto_now=True)),
                ('location_id', models.PositiveIntegerField()),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='auth.group')),
                ('location_hierarchy_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'User Location Relation',
            },
        ),
    ]
