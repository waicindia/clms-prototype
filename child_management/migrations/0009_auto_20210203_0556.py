# Generated by Django 3.1.2 on 2021-02-03 05:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('child_management', '0008_child_date_declaring_child_free_for_adoption'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='child',
            name='last_date_of_cwc_order_or_review',
        ),
        migrations.AlterField(
            model_name='child',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'No'), (2, 'Yes')], db_index=True, default=2),
        ),
        migrations.AlterField(
            model_name='childflaggedhistory',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'No'), (2, 'Yes')], db_index=True, default=2),
        ),
        migrations.AlterField(
            model_name='childshelterhomerelation',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'No'), (2, 'Yes')], db_index=True, default=2),
        ),
        migrations.AlterField(
            model_name='familyvisit',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'No'), (2, 'Yes')], db_index=True, default=2),
        ),
        migrations.AlterField(
            model_name='guardian',
            name='active',
            field=models.PositiveIntegerField(choices=[(0, 'No'), (2, 'Yes')], db_index=True, default=2),
        ),
        migrations.CreateModel(
            name='ChildCWCHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.PositiveIntegerField(choices=[(0, 'No'), (2, 'Yes')], db_index=True, default=2)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('modified_on', models.DateTimeField(auto_now=True)),
                ('last_date_of_cwc_order_or_review', models.DateField()),
                ('child', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='child_management.child')),
            ],
            options={
                'verbose_name_plural': 'Child CWC History',
            },
        ),
    ]