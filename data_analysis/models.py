from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, URLValidator
from django.utils.translation import gettext_lazy as _

class Performance(models.Model):
    """공연 정보를 저장하는 모델"""
    GENRE_CHOICES = [
        ('concert', '콘서트'),
        ('musical', '뮤지컬'),
        ('play', '연극'),
        ('exhibition', '전시'),
    ]

    name = models.CharField(max_length=200, verbose_name='공연명')
    genre = models.CharField(max_length=20, choices=GENRE_CHOICES, default='concert', verbose_name='장르')
    venue = models.CharField(max_length=200, verbose_name='공연장소')
    start_date = models.DateField(verbose_name='공연 시작일')
    end_date = models.DateField(verbose_name='공연 종료일')
    age_limit = models.CharField(max_length=50, verbose_name='관람연령')
    running_time = models.CharField(max_length=50, verbose_name='공연시간', default='')
    description = models.TextField(verbose_name='공연 설명', blank=True)
    total_sales = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name='총 매출')
    total_audience = models.PositiveIntegerField(default=0, verbose_name='총 관객수')
    occupancy_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='객석 점유율')
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

class Review(models.Model):
    """공연 리뷰 정보를 저장하는 모델"""
    SENTIMENT_CHOICES = [
        ('positive', '긍정'),
        ('neutral', '중립'),
        ('negative', '부정'),
    ]

    performance = models.ForeignKey(
        Performance,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='공연'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='별점'
    )
    title = models.CharField(max_length=200, verbose_name='리뷰 제목')
    content = models.TextField(verbose_name='리뷰 내용')
    nickname = models.CharField(max_length=50, verbose_name='닉네임')
    is_verified = models.BooleanField(default=False, verbose_name='예매자 인증 여부')
    sentiment = models.CharField(
        max_length=10,
        choices=SENTIMENT_CHOICES,
        default='neutral',
        verbose_name='감정 분석'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    views = models.PositiveIntegerField(default=0, verbose_name='조회수')
    likes = models.PositiveIntegerField(default=0, verbose_name='공감수')

    class Meta:
        verbose_name = '리뷰'
        verbose_name_plural = '리뷰 목록'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.performance.name} - {self.title} ({self.rating}점)'

class SalesData(models.Model):
    performance = models.ForeignKey('Performance', on_delete=models.CASCADE, related_name='sales_data', verbose_name='공연')
    file = models.FileField(upload_to='sales_data/%Y/%m/', verbose_name='판매현황 파일')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='업로드 일시')
    description = models.CharField(max_length=200, blank=True, verbose_name='설명')
    
    # 판매량 및 점유율
    total_sales_count = models.PositiveIntegerField(default=0, verbose_name='총 판매량')
    paid_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='유료 점유율')
    free_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='무료 점유율')
    total_occupancy_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='전체 점유율')
    
    # 매출 관련
    target_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name='목표 매출')
    total_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name='총 매출액')
    average_ticket_price = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name='객단가')

    class Meta:
        verbose_name = '판매현황'
        verbose_name_plural = '판매현황'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.performance.name} - 판매현황 ({self.uploaded_at.strftime('%Y-%m-%d')})"

class SettlementData(models.Model):
    performance = models.ForeignKey('Performance', on_delete=models.CASCADE, related_name='settlement_data', verbose_name='공연')
    file = models.FileField(upload_to='settlement_data/%Y/%m/', verbose_name='정산서 파일')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='업로드 일시')
    description = models.CharField(max_length=200, blank=True, verbose_name='설명')

    class Meta:
        verbose_name = '정산서'
        verbose_name_plural = '정산서'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.performance.name} - 정산서 ({self.uploaded_at.strftime('%Y-%m-%d')})"

class MarketingCalendar(models.Model):
    """공연의 마케팅 캘린더"""
    performance = models.OneToOneField(
        'Performance',
        on_delete=models.CASCADE,
        related_name='marketing_calendar',
        verbose_name='공연'
    )
    start_date = models.DateField(verbose_name='시작일')
    end_date = models.DateField(verbose_name='종료일')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '마케팅 캘린더'
        verbose_name_plural = '마케팅 캘린더'

    def __str__(self):
        return f"{self.performance.name} 마케팅 캘린더"

class MarketingEvent(models.Model):
    """마케팅 캘린더의 일정"""
    calendar = models.ForeignKey(
        MarketingCalendar,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='마케팅 캘린더'
    )
    start_date = models.DateField(verbose_name='시작일')
    end_date = models.DateField(verbose_name='종료일')
    title = models.CharField(max_length=200, verbose_name='제목')
    description = models.TextField(verbose_name='내용')
    tag = models.CharField(
        max_length=20,
        verbose_name='태그'
    )
    color = models.CharField(
        max_length=7,
        verbose_name='색상',
        help_text='색상 코드 (예: #FF0000)'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '마케팅 일정'
        verbose_name_plural = '마케팅 일정'
        ordering = ['start_date']

    def __str__(self):
        return f"{self.calendar.performance.name} - {self.start_date}: {self.title}"

class CrawlingTarget(models.Model):
    """크롤링 대상 공연 정보를 관리하는 모델"""
    
    performance = models.ForeignKey(
        'Performance',
        on_delete=models.CASCADE,
        related_name='crawling_targets',
        verbose_name=_('공연')
    )
    
    platform = models.CharField(
        max_length=50,
        verbose_name=_('플랫폼'),
        help_text=_('크롤링할 플랫폼 이름을 입력하세요. (예: 인터파크티켓, 티켓링크, 인스타그램)')
    )
    
    url = models.URLField(
        max_length=500,
        validators=[URLValidator()],
        verbose_name=_('URL'),
        help_text=_('크롤링할 페이지의 URL을 입력하세요.')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('활성화 여부'),
        help_text=_('크롤링 대상 활성화 여부를 설정합니다.')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('등록일')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('수정일')
    )
    
    last_crawled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('마지막 크롤링 일시'),
        help_text=_('가장 최근에 크롤링을 수행한 일시입니다.')
    )

    class Meta:
        verbose_name = _('크롤링 대상')
        verbose_name_plural = _('크롤링 대상 목록')
        ordering = ['-created_at']
        unique_together = ['performance', 'platform', 'url']

    def __str__(self):
        return f"{self.performance.name} - {self.platform}"
