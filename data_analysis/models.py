from django.db import models
from django.core.validators import MinValueValidator

class Performance(models.Model):
    """공연 정보를 저장하는 모델"""
    name = models.CharField(max_length=200, verbose_name='공연명')
    venue = models.CharField(max_length=200, verbose_name='공연장소')
    start_date = models.DateField(verbose_name='공연 시작일')
    end_date = models.DateField(verbose_name='공연 종료일')
    age_limit = models.CharField(max_length=50, verbose_name='관람연령')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='등록일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '공연'
        verbose_name_plural = '공연 목록'
        ordering = ['-start_date']

    def __str__(self):
        return self.name

class SeatGrade(models.Model):
    """좌석 등급 정보를 저장하는 모델"""
    performance = models.ForeignKey(
        Performance, 
        on_delete=models.CASCADE, 
        related_name='seat_grades',
        verbose_name='공연'
    )
    name = models.CharField(max_length=50, verbose_name='등급명')
    price = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        verbose_name='가격'
    )

    class Meta:
        verbose_name = '좌석 등급'
        verbose_name_plural = '좌석 등급 목록'
        unique_together = ['performance', 'name']

    def __str__(self):
        return f'{self.performance.name} - {self.name}'

class Actor(models.Model):
    """배우 정보를 저장하는 모델"""
    name = models.CharField(max_length=100, verbose_name='배우명')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='등록일')

    class Meta:
        verbose_name = '배우'
        verbose_name_plural = '배우 목록'

    def __str__(self):
        return self.name

class Casting(models.Model):
    """공연의 캐스팅 정보를 저장하는 모델"""
    performance = models.ForeignKey(
        Performance, 
        on_delete=models.CASCADE, 
        related_name='castings',
        verbose_name='공연'
    )
    actor = models.ForeignKey(
        Actor, 
        on_delete=models.CASCADE, 
        related_name='castings',
        verbose_name='배우'
    )
    role_name = models.CharField(max_length=100, verbose_name='역할명')

    class Meta:
        verbose_name = '캐스팅'
        verbose_name_plural = '캐스팅 목록'
        unique_together = ['performance', 'actor', 'role_name']

    def __str__(self):
        return f'{self.performance.name} - {self.actor.name} ({self.role_name})'
