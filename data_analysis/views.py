from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import F
from .models import Performance, Actor, SeatGrade, Casting, Review, SalesData, SettlementData, MarketingCalendar, MarketingEvent, CrawlingTarget
from .forms import PerformanceForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.urls import reverse_lazy
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods
from django.core.exceptions import PermissionDenied
import json

@login_required
def index(request):
    context = {
        'performances': Performance.objects.all(),
        'actors': Actor.objects.all(),
        'seatgrades': SeatGrade.objects.all(),
        'castings': Casting.objects.all(),
    }
    return render(request, 'data_analysis/index.html', context)

# Performance Views
class PerformanceListView(LoginRequiredMixin, ListView):
    model = Performance
    template_name = 'data_analysis/performance/list.html'
    context_object_name = 'performances'
    ordering = ['-start_date']

class PerformanceDetailView(LoginRequiredMixin, DetailView):
    model = Performance
    template_name = 'data_analysis/performance/detail.html'
    context_object_name = 'performance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reviews = self.object.reviews.all()
        total_reviews = reviews.count()
        
        if total_reviews > 0:
            # 감정 분석 통계
            positive_count = reviews.filter(sentiment='positive').count()
            negative_count = reviews.filter(sentiment='negative').count()
            neutral_count = reviews.filter(sentiment='neutral').count()
            
            context['review_stats'] = {
                'total': total_reviews,
                'positive': {
                    'count': positive_count,
                    'percentage': round(positive_count / total_reviews * 100)
                },
                'negative': {
                    'count': negative_count,
                    'percentage': round(negative_count / total_reviews * 100)
                },
                'neutral': {
                    'count': neutral_count,
                    'percentage': round(neutral_count / total_reviews * 100)
                },
                'average_rating': round(sum(review.rating for review in reviews) / total_reviews, 1)
            }
        
        return context

class PerformanceCreateView(LoginRequiredMixin, CreateView):
    model = Performance
    form_class = PerformanceForm
    template_name = 'data_analysis/performance/form.html'
    success_url = reverse_lazy('data_analysis:performance_list')

class PerformanceUpdateView(LoginRequiredMixin, UpdateView):
    model = Performance
    form_class = PerformanceForm
    template_name = 'data_analysis/performance/form.html'
    success_url = reverse_lazy('data_analysis:performance_list')

class PerformanceDeleteView(LoginRequiredMixin, DeleteView):
    model = Performance
    template_name = 'data_analysis/performance/confirm_delete.html'
    success_url = reverse_lazy('data_analysis:performance_list')

# Actor Views
class ActorListView(LoginRequiredMixin, ListView):
    model = Actor
    template_name = 'data_analysis/actor/list.html'
    context_object_name = 'actors'
    ordering = ['name']

class ActorDetailView(LoginRequiredMixin, DetailView):
    model = Actor
    template_name = 'data_analysis/actor/detail.html'
    context_object_name = 'actor'

class ActorCreateView(LoginRequiredMixin, CreateView):
    model = Actor
    template_name = 'data_analysis/actor/form.html'
    fields = ['name']
    success_url = reverse_lazy('data_analysis:actor_list')

class ActorUpdateView(LoginRequiredMixin, UpdateView):
    model = Actor
    template_name = 'data_analysis/actor/form.html'
    fields = ['name']
    success_url = reverse_lazy('data_analysis:actor_list')

class ActorDeleteView(LoginRequiredMixin, DeleteView):
    model = Actor
    template_name = 'data_analysis/actor/confirm_delete.html'
    success_url = reverse_lazy('data_analysis:actor_list')

# SeatGrade Views
class SeatGradeListView(LoginRequiredMixin, ListView):
    model = SeatGrade
    template_name = 'data_analysis/seatgrade/list.html'
    context_object_name = 'seatgrades'
    ordering = ['performance', 'price']

class SeatGradeCreateView(LoginRequiredMixin, CreateView):
    model = SeatGrade
    template_name = 'data_analysis/seatgrade/form.html'
    fields = ['performance', 'name', 'price']
    success_url = reverse_lazy('data_analysis:seatgrade_list')

class SeatGradeUpdateView(LoginRequiredMixin, UpdateView):
    model = SeatGrade
    template_name = 'data_analysis/seatgrade/form.html'
    fields = ['performance', 'name', 'price']
    success_url = reverse_lazy('data_analysis:seatgrade_list')

class SeatGradeDeleteView(LoginRequiredMixin, DeleteView):
    model = SeatGrade
    template_name = 'data_analysis/seatgrade/confirm_delete.html'
    success_url = reverse_lazy('data_analysis:seatgrade_list')

