from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View, TemplateView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.db.models import F, Sum, Avg
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
from django.core.management import call_command
from django.contrib.auth.models import User
from django.conf import settings
import os
from django.utils import timezone

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

def crawl_platform(platform, url):
    """
    주어진 플랫폼과 URL에 따라 적절한 크롤링 함수를 호출합니다.
    """
    platform_crawlers = {
        'nol_ticket': crawl_nol_ticket,
        'youtube': crawl_youtube,
        'facebook': crawl_facebook,
        'instagram': crawl_instagram,
        'twitter': crawl_twitter
    }
    
    if platform not in platform_crawlers:
        raise ValueError(f"지원하지 않는 플랫폼입니다: {platform}")
    
    return platform_crawlers[platform](url)

def crawl_nol_ticket(url):
    """
    노티켓 사이트에서 공연 정보를 크롤링합니다.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        # Chrome 웹드라이버 설정
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        # 페이지 로딩 대기
        wait = WebDriverWait(driver, 10)
        
        # 공연 정보 추출
        performance_data = {
            'title': wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.title'))).text,
            'period': wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.period'))).text,
            'location': wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.location'))).text,
            'price': wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.price'))).text
        }
        
        driver.quit()
        return performance_data
        
    except Exception as e:
        return {'error': str(e)}

def crawl_youtube(url):
    """
    유튜브에서 공연 관련 동영상 정보를 크롤링합니다.
    """
    try:
        from googleapiclient.discovery import build
        from urllib.parse import urlparse, parse_qs
        
        # YouTube API 키 설정
        api_key = settings.YOUTUBE_API_KEY
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # URL에서 video ID 추출
        parsed_url = urlparse(url)
        video_id = parse_qs(parsed_url.query)['v'][0]
        
        # 비디오 정보 요청
        request = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        )
        response = request.execute()
        
        if not response['items']:
            return {'error': '비디오를 찾을 수 없습니다.'}
            
        video_data = response['items'][0]
        return {
            'title': video_data['snippet']['title'],
            'views': video_data['statistics']['viewCount'],
            'likes': video_data['statistics']['likeCount'],
            'comments': video_data['statistics']['commentCount']
        }
        
    except Exception as e:
        return {'error': str(e)}

def crawl_facebook(url):
    """
    페이스북에서 공연 관련 게시물 정보를 크롤링합니다.
    """
    try:
        import facebook
        
        # Facebook API 설정
        graph = facebook.GraphAPI(access_token=settings.FACEBOOK_ACCESS_TOKEN)
        
        # URL에서 post ID 추출
        post_id = url.split('/')[-1]
        
        # 게시물 정보 요청
        post_data = graph.get_object(
            post_id,
            fields='message,created_time,likes.summary(true),comments.summary(true),shares'
        )
        
        return {
            'message': post_data.get('message', ''),
            'created_time': post_data.get('created_time', ''),
            'likes': post_data.get('likes', {}).get('summary', {}).get('total_count', 0),
            'comments': post_data.get('comments', {}).get('summary', {}).get('total_count', 0),
            'shares': post_data.get('shares', {}).get('count', 0)
        }
        
    except Exception as e:
        return {'error': str(e)}

def crawl_instagram(url):
    """
    인스타그램에서 공연 관련 게시물 정보를 크롤링합니다.
    """
    try:
        from instaloader import Instaloader, Post
        from urllib.parse import urlparse
        
        # Instaloader 인스턴스 생성
        L = Instaloader()
        
        # URL에서 shortcode 추출
        path_components = urlparse(url).path.split('/')
        shortcode = path_components[-2] if path_components[-1] == '' else path_components[-1]
        
        # 게시물 정보 로드
        post = Post.from_shortcode(L.context, shortcode)
        
        return {
            'caption': post.caption if post.caption else '',
            'likes': post.likes,
            'comments': post.comments,
            'posted_at': post.date_local.isoformat()
        }
        
    except Exception as e:
        return {'error': str(e)}

def crawl_twitter(url):
    """
    트위터에서 공연 관련 트윗 정보를 크롤링합니다.
    """
    try:
        import tweepy
        from urllib.parse import urlparse
        
        # Twitter API 설정
        auth = tweepy.OAuthHandler(
            settings.TWITTER_API_KEY,
            settings.TWITTER_API_SECRET
        )
        auth.set_access_token(
            settings.TWITTER_ACCESS_TOKEN,
            settings.TWITTER_ACCESS_TOKEN_SECRET
        )
        api = tweepy.API(auth)
        
        # URL에서 트윗 ID 추출
        tweet_id = urlparse(url).path.split('/')[-1]
        
        # 트윗 정보 요청
        tweet = api.get_status(tweet_id, tweet_mode='extended')
        
        return {
            'text': tweet.full_text,
            'created_at': tweet.created_at.isoformat(),
            'retweets': tweet.retweet_count,
            'likes': tweet.favorite_count
        }
        
    except Exception as e:
        return {'error': str(e)}

@login_required
def add_crawling_target(request, performance_id):
    """
    새로운 크롤링 대상을 추가합니다.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            platform = data.get('platform')
            url = data.get('url')
            
            if not all([platform, url]):
                return JsonResponse({'error': '플랫폼과 URL을 모두 입력해주세요.'}, status=400)
            
            performance = get_object_or_404(Performance, pk=performance_id)
            
            # 크롤링 시도
            crawling_result = crawl_platform(platform, url)
            
            if 'error' in crawling_result:
                return JsonResponse({'error': crawling_result['error']}, status=400)
            
            # 크롤링 대상 저장
            target = CrawlingTarget.objects.create(
                performance=performance,
                platform=platform,
                url=url,
                last_crawled_data=crawling_result
            )
            
            return JsonResponse({
                'message': '크롤링 대상이 성공적으로 추가되었습니다.',
                'target_id': target.id,
                'data': crawling_result
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
        
        # 크롤링 시도
        crawling_result = crawl_platform(target.platform, target.url)
        
        if 'error' in crawling_result:
            return JsonResponse({'error': crawling_result['error']}, status=400)
        
        # 크롤링 결과 업데이트
        target.last_crawled_data = crawling_result
        target.save()
        
        return JsonResponse({
            'message': '크롤링 대상이 성공적으로 업데이트되었습니다.',
            'data': crawling_result
        })
        
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
        target.delete()
        return JsonResponse({'message': '크롤링 대상이 성공적으로 삭제되었습니다.'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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