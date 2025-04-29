from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View, TemplateView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.db.models import F, Sum, Avg, Max
from .models import Performance, Actor, SeatGrade, Casting, Review, SalesData, SettlementData, MarketingCalendar, MarketingEvent, CrawlingTarget, SessionSummary
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
from django.core.management import call_command
from django.contrib.auth.models import User
from django.conf import settings
import os
from django.utils import timezone
import calendar
from datetime import timedelta
from decimal import Decimal
from data_analysis.management.commands.import_sales import import_one_file
from django.core.files.storage import FileSystemStorage

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
        
        # 공연 세션 및 회차별 요약 정보 가져오기
        performance = self.get_object()
        sessions = performance.sessions.all()
        
        # 일정 데이터
        events = {}
        for calendar in MarketingCalendar.objects.filter(performance=performance):
            for event in calendar.events.all():
                date_str = event.start_date.strftime('%Y-%m-%d')
                if date_str not in events:
                    events[date_str] = []
                
                events[date_str].append({
                    'id': event.id,
                    'title': event.title,
                    'start_date': event.start_date.strftime('%Y-%m-%d'),
                    'end_date': event.end_date.strftime('%Y-%m-%d'),
                    'description': event.description,
                    'tag': event.tag,
                    'color': event.color
                })
                
        context['events_json'] = json.dumps(events)
        
        # 세션 및 요약 정보를 JSON으로 직렬화
        session_data = {}
        for session in sessions:
            try:
                summary = session.summary
                summary_data = {
                    'r_count': summary.r_count,
                    's_count': summary.s_count,
                    'total_count': summary.total_count,
                    'total_amount': summary.total_amount,
                    'r_avg': float(summary.r_avg) if summary.r_avg else 0,
                    's_avg': float(summary.s_avg) if summary.s_avg else 0,
                    'total_avg': float(summary.total_avg) if summary.total_avg else 0,
                    'amount_avg': float(summary.amount_avg) if summary.amount_avg else 0
                }
            except SessionSummary.DoesNotExist:
                # 요약 정보가 없는 경우 기본값 설정
                summary_data = {
                    'r_count': 0,
                    's_count': 0,
                    'total_count': 0,
                    'total_amount': 0,
                    'r_avg': 0,
                    's_avg': 0,
                    'total_avg': 0,
                    'amount_avg': 0
                }
            
            session_data[session.id] = {
                'id': session.id,
                'date': session.session_date.strftime('%Y-%m-%d'),
                'time': session.session_time.strftime('%H:%M'),
                'round_number': session.round_number,
                'day_of_week': session.day_of_week,
                'summary': summary_data
            }
            
        context['sessions_json'] = json.dumps(session_data)
        
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
    try:
        performance = Performance.objects.get(pk=pk)
    except Performance.DoesNotExist:
        messages.error(request, '해당 공연을 찾을 수 없습니다.')
        return redirect('data_analysis:performance_list')

    if request.method == "POST":
        # AJAX 요청인지 확인
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if not request.FILES.get('file'):
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': '업로드할 파일을 선택해주세요.'}, status=400)
            else:
                messages.error(request, '업로드할 파일을 선택해주세요.')
                return redirect('data_analysis:performance_detail', pk=pk)
        
        file = request.FILES['file']
        if not file.name.endswith('.xlsx'):
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': 'Excel 파일(.xlsx)만 업로드 가능합니다.'}, status=400)
            else:
                messages.error(request, 'Excel 파일(.xlsx)만 업로드 가능합니다.')
                return redirect('data_analysis:performance_detail', pk=pk)
        
        # 파일 저장
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        filename = fs.save(file.name, file)
        uploaded_file_path = os.path.join(settings.MEDIA_ROOT, filename)
        
        try:
            # 기존 import_one_file 함수 호출 시 performance_id 전달
            import_one_file(uploaded_file_path, performance_id=pk)
            
            if is_ajax:
                return JsonResponse({'status': 'success', 'message': '판매 데이터가 성공적으로 업로드되었습니다.'})
            else:
                messages.success(request, '판매 데이터가 성공적으로 업로드되었습니다.')
                return redirect('data_analysis:performance_detail', pk=pk)
        except Exception as e:
            error_message = f'파일 처리 중 오류가 발생했습니다: {str(e)}'
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': error_message}, status=500)
            else:
                messages.error(request, error_message)
                return redirect('data_analysis:performance_detail', pk=pk)
        finally:
            # 임시 파일 삭제
            if os.path.exists(uploaded_file_path):
                os.remove(uploaded_file_path)
    
    return render(request, 'data_analysis/sales_data_upload.html', {'performance': performance})

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
    return redirect('data_analysis:performance_detail', pk=pk)

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
    
    return redirect('data_analysis:performance_detail', pk=pk)

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
def add_crawling_target(request, pk):
    """
    새로운 크롤링 대상을 추가합니다.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            platform = data.get('platform')
            url = data.get('url')
            is_active = data.get('is_active', True)
            
            if not all([platform, url]):
                return JsonResponse({'error': '플랫폼과 URL을 모두 입력해주세요.'}, status=400)
            
            performance = get_object_or_404(Performance, pk=pk)
            
            # 중복 체크
            if CrawlingTarget.objects.filter(performance=performance, platform=platform, url=url).exists():
                return JsonResponse({'error': '이미 등록된 크롤링 대상입니다.'}, status=400)
            
            # 크롤링 대상 저장
            target = CrawlingTarget.objects.create(
                performance=performance,
                platform=platform,
                url=url,
                is_active=is_active
            )
            
            return JsonResponse({
                'message': '크롤링 대상이 성공적으로 추가되었습니다.',
                'target_id': target.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': '잘못된 요청 형식입니다.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': '허용되지 않는 메소드입니다.'}, status=405)

@login_required
@require_POST
def update_crawling_target(request, target_id):
    """
    기존 크롤링 대상의 정보를 업데이트합니다.
    """
    try:
        target = get_object_or_404(CrawlingTarget, pk=target_id)
        data = json.loads(request.body)
        
        # 필드 업데이트
        target.platform = data.get('platform', target.platform)
        target.url = data.get('url', target.url)
        target.is_active = data.get('is_active', target.is_active)
        target.save()
        
        return JsonResponse({
            'message': '크롤링 대상이 성공적으로 업데이트되었습니다.',
            'target': {
                'id': target.id,
                'platform': target.platform,
                'url': target.url,
                'is_active': target.is_active
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 요청 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_crawling_target(request, target_id):
    """
    특정 크롤링 대상의 정보를 반환합니다.
    """
    try:
        target = get_object_or_404(CrawlingTarget, pk=target_id)
        return JsonResponse({
            'platform': target.platform,
            'url': target.url,
            'is_active': target.is_active
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def delete_crawling_target(request, target_id):
    """
    크롤링 대상을 삭제합니다.
    """
    try:
        target = get_object_or_404(CrawlingTarget, pk=target_id)
        performance_id = target.performance.id
        target.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'message': '크롤링 대상이 성공적으로 삭제되었습니다.'})
        else:
            messages.success(request, '크롤링 대상이 성공적으로 삭제되었습니다.')
            return redirect('data_analysis:performance_detail', pk=performance_id)
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=500)
        else:
            messages.error(request, f'크롤링 대상 삭제 중 오류가 발생했습니다: {str(e)}')
            return redirect('data_analysis:performance_detail', pk=performance_id)

@login_required
@require_POST
def toggle_crawling_target(request, target_id):
    """
    크롤링 대상의 활성화 상태를 토글합니다.
    """
    try:
        target = get_object_or_404(CrawlingTarget, pk=target_id)
        target.is_active = not target.is_active
        target.save()
        return JsonResponse({
            'message': '크롤링 대상의 상태가 변경되었습니다.',
            'is_active': target.is_active
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def create_super_user(request):
    # 허용된 IP 주소 목록
    ALLOWED_IPS = ['127.0.0.1', 'localhost', '183.98.186.21']
    
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '') or request.META.get('REMOTE_ADDR')
    if client_ip.split(',')[0].strip() not in ALLOWED_IPS:
        return HttpResponse("접근이 허용되지 않은 IP입니다.", status=403)
    
    try:
        # 이미 superuser가 존재하는지 확인
        if User.objects.filter(is_superuser=True).exists():
            return HttpResponse("Superuser가 이미 존재합니다.")
        
        # superuser 생성
        User.objects.create_superuser(
            username='admin',
            email='agent@ticketsquare.co.kr',
            password='ts0315^^'
        )
        return HttpResponse("Superuser가 성공적으로 생성되었습니다.")
    except Exception as e:
        return HttpResponse(f"오류 발생: {str(e)}", status=500)

class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'data_analysis/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 전체 데이터
        all_performances = Performance.objects.all()
        
        # 장르별 데이터
        genre_data = {
            'all': all_performances,
            'concert': all_performances.filter(genre='concert'),
            'theater': all_performances.filter(genre='theater'),
            'musical': all_performances.filter(genre='musical'),
            'exhibition': all_performances.filter(genre='exhibition')
        }

        # 장르별 통계 데이터 계산
        stats = {}
        for genre, queryset in genre_data.items():
            stats[genre] = {
                'total_sales': queryset.aggregate(Sum('total_sales'))['total_sales__sum'] or 0,
                'total_audience': queryset.aggregate(Sum('total_audience'))['total_audience__sum'] or 0,
                'avg_occupancy': queryset.aggregate(Avg('occupancy'))['occupancy__avg'] or 0,
                'active_count': queryset.filter(end_date__gte=timezone.now()).count(),
                'monthly_sales': self.get_monthly_sales(queryset),
                'genre_distribution': self.get_genre_distribution(queryset)
            }

        context.update({
            'performances': all_performances,
            'stats': stats,
            'current_month': timezone.now().strftime('%Y년 %m월')
        })
        
        return context
    
    def get_monthly_sales(self, queryset):
        """월별 판매 추이 데이터 계산"""
        current_year = timezone.now().year
        monthly_sales = []
        
        for month in range(1, 13):
            sales = queryset.filter(
                sales_data__uploaded_at__year=current_year,
                sales_data__uploaded_at__month=month
            ).aggregate(
                total=Sum('sales_data__total_amount')
            )['total'] or 0
            monthly_sales.append(sales)
        
        return monthly_sales

    def get_genre_distribution(self, queryset):
        """장르별 판매 비율 데이터 계산"""
        return {
            'concert': queryset.filter(genre='concert').count(),
            'theater': queryset.filter(genre='theater').count(),
            'musical': queryset.filter(genre='musical').count(),
            'exhibition': queryset.filter(genre='exhibition').count()
        }

class ConcertDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'data_analysis/dashboard/concert_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 현재 시간 기준으로 진행중인 공연 필터링
        now = timezone.now()
        performances = Performance.objects.filter(genre='concert')
        active_performances = performances.filter(start_date__lte=now, end_date__gte=now)
        active_performances_count = active_performances.count()
        
        # 전월 동일 시점 진행중인 공연 수 계산
        last_month = now - timedelta(days=30)
        last_month_active = performances.filter(
            start_date__lte=last_month,
            end_date__gte=last_month
        ).count()
        
        # 전월 대비 증감률 계산
        if last_month_active > 0:
            performance_change = ((active_performances_count - last_month_active) / last_month_active) * 100
        else:
            performance_change = 0
            
        context.update({
            'active_performances': active_performances,
            'active_performances_count': active_performances_count,
            'performance_change': performance_change,
        })
        
        return context

class MusicalDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'data_analysis/dashboard/musical_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        performances = Performance.objects.filter(genre='musical')
        
        # 통계 데이터 계산
        context['total_sales'] = performances.aggregate(Sum('total_sales'))['total_sales__sum'] or 0
        context['total_audience'] = performances.aggregate(Sum('total_audience'))['total_audience__sum'] or 0
        context['avg_occupancy'] = performances.aggregate(Avg('occupancy_rate'))['occupancy_rate__avg'] or 0
        
        # 진행중인 공연 QuerySet
        active_performances = performances.filter(
            start_date__lte=now,
            end_date__gte=now
        )
        context['active_performances'] = active_performances
        context['active_performances_count'] = active_performances.count()
        
        # 차트 데이터 준비
        sales_data = {
            'labels': [p.name for p in performances[:10]],
            'data': [p.total_sales for p in performances[:10]]
        }
        audience_data = {
            'labels': [p.name for p in performances[:10]],
            'data': [p.total_audience for p in performances[:10]]
        }
        
        context['sales_data'] = json.dumps(sales_data, cls=DecimalEncoder)
        context['audience_data'] = json.dumps(audience_data)
        context['performances'] = performances
        
        return context

class PlayDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'data_analysis/dashboard/play_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        performances = Performance.objects.filter(genre='play')
        
        # 통계 데이터 계산
        context['total_sales'] = performances.aggregate(Sum('total_sales'))['total_sales__sum'] or 0
        context['total_audience'] = performances.aggregate(Sum('total_audience'))['total_audience__sum'] or 0
        context['avg_occupancy'] = performances.aggregate(Avg('occupancy_rate'))['occupancy_rate__avg'] or 0
        
        # 진행중인 공연 QuerySet
        active_performances = performances.filter(
            start_date__lte=now,
            end_date__gte=now
        )
        context['active_performances'] = active_performances
        context['active_performances_count'] = active_performances.count()
        
        # 차트 데이터 준비
        sales_data = {
            'labels': [p.name for p in performances[:10]],
            'data': [p.total_sales for p in performances[:10]]
        }
        audience_data = {
            'labels': [p.name for p in performances[:10]],
            'data': [p.total_audience for p in performances[:10]]
        }
        
        context['sales_data'] = json.dumps(sales_data)
        context['audience_data'] = json.dumps(audience_data)
        context['performances'] = performances
        
        return context

class ExhibitionDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'data_analysis/dashboard/exhibition_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        performances = Performance.objects.filter(genre='exhibition')
        
        # 통계 데이터 계산
        context['total_sales'] = performances.aggregate(Sum('total_sales'))['total_sales__sum'] or 0
        context['total_audience'] = performances.aggregate(Sum('total_audience'))['total_audience__sum'] or 0
        context['avg_occupancy'] = performances.aggregate(Avg('occupancy_rate'))['occupancy_rate__avg'] or 0
        
        # 진행중인 공연 QuerySet
        active_performances = performances.filter(
            start_date__lte=now,
            end_date__gte=now
        )
        context['active_performances'] = active_performances
        context['active_performances_count'] = active_performances.count()
        
        # 차트 데이터 준비
        sales_data = {
            'labels': [p.name for p in performances[:10]],
            'data': [p.total_sales for p in performances[:10]]
        }
        audience_data = {
            'labels': [p.name for p in performances[:10]],
            'data': [p.total_audience for p in performances[:10]]
        }
        
        context['sales_data'] = json.dumps(sales_data)
        context['audience_data'] = json.dumps(audience_data)
        context['performances'] = performances
        
        return context

@login_required
def performance_dashboard(request, pk):
    performance = get_object_or_404(Performance, pk=pk)
    
    # 기본 기간은 월간으로 설정
    period = request.GET.get('period', 'monthly')
    
    # 대시보드 데이터 가져오기
    dashboard_data = get_dashboard_data(performance, period)
    
    context = {
        'performance': performance,
        'total_amount': dashboard_data['total_amount'],
        'target_amount': dashboard_data['target_amount'],
        'sales_achievement': dashboard_data['sales_achievement'],
        'total_sales_count': dashboard_data['total_sales_count'],
        'average_ticket_price': dashboard_data['average_ticket_price'],
        'sales_count_growth': dashboard_data['sales_count_growth'],
        'total_occupancy_rate': dashboard_data['total_occupancy_rate'],
        'paid_rate': dashboard_data['paid_rate'],
        'free_rate': dashboard_data['free_rate'],
        'price_growth': dashboard_data['price_growth'],
        'max_ticket_price': dashboard_data['max_ticket_price'],
        'date_labels': json.dumps(dashboard_data['date_labels']),
        'sales_data': json.dumps(dashboard_data['sales_data']),
        'target_data': json.dumps(dashboard_data['target_data']),
        'total_occupancy_data': json.dumps(dashboard_data['total_occupancy_data']),
        'paid_rate_data': json.dumps(dashboard_data['paid_rate_data']),
        'free_rate_data': json.dumps(dashboard_data['free_rate_data']),
    }
    
    # 전시가 아닌 경우 캐스팅별 매출 데이터 추가
    if performance.genre != 'exhibition':
        context.update({
            'casting_labels': json.dumps(dashboard_data['casting_labels']),
            'casting_sales_data': json.dumps(dashboard_data['casting_sales_data']),
        })
    
    return render(request, 'data_analysis/performance/dashboard.html', context)

def get_dashboard_data(performance, period):
    today = timezone.now().date()
    
    # 기간에 따른 날짜 범위 설정
    if period == 'daily':
        start_date = today - timezone.timedelta(days=30)
        date_format = '%Y-%m-%d'
    elif period == 'weekly':
        start_date = today - timezone.timedelta(weeks=12)
        date_format = '%Y-%m-%d'
    else:  # monthly
        start_date = today - timezone.timedelta(days=365)
        date_format = '%Y-%m'
    
    # 판매 데이터 쿼리
    sales_data = SalesData.objects.filter(
        performance=performance,
        uploaded_at__date__gte=start_date
    ).order_by('uploaded_at')
    
    # 이전 달의 데이터
    last_month = today.replace(day=1) - timezone.timedelta(days=1)
    last_month_data = SalesData.objects.filter(
        performance=performance,
        uploaded_at__year=last_month.year,
        uploaded_at__month=last_month.month
    ).order_by('-uploaded_at').first()
    
    # 현재 달의 데이터
    current_month_data = SalesData.objects.filter(
        performance=performance,
        uploaded_at__year=today.year,
        uploaded_at__month=today.month
    ).order_by('-uploaded_at').first()
    
    # 기간별 데이터 집계
    date_labels = []
    sales_amounts = []
    target_amounts = []
    total_occupancy_rates = []
    paid_rates = []
    free_rates = []
    
    for data in sales_data:
        date_str = data.uploaded_at.strftime(date_format)
        if date_str not in date_labels:
            date_labels.append(date_str)
            sales_amounts.append(float(data.total_amount))
            target_amounts.append(float(data.target_amount))
            total_occupancy_rates.append(float(data.total_occupancy_rate))
            paid_rates.append(float(data.paid_rate))
            free_rates.append(float(data.free_rate))
    
    # 성장률 계산
    sales_count_growth = 0
    price_growth = 0
    if last_month_data and current_month_data:
        if last_month_data.total_sales_count > 0:
            sales_count_growth = round((current_month_data.total_sales_count - last_month_data.total_sales_count) / last_month_data.total_sales_count * 100, 1)
        if last_month_data.average_ticket_price > 0:
            price_growth = round((current_month_data.average_ticket_price - last_month_data.average_ticket_price) / last_month_data.average_ticket_price * 100, 1)
    
    # 최신 데이터
    latest_data = sales_data.last() if sales_data.exists() else None
    
    # 캐스팅별 매출 데이터 (전시 제외)
    casting_data = {}
    if performance.genre != 'exhibition':
        castings = performance.castings.all()
        for casting in castings:
            casting_sales = sales_data.filter(
                uploaded_at__date__gte=start_date
            ).aggregate(
                total_amount=Sum('total_amount')
            )['total_amount'] or 0
            casting_data[str(casting)] = float(casting_sales)
    
    # 기본 응답 데이터
    response_data = {
        'total_amount': float(latest_data.total_amount) if latest_data else 0,
        'target_amount': float(latest_data.target_amount) if latest_data else 0,
        'sales_achievement': round(float(latest_data.total_amount / latest_data.target_amount * 100), 1) if latest_data and latest_data.target_amount > 0 else 0,
        'total_sales_count': latest_data.total_sales_count if latest_data else 0,
        'average_ticket_price': float(latest_data.average_ticket_price) if latest_data else 0,
        'sales_count_growth': sales_count_growth,
        'sales_count_growth_abs': abs(sales_count_growth),  # 절대값 추가
        'total_occupancy_rate': float(latest_data.total_occupancy_rate) if latest_data else 0,
        'paid_rate': float(latest_data.paid_rate) if latest_data else 0,
        'free_rate': float(latest_data.free_rate) if latest_data else 0,
        'price_growth': price_growth,
        'price_growth_abs': abs(price_growth),  # 절대값 추가
        'max_ticket_price': float(sales_data.aggregate(max_price=Max('average_ticket_price'))['max_price'] or 0),
        'date_labels': date_labels,
        'sales_data': sales_amounts,
        'target_data': target_amounts,
        'total_occupancy_data': total_occupancy_rates,
        'paid_rate_data': paid_rates,
        'free_rate_data': free_rates,
    }
    
    # 전시가 아닌 경우 캐스팅 데이터 추가
    if performance.genre != 'exhibition':
        response_data.update({
            'casting_labels': list(casting_data.keys()),
            'casting_sales_data': list(casting_data.values()),
        })
    
    return response_data

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)