# Casting Views
class CastingListView(LoginRequiredMixin, ListView):
    model = Casting
    template_name = 'data_analysis/casting/list.html'
    context_object_name = 'castings'
    ordering = ['performance', 'actor']

class CastingCreateView(LoginRequiredMixin, CreateView):
    model = Casting
    template_name = 'data_analysis/casting/form.html'
    fields = ['performance', 'actor', 'role_name']
    success_url = reverse_lazy('data_analysis:casting_list')

class CastingUpdateView(LoginRequiredMixin, UpdateView):
    model = Casting
    template_name = 'data_analysis/casting/form.html'
    fields = ['performance', 'actor', 'role_name']
    success_url = reverse_lazy('data_analysis:casting_list')

class CastingDeleteView(LoginRequiredMixin, DeleteView):
    model = Casting
    template_name = 'data_analysis/casting/confirm_delete.html'
    success_url = reverse_lazy('data_analysis:casting_list')

# Review Views
class ReviewListView(LoginRequiredMixin, ListView):
    model = Review
    template_name = 'data_analysis/review/list.html'
    context_object_name = 'reviews'
    ordering = ['-created_at']
    paginate_by = 10

class ReviewDetailView(LoginRequiredMixin, DetailView):
    model = Review
    template_name = 'data_analysis/review/detail.html'
    context_object_name = 'review'

    def get_object(self, queryset=None):
        # 조회수 증가
        obj = super().get_object(queryset)
        obj.views = F('views') + 1
        obj.save()
        return obj

class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    template_name = 'data_analysis/review/form.html'
    fields = ['performance', 'title', 'content', 'rating', 'nickname', 'sentiment']
    success_url = reverse_lazy('data_analysis:review_list')

class ReviewUpdateView(LoginRequiredMixin, UpdateView):
    model = Review
    template_name = 'data_analysis/review/form.html'
    fields = ['title', 'content', 'rating', 'sentiment']
    success_url = reverse_lazy('data_analysis:review_list')

class ReviewDeleteView(LoginRequiredMixin, DeleteView):
    model = Review
    template_name = 'data_analysis/review/confirm_delete.html'
    success_url = reverse_lazy('data_analysis:review_list')

class PerformanceReviewListView(LoginRequiredMixin, ListView):
    model = Review
    template_name = 'data_analysis/review/performance_reviews.html'
    context_object_name = 'reviews'
    paginate_by = 10

    def get_queryset(self):
        self.performance = get_object_or_404(Performance, pk=self.kwargs['performance_pk'])
        return Review.objects.filter(performance=self.performance).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['performance'] = self.performance
        return context

class ReviewLikeView(View):
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        review.likes = F('likes') + 1
        review.save()
        return JsonResponse({'status': 'success', 'likes': review.likes})

@login_required
def sales_data_upload(request, pk):
    performance = get_object_or_404(Performance, pk=pk)
    if request.method == 'POST':
        file = request.FILES.get('file')
        description = request.POST.get('description', '')
        
        if file and file.name.endswith(('.xlsx', '.xls')):
            SalesData.objects.create(
                performance=performance,
                file=file,
                description=description
            )
            messages.success(request, '판매현황 데이터가 업로드되었습니다.')
        else:
            messages.error(request, '엑셀 파일(.xlsx, .xls)만 업로드 가능합니다.')
    
    return redirect('data_analysis:performance_detail', pk=pk)

@login_required
def settlement_data_upload(request, pk):
    performance = get_object_or_404(Performance, pk=pk)
    if request.method == 'POST':
        file = request.FILES.get('file')
        description = request.POST.get('description', '')
        
        if file and file.name.endswith(('.xlsx', '.xls')):
            SettlementData.objects.create(
                performance=performance,
                file=file,
                description=description
            )
            messages.success(request, '정산서 데이터가 업로드되었습니다.')
        else:
            messages.error(request, '엑셀 파일(.xlsx, .xls)만 업로드 가능합니다.')
    
    return redirect('data_analysis:performance_detail', pk=pk)

@login_required
def sales_data_delete(request, pk):
    data = get_object_or_404(SalesData, pk=pk)
    performance_pk = data.performance.pk
    data.delete()
    messages.success(request, '판매현황 데이터가 삭제되었습니다.')
    return redirect('data_analysis:performance_detail', pk=performance_pk)

@login_required
def settlement_data_delete(request, pk):
    data = get_object_or_404(SettlementData, pk=pk)
    performance_pk = data.performance.pk
    data.delete()
    messages.success(request, '정산서 데이터가 삭제되었습니다.')
    return redirect('data_analysis:performance_detail', pk=performance_pk)

