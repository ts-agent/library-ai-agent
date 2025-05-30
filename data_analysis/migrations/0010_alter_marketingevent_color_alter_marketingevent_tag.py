# Generated by Django 5.2 on 2025-04-21 04:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_analysis', '0009_alter_marketingevent_tag_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marketingevent',
            name='color',
            field=models.CharField(help_text='색상 코드 (예: #FF0000)', max_length=7, verbose_name='색상'),
        ),
        migrations.AlterField(
            model_name='marketingevent',
            name='tag',
            field=models.CharField(max_length=20, verbose_name='태그'),
        ),
    ]
