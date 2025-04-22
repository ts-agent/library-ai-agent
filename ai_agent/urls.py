from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # 로그인/로그아웃 URL 추가
    path('data_analysis/', include('data_analysis.urls')),
]
