# Generated by Django 5.2 on 2025-04-18 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_analysis', '0003_salesdata_settlementdata'),
    ]

    operations = [
        migrations.AddField(
            model_name='performance',
            name='running_time',
            field=models.CharField(default='미정', help_text='예: 150분, 2시간 30분', max_length=50, verbose_name='공연시간'),
        ),
    ]
