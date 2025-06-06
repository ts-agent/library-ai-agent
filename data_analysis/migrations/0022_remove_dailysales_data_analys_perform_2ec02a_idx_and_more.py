# Generated by Django 5.0.2 on 2025-04-30 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_analysis', '0021_salesdata_error_log_salesdata_file_hash_and_more'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='dailysales',
            name='data_analys_perform_2ec02a_idx',
        ),
        migrations.RemoveIndex(
            model_name='performancesession',
            name='data_analys_perform_fdd323_idx',
        ),
        migrations.RemoveIndex(
            model_name='performancesession',
            name='data_analys_perform_aa8f69_idx',
        ),
        migrations.RemoveIndex(
            model_name='sessionseatgradesales',
            name='data_analys_session_d9b5ee_idx',
        ),
        migrations.AlterUniqueTogether(
            name='performancesession',
            unique_together={('performance', 'session_date', 'session_time')},
        ),
        migrations.AlterField(
            model_name='dailysales',
            name='delta_revenue',
            field=models.IntegerField(default=0, verbose_name='증감(매출)'),
        ),
        migrations.AlterField(
            model_name='dailysales',
            name='revenue_total',
            field=models.PositiveIntegerField(verbose_name='누적 매출'),
        ),
    ]
