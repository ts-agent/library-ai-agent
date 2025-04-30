from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, URLValidator
from django.utils.translation import gettext_lazy as _


# 공연 기본 정보
class Performance(models.Model):
    GENRE_CHOICES = [
        ('concert', '콘서트'),
        ('musical', '뮤지컬'),
        ('play', '연극'),
        ('exhibition', '전시'),
    ]

    name            = models.CharField(max_length=200, verbose_name='공연명')
    genre           = models.CharField(max_length=20, choices=GENRE_CHOICES,
                                       default='concert', verbose_name='장르')
    poster          = models.ImageField(upload_to='posters/', null=True, blank=True,
                                       verbose_name='포스터')
    venue           = models.CharField(max_length=200, verbose_name='공연장소')
    start_date      = models.DateField(verbose_name='공연 시작일')
    end_date        = models.DateField(verbose_name='공연 종료일')
    age_limit       = models.CharField(max_length=50, verbose_name='관람연령')
    running_time    = models.CharField(max_length=50, default='', verbose_name='공연시간')
    description     = models.TextField(blank=True, verbose_name='공연 설명')
    total_sales     = models.DecimalField(max_digits=15, decimal_places=0,
                                          default=0, verbose_name='총 매출')
    total_audience  = models.PositiveIntegerField(default=0, verbose_name='총 관객수')
    occupancy_rate  = models.DecimalField(max_digits=5, decimal_places=2,
                                          default=0, verbose_name='객석 점유율')
    created_at      = models.DateTimeField(auto_now_add=True, verbose_name='등록일')
    updated_at      = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '공연'
        verbose_name_plural = '공연 목록'
        ordering = ['-start_date']

    def __str__(self):
        return self.name


# 공연별 좌석 등급
class SeatGrade(models.Model):
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE,
                                    related_name='seat_grades', verbose_name='공연')
    name        = models.CharField(max_length=50, verbose_name='등급명')
    price       = models.PositiveIntegerField(validators=[MinValueValidator(0)],
                                              verbose_name='가격')

    class Meta:
        verbose_name = '좌석 등급'
        verbose_name_plural = '좌석 등급 목록'
        unique_together = ['performance', 'name']

    def __str__(self):
        return f'{self.performance.name} - {self.name}'


# 배우 마스터
class Actor(models.Model):
    name       = models.CharField(max_length=100, verbose_name='배우명')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='등록일')

    class Meta:
        verbose_name = '배우'
        verbose_name_plural = '배우 목록'

    def __str__(self):
        return self.name


# 공연-배우 매핑
class Casting(models.Model):
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE,
                                    related_name='castings', verbose_name='공연')
    actor       = models.ForeignKey(Actor, on_delete=models.CASCADE,
                                    related_name='castings', verbose_name='배우')
    role_name   = models.CharField(max_length=100, verbose_name='역할명')

    class Meta:
        verbose_name = '캐스팅'
        verbose_name_plural = '캐스팅 목록'
        unique_together = ['performance', 'actor', 'role_name']

    def __str__(self):
        return f'{self.performance.name} - {self.actor.name} ({self.role_name})'


# 관람자 리뷰
class Review(models.Model):
    SENTIMENT_CHOICES = [
        ('positive', '긍정'),
        ('neutral',  '중립'),
        ('negative', '부정'),
    ]

    performance = models.ForeignKey(Performance, on_delete=models.CASCADE,
                                    related_name='reviews', verbose_name='공연')
    rating      = models.IntegerField(validators=[MinValueValidator(1),
                                                  MaxValueValidator(5)],
                                      verbose_name='별점')
    title       = models.CharField(max_length=200, verbose_name='리뷰 제목')
    content     = models.TextField(verbose_name='리뷰 내용')
    nickname    = models.CharField(max_length=50, verbose_name='닉네임')
    is_verified = models.BooleanField(default=False, verbose_name='예매자 인증 여부')
    sentiment   = models.CharField(max_length=10, choices=SENTIMENT_CHOICES,
                                   default='neutral', verbose_name='감정 분석')
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    views       = models.PositiveIntegerField(default=0, verbose_name='조회수')
    likes       = models.PositiveIntegerField(default=0, verbose_name='공감수')

    class Meta:
        verbose_name = '리뷰'
        verbose_name_plural = '리뷰 목록'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.performance.name} - {self.title} ({self.rating}점)'


# 공연 회차 정보
class PerformanceSession(models.Model):
    performance   = models.ForeignKey(Performance, on_delete=models.CASCADE,
                                      related_name='sessions', verbose_name='공연')
    session_date  = models.DateField(verbose_name='공연일')
    session_time  = models.TimeField(verbose_name='공연시간')
    round_number  = models.PositiveIntegerField(verbose_name='회차')
    day_of_week   = models.CharField(max_length=3, verbose_name='요일')

    class Meta:
        verbose_name = '공연 회차'
        verbose_name_plural = '공연 회차'
        unique_together = ['performance', 'session_date', 'session_time']
        ordering = ['session_date', 'session_time']

    def __str__(self):
        return f'{self.performance.name} - {self.session_date} {self.session_time}'


