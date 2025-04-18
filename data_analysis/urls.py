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
]