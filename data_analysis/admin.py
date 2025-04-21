from django.contrib import admin
from .models import Performance, SeatGrade, Actor, Casting, Review, CrawlingTarget

class SeatGradeInline(admin.TabularInline):
    model = SeatGrade
    extra = 1
    min_num = 1

class CastingInline(admin.TabularInline):
    model = Casting
    extra = 1
    min_num = 1

@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ['name', 'venue', 'start_date', 'end_date', 'age_limit']
    list_filter = ['venue', 'age_limit', 'start_date']
    search_fields = ['name', 'venue']
    ordering = ['-start_date']
    inlines = [SeatGradeInline, CastingInline]
    date_hierarchy = 'start_date'

@admin.register(SeatGrade)
class SeatGradeAdmin(admin.ModelAdmin):
    list_display = ['performance', 'name', 'price']
    list_filter = ['performance', 'name']
    search_fields = ['performance__name', 'name']
    ordering = ['performance', 'price']

@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']

@admin.register(Casting)
class CastingAdmin(admin.ModelAdmin):
    list_display = ['performance', 'actor', 'role_name']
    list_filter = ['performance', 'actor']
    search_fields = ['performance__name', 'actor__name', 'role_name']
    autocomplete_fields = ['performance', 'actor']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['performance', 'title', 'rating', 'nickname', 'is_verified', 'created_at', 'views', 'likes']
    list_filter = ['performance', 'rating', 'is_verified', 'created_at']
    search_fields = ['performance__name', 'title', 'content', 'nickname']
    ordering = ['-created_at']
    readonly_fields = ['views', 'likes', 'created_at']
    list_per_page = 20

@admin.register(CrawlingTarget)
class CrawlingTargetAdmin(admin.ModelAdmin):
    list_display = ['performance', 'platform', 'url', 'is_active', 'last_crawled_at']
    list_filter = ['is_active', 'platform', 'performance']
    search_fields = ['performance__name', 'url']
    readonly_fields = ['created_at', 'updated_at', 'last_crawled_at']
    ordering = ['-created_at']
    raw_id_fields = ['performance']