# 회차별 요약 판매
class SessionSummary(models.Model):
    session      = models.OneToOneField(PerformanceSession, on_delete=models.CASCADE,
                                        related_name='summary', verbose_name='회차')
    r_count      = models.PositiveIntegerField(null=True, verbose_name='R석 판매수')
    s_count      = models.PositiveIntegerField(null=True, verbose_name='S석 판매수')
    total_count  = models.PositiveIntegerField(null=True, verbose_name='총 판매수')
    total_amount = models.PositiveIntegerField(null=True, verbose_name='총 매출액')
    r_avg        = models.DecimalField(max_digits=10, decimal_places=2, null=True, verbose_name='R석 평균')
    s_avg        = models.DecimalField(max_digits=10, decimal_places=2, null=True, verbose_name='S석 평균')
    total_avg    = models.DecimalField(max_digits=10, decimal_places=2, null=True, verbose_name='전체 평균')
    amount_avg   = models.DecimalField(max_digits=10, decimal_places=2, null=True, verbose_name='금액 평균')

    class Meta:
        verbose_name = '회차별 판매 요약'
        verbose_name_plural = '회차별 판매 요약'

    def __str__(self):
        return f'{self.session} 요약'
        
    @classmethod
    def get_for_session(cls, session):
        """
        세션에 대한 요약 정보를 안전하게 가져옵니다.
        요약 정보가 없을 경우 기본값이 설정된 SessionSummary 객체를 반환합니다.
        이 메소드는 DoesNotExist 예외를 방지하기 위해 사용됩니다.
        """
        try:
            return cls.objects.get(session=session)
        except cls.DoesNotExist:
            # 데이터베이스에 저장하지 않는 임시 객체
            return cls(
                session=session,
                r_count=0,
                s_count=0,
                total_count=0,
                total_amount=0,
                r_avg=0,
                s_avg=0,
                total_avg=0,
                amount_avg=0
            )


# 회차-좌석등급 판매상세
class SessionSeatGradeSales(models.Model):
    session        = models.ForeignKey(PerformanceSession, on_delete=models.CASCADE,
                                       related_name='grade_sales', verbose_name='회차')
    seat_grade     = models.ForeignKey(SeatGrade, on_delete=models.CASCADE,
                                       related_name='grade_sales', verbose_name='좌석등급')
    sold_count     = models.PositiveIntegerField(verbose_name='판매수량')
    revenue        = models.PositiveIntegerField(verbose_name='매출액')
    occupancy_rate = models.DecimalField(max_digits=5, decimal_places=2,
                                         verbose_name='점유율')

    class Meta:
        verbose_name = '회차·좌석등급 판매'
        verbose_name_plural = '회차·좌석등급 판매'
        unique_together = ['session', 'seat_grade']

    def __str__(self):
        return f'{self.session} - {self.seat_grade.name}'


# 공연 일자별 누적
class DailySales(models.Model):
    performance      = models.ForeignKey(Performance, on_delete=models.CASCADE,
                                         related_name='daily_sales', verbose_name='공연')
    date             = models.DateField(verbose_name='날짜')
    sold_count_total = models.PositiveIntegerField(verbose_name='누적 판매수')
    revenue_total    = models.PositiveIntegerField(verbose_name='누적 매출')
    delta_count      = models.IntegerField(default=0, verbose_name='증감(좌석)')
    delta_revenue    = models.IntegerField(default=0, verbose_name='증감(매출)')

    class Meta:
        verbose_name = '일별 판매 집계'
        verbose_name_plural = '일별 판매 집계'
        unique_together = ['performance', 'date']
        ordering = ['date']

    def __str__(self):
        return f'{self.performance.name} - {self.date}'


# 무료 초대 내역
class InvitationRecord(models.Model):
    session        = models.ForeignKey(PerformanceSession, on_delete=models.CASCADE,
                                       related_name='invitations', verbose_name='회차')
    seat_grade     = models.ForeignKey(SeatGrade, on_delete=models.SET_NULL,
                                       null=True, blank=True, verbose_name='좌석등급')
    invited_count  = models.PositiveIntegerField(verbose_name='인원수')
    requester      = models.CharField(max_length=100, verbose_name='요청자')
    purpose        = models.CharField(max_length=100, verbose_name='용도')
    issued         = models.BooleanField(default=False, verbose_name='발권여부')
    note           = models.CharField(max_length=200, blank=True, verbose_name='비고')

    class Meta:
        verbose_name = '초대 내역'
        verbose_name_plural = '초대 내역'

    def __str__(self):
        return f'{self.session} 초대 {self.invited_count}명'


# 티켓 오픈 결과
class TicketOpenEvent(models.Model):
    performance        = models.ForeignKey(Performance, on_delete=models.CASCADE,
                                           related_name='ticket_open_events', verbose_name='공연')
    name               = models.CharField(max_length=50, verbose_name='오픈차수')
    open_date          = models.DateField(verbose_name='오픈일')
    reservation_rate   = models.DecimalField(max_digits=5, decimal_places=2,
                                             verbose_name='예매율')
    reservation_count  = models.PositiveIntegerField(verbose_name='예매건수')
    revenue_estimated  = models.PositiveIntegerField(verbose_name='추정 매출')

    class Meta:
        verbose_name = '티켓 오픈 결과'
        verbose_name_plural = '티켓 오픈 결과'
        ordering = ['open_date']
        unique_together = ['performance', 'name']

    def __str__(self):
        return f'{self.performance.name} {self.name}'


