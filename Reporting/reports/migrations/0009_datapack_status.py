# Generated by Django 4.0.5 on 2022-10-04 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0008_alter_report_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='datapack',
            name='status',
            field=models.TextField(choices=[('In Progress', 'In Progress'), ('Completed', 'Completed'), ('Not Released', 'Not Released')], default='In Progress'),
        ),
    ]
