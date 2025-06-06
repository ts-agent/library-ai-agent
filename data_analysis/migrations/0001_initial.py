# Generated by Django 5.2 on 2025-04-18 11:06

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Actor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='배우명')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='등록일')),
            ],
            options={
                'verbose_name': '배우',
                'verbose_name_plural': '배우 목록',
            },
        ),
        migrations.CreateModel(
            name='Performance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='공연명')),
                ('venue', models.CharField(max_length=200, verbose_name='공연장소')),
                ('start_date', models.DateField(verbose_name='공연 시작일')),
                ('end_date', models.DateField(verbose_name='공연 종료일')),
                ('age_limit', models.CharField(max_length=50, verbose_name='관람연령')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='등록일')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='수정일')),
            ],
            options={
                'verbose_name': '공연',
                'verbose_name_plural': '공연 목록',
                'ordering': ['-start_date'],
            },
        ),
        migrations.CreateModel(
            name='Casting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_name', models.CharField(max_length=100, verbose_name='역할명')),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='castings', to='data_analysis.actor', verbose_name='배우')),
                ('performance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='castings', to='data_analysis.performance', verbose_name='공연')),
            ],
            options={
                'verbose_name': '캐스팅',
                'verbose_name_plural': '캐스팅 목록',
                'unique_together': {('performance', 'actor', 'role_name')},
            },
        ),
        migrations.CreateModel(
            name='SeatGrade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='등급명')),
                ('price', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='가격')),
                ('performance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seat_grades', to='data_analysis.performance', verbose_name='공연')),
            ],
            options={
                'verbose_name': '좌석 등급',
                'verbose_name_plural': '좌석 등급 목록',
                'unique_together': {('performance', 'name')},
            },
        ),
    ]
