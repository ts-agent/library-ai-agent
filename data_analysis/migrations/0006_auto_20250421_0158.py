# Generated by Django 5.2 on 2025-04-21 01:58

from django.db import migrations, models

def migrate_dates(apps, schema_editor):
    MarketingEvent = apps.get_model('data_analysis', 'MarketingEvent')
    for event in MarketingEvent.objects.all():
        event.start_date = event.date
        event.end_date = event.date
        event.tag = 'other'
        event.color = '#a8deff'
        event.save()

class Migration(migrations.Migration):

    dependencies = [
        ('data_analysis', '0005_marketingcalendar_marketingevent'),
    ]

    operations = [
        migrations.AddField(
            model_name='marketingevent',
            name='start_date',
            field=models.DateField(null=True, verbose_name='시작일'),
        ),
        migrations.AddField(
            model_name='marketingevent',
            name='end_date',
            field=models.DateField(null=True, verbose_name='종료일'),
        ),
        migrations.AddField(
            model_name='marketingevent',
            name='tag',
            field=models.CharField(
                choices=[
                    ('promotion', '프로모션'),
                    ('marketing', '마케팅'),
                    ('press', '언론보도'),
                    ('event', '이벤트'),
                    ('sns', 'SNS'),
                    ('other', '기타'),
                ],
                default='other',
                max_length=20,
                verbose_name='태그'
            ),
        ),
        migrations.AddField(
            model_name='marketingevent',
            name='color',
            field=models.CharField(
                choices=[
                    ('#a8deff', '하늘색'),
                    ('#ff8a8a', '빨간색'),
                    ('#a8ff8f', '초록색'),
                    ('#ffdc73', '노란색'),
                    ('#d9a8ff', '보라색'),
                    ('#ffc4a8', '주황색'),
                ],
                default='#a8deff',
                max_length=7,
                verbose_name='색상'
            ),
        ),
        migrations.RunPython(migrate_dates),
        migrations.AlterField(
            model_name='marketingevent',
            name='start_date',
            field=models.DateField(verbose_name='시작일'),
        ),
        migrations.AlterField(
            model_name='marketingevent',
            name='end_date',
            field=models.DateField(verbose_name='종료일'),
        ),
        migrations.RemoveField(
            model_name='marketingevent',
            name='date',
        ),
    ]
