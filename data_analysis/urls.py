from django.urls import path
from . import views

app_name = 'data_analysis'

urlpatterns = [
    path('', views.index, name='index'),
    
    # Performance URLs
    path('performances/', views.PerformanceListView.as_view(), name='performance_list'),
    path('performances/<int:pk>/', views.PerformanceDetailView.as_view(), name='performance_detail'),
    path('performances/create/', views.PerformanceCreateView.as_view(), name='performance_create'),
    path('performances/<int:pk>/update/', views.PerformanceUpdateView.as_view(), name='performance_update'),
    path('performances/<int:pk>/delete/', views.PerformanceDeleteView.as_view(), name='performance_delete'),
    
    # Actor URLs
    path('actors/', views.ActorListView.as_view(), name='actor_list'),
    path('actors/<int:pk>/', views.ActorDetailView.as_view(), name='actor_detail'),
    path('actors/create/', views.ActorCreateView.as_view(), name='actor_create'),
    path('actors/<int:pk>/update/', views.ActorUpdateView.as_view(), name='actor_update'),
    path('actors/<int:pk>/delete/', views.ActorDeleteView.as_view(), name='actor_delete'),
    
    # SeatGrade URLs
    path('seatgrades/', views.SeatGradeListView.as_view(), name='seatgrade_list'),
    path('seatgrades/create/', views.SeatGradeCreateView.as_view(), name='seatgrade_create'),
    path('seatgrades/<int:pk>/update/', views.SeatGradeUpdateView.as_view(), name='seatgrade_update'),
    path('seatgrades/<int:pk>/delete/', views.SeatGradeDeleteView.as_view(), name='seatgrade_delete'),
    
    # Casting URLs
    path('castings/', views.CastingListView.as_view(), name='casting_list'),
    path('castings/create/', views.CastingCreateView.as_view(), name='casting_create'),
    path('castings/<int:pk>/update/', views.CastingUpdateView.as_view(), name='casting_update'),
    path('castings/<int:pk>/delete/', views.CastingDeleteView.as_view(), name='casting_delete'),

    # Review URLs
    path('reviews/', views.ReviewListView.as_view(), name='review_list'),
    path('reviews/<int:pk>/', views.ReviewDetailView.as_view(), name='review_detail'),
    path('reviews/create/', views.ReviewCreateView.as_view(), name='review_create'),
    path('reviews/<int:pk>/update/', views.ReviewUpdateView.as_view(), name='review_update'),
    path('reviews/<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='review_delete'),
    # 공연별 리뷰 목록
    path('performances/<int:performance_pk>/reviews/', views.PerformanceReviewListView.as_view(), name='performance_review_list'),
    # 리뷰 좋아요 기능
    path('reviews/<int:pk>/like/', views.ReviewLikeView.as_view(), name='review_like'),

    # 판매현황 데이터
    path('performances/<int:pk>/sales-data/upload/', views.sales_data_upload, name='sales_data_upload'),
    path('sales-data/<int:pk>/delete/', views.sales_data_delete, name='sales_data_delete'),

    # 정산서 데이터
    path('performances/<int:pk>/settlement-data/upload/', views.settlement_data_upload, name='settlement_data_upload'),
    path('settlement-data/<int:pk>/delete/', views.settlement_data_delete, name='settlement_data_delete'),

    # 마케팅 캘린더
    path('performances/<int:pk>/marketing-calendar/', views.marketing_calendar, name='marketing_calendar'),
    path('performances/<int:pk>/marketing-calendar/settings/', views.marketing_calendar_settings, name='marketing_calendar_settings'),
    path('performances/<int:pk>/marketing-calendar/events/create/', views.marketing_event_create, name='marketing_event_create'),
    path('performances/<int:pk>/marketing-calendar/events/<int:event_pk>/update/', views.marketing_event_update, name='marketing_event_update'),
    path('performances/<int:pk>/marketing-calendar/events/<int:event_pk>/delete/', views.marketing_event_delete, name='marketing_event_delete'),

    # 크롤링 설정 관리
    path('performances/<int:pk>/crawling/add/', views.add_crawling_target, name='add_crawling_target'),
    path('crawling/<int:target_id>/', views.get_crawling_target, name='get_crawling_target'),
    path('crawling/<int:target_id>/update/', views.update_crawling_target, name='update_crawling_target'),
    path('crawling/<int:target_id>/delete/', views.delete_crawling_target, name='delete_crawling_target'),
    path('crawling/<int:target_id>/toggle/', views.toggle_crawling_target, name='toggle_crawling_target'),

    # superuser 생성 URL (비활성화)
    # path('create-admin/', views.create_super_user, name='create_super_user'),

    # 장르별 대시보드
    path('concert/', views.ConcertDashboardView.as_view(), name='concert_dashboard'),
    path('musical/', views.MusicalDashboardView.as_view(), name='musical_dashboard'),
    path('play/', views.PlayDashboardView.as_view(), name='play_dashboard'),
    path('exhibition/', views.ExhibitionDashboardView.as_view(), name='exhibition_dashboard'),
    path('performance/<int:pk>/dashboard/', views.performance_dashboard, name='performance_dashboard'),
]