# 판매현황 파일 메타
class SalesData(models.Model):
    STATUS_CHOICES = [
        ('pending', '처리 대기'),
        ('processing', '처리 중'),
        ('done', '완료'),
        ('error', '오류'),
    ]
    
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE,
                                    related_name='sales_data', verbose_name='공연')
    file        = models.FileField(upload_to='sales_data/%Y/%m/', verbose_name='판매현황 파일')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='업로드 일시')
    description = models.CharField(max_length=200, blank=True, verbose_name='설명')

    # 판매 데이터 처리 상태 관련 필드
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', 
                             verbose_name='처리 상태')
    file_hash = models.CharField(max_length=64, blank=True, verbose_name='파일 해시')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='처리 완료 시간')
    error_log = models.TextField(blank=True, verbose_name='오류 로그')

    total_sales_count    = models.PositiveIntegerField(default=0, verbose_name='총 판매량')
    paid_rate            = models.DecimalField(max_digits=5, decimal_places=2,
                                               default=0, verbose_name='유료 점유율')
    free_rate            = models.DecimalField(max_digits=5, decimal_places=2,
                                               default=0, verbose_name='무료 점유율')
    total_occupancy_rate = models.DecimalField(max_digits=5, decimal_places=2,
                                               default=0, verbose_name='전체 점유율')
    target_amount        = models.BigIntegerField(default=0, verbose_name='목표 매출')
    total_amount         = models.BigIntegerField(default=0, verbose_name='총 매출액')
    average_ticket_price = models.DecimalField(max_digits=10, decimal_places=0,
                                               default=0, verbose_name='객단가')

    class Meta:
        verbose_name = '판매현황'
        verbose_name_plural = '판매현황'
        ordering = ['-uploaded_at']
        unique_together = ['performance', 'file_hash']
        indexes = [
            models.Index(fields=['performance', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.performance.name} 판매현황 {self.uploaded_at:%Y-%m-%d}'


# 공연별 정산서
class SettlementData(models.Model):
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE,
                                    related_name='settlement_data', verbose_name='공연')
    file        = models.FileField(upload_to='settlement_data/%Y/%m/',
                                   verbose_name='정산서 파일')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='업로드 일시')
    description = models.CharField(max_length=200, blank=True, verbose_name='설명')

    class Meta:
        verbose_name = '정산서'
        verbose_name_plural = '정산서'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.performance.name} 정산서 {self.uploaded_at:%Y-%m-%d}'


# 공연별 마케팅 캘린더
class MarketingCalendar(models.Model):
    performance = models.OneToOneField(Performance, on_delete=models.CASCADE,
                                       related_name='marketing_calendar', verbose_name='공연')
    start_date  = models.DateField(verbose_name='시작일')
    end_date    = models.DateField(verbose_name='종료일')
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at  = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '마케팅 캘린더'
        verbose_name_plural = '마케팅 캘린더'

    def __str__(self):
        return f'{self.performance.name} 마케팅 캘린더'


# 마케팅 일정 이벤트
class MarketingEvent(models.Model):
    calendar    = models.ForeignKey(MarketingCalendar, on_delete=models.CASCADE,
                                    related_name='events', verbose_name='마케팅 캘린더')
    start_date  = models.DateField(verbose_name='시작일')
    end_date    = models.DateField(verbose_name='종료일')
    title       = models.CharField(max_length=200, verbose_name='제목')
    description = models.TextField(verbose_name='내용')
    tag         = models.CharField(max_length=20, verbose_name='태그')
    color       = models.CharField(max_length=7, verbose_name='색상',
                                   help_text='색상 코드 (예: #FF0000)')
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at  = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '마케팅 일정'
        verbose_name_plural = '마케팅 일정'
        ordering = ['start_date']

    def __str__(self):
        return f'{self.calendar.performance.name} - {self.start_date}: {self.title}'


# 크롤링 타깃
class CrawlingTarget(models.Model):
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE,
                                    related_name='crawling_targets', verbose_name=_('공연'))
    platform    = models.CharField(max_length=50, verbose_name=_('플랫폼'))
    url         = models.URLField(max_length=500, validators=[URLValidator()],
                                  verbose_name=_('URL'))
    is_active   = models.BooleanField(default=True, verbose_name=_('활성화 여부'))
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name=_('등록일'))
    updated_at  = models.DateTimeField(auto_now=True, verbose_name=_('수정일'))
    last_crawled_at = models.DateTimeField(null=True, blank=True,
                                          verbose_name=_('마지막 크롤링 일시'))

    class Meta:
        verbose_name = _('크롤링 대상')
        verbose_name_plural = _('크롤링 대상 목록')
        unique_together = ['performance', 'platform', 'url']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.performance.name} - {self.platform}'
