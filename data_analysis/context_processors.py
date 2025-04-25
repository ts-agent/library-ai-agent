from django.utils import timezone
from .models import Performance

def sidebar_context(request):
    """
    사이드바에 표시할 컨텍스트를 제공하는 context processor
    """
    if not request.user.is_authenticated:
        return {
            'upcoming_performances': [],
            'ongoing_performances': [],
            'completed_performances': []
        }

    now = timezone.now()
    
    # 공연 전 (시작일이 현재보다 미래)
    upcoming_performances = Performance.objects.filter(
        start_date__gt=now
    ).order_by('start_date')
    
    # 공연 중 (현재 날짜가 시작일과 종료일 사이)
    ongoing_performances = Performance.objects.filter(
        start_date__lte=now,
        end_date__gte=now
    ).order_by('end_date')
    
    # 공연 종료 (종료일이 현재보다 과거)
    completed_performances = Performance.objects.filter(
        end_date__lt=now
    ).order_by('-end_date')[:5]  # 최근 5개만 표시
    
    return {
        'upcoming_performances': upcoming_performances,
        'ongoing_performances': ongoing_performances,
        'completed_performances': completed_performances
    } 