def marketing_calendar(request, pk):
    """마케팅 캘린더 뷰"""
    performance = get_object_or_404(Performance, pk=pk)
    calendar, created = MarketingCalendar.objects.get_or_create(
        performance=performance,
        defaults={
            'start_date': performance.start_date,
            'end_date': performance.end_date
        }
    )
    
    # 이벤트를 날짜별로 그룹화
    events = MarketingEvent.objects.filter(calendar=calendar)
    events_by_date = {}
    for event in events:
        date_str = event.start_date.isoformat()
        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'start_date': event.start_date.isoformat(),
            'end_date': event.end_date.isoformat(),
            'tag': event.tag,
            'color': event.color
        })
    
    context = {
        'performance': performance,
        'calendar': calendar,
        'events_json': json.dumps(events_by_date)
    }
    return render(request, 'data_analysis/marketing/calendar.html', context)

def marketing_calendar_settings(request, pk):
    """마케팅 캘린더 설정 뷰"""
    performance = get_object_or_404(Performance, pk=pk)
    calendar = get_object_or_404(MarketingCalendar, performance=performance)
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        calendar.start_date = start_date
        calendar.end_date = end_date
        calendar.save()
        
        messages.success(request, '캘린더 설정이 저장되었습니다.')
        return redirect('data_analysis:marketing_calendar', pk=pk)
    
    return redirect('data_analysis:marketing_calendar', pk=pk)

def marketing_event_create(request, pk):
    """마케팅 일정 생성 뷰"""
    performance = get_object_or_404(Performance, pk=pk)
    calendar = get_object_or_404(MarketingCalendar, performance=performance)
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        title = request.POST.get('title')
        description = request.POST.get('description')
        tag = request.POST.get('tag')
        color = request.POST.get('color')
        
        MarketingEvent.objects.create(
            calendar=calendar,
            start_date=start_date,
            end_date=end_date,
            title=title,
            description=description,
            tag=tag,
            color=color
        )
        
        messages.success(request, '일정이 추가되었습니다.')
    
    return redirect('data_analysis:marketing_calendar', pk=pk)

def marketing_event_update(request, pk, event_pk):
    """마케팅 일정 수정 뷰"""
    performance = get_object_or_404(Performance, pk=pk)
    event = get_object_or_404(MarketingEvent, pk=event_pk, calendar__performance=performance)
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        title = request.POST.get('title')
        description = request.POST.get('description')
        tag = request.POST.get('tag')
        color = request.POST.get('color')
        
        event.start_date = start_date
        event.end_date = end_date
        event.title = title
        event.description = description
        event.tag = tag
        event.color = color
        event.save()
        
        messages.success(request, '일정이 수정되었습니다.')
    
    return redirect('data_analysis:marketing_calendar', pk=pk)

def marketing_event_delete(request, pk, event_pk):
    """마케팅 일정 삭제 뷰"""
    performance = get_object_or_404(Performance, pk=pk)
    event = get_object_or_404(MarketingEvent, pk=event_pk, calendar__performance=performance)
    
    event.delete()
    messages.success(request, '일정이 삭제되었습니다.')
    
    return redirect('data_analysis:marketing_calendar', pk=pk)

@login_required
def add_crawling_target(request, performance_id):
    if request.method == 'POST':
        performance = get_object_or_404(Performance, id=performance_id)
        target = CrawlingTarget.objects.create(
            performance=performance,
            platform=request.POST['platform'],
            url=request.POST['url'],
            is_active=request.POST.get('is_active', False) == 'on'
        )
        return redirect('data_analysis:performance_detail', pk=performance_id)
    return JsonResponse({'status': 'error', 'message': '잘못된 요청입니다.'})

@login_required
def get_crawling_target(request, target_id):
    target = get_object_or_404(CrawlingTarget, id=target_id)
    return JsonResponse({
        'platform': target.platform,
        'url': target.url,
        'is_active': target.is_active,
    })

@login_required
@require_POST
def update_crawling_target(request, target_id):
    target = get_object_or_404(CrawlingTarget, id=target_id)
    target.platform = request.POST['platform']
    target.url = request.POST['url']
    target.is_active = request.POST.get('is_active', False) == 'on'
    target.save()
    return redirect('data_analysis:performance_detail', pk=target.performance.id)

@login_required
@require_POST
def delete_crawling_target(request, target_id):
    """크롤링 대상을 삭제합니다."""
    target = get_object_or_404(CrawlingTarget, id=target_id)
    performance_id = target.performance.id
    target.delete()
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def toggle_crawling_target(request, target_id):
    """크롤링 대상의 활성화 상태를 토글합니다."""
    target = get_object_or_404(CrawlingTarget, id=target_id)
    target.is_active = not target.is_active
    target.save()
    return JsonResponse({'status': 'success', 'is_active': target.is_active})