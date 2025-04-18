from django.contrib import admin
from .models import Performance, SeatGrade, Actor, Casting

class SeatGradeInline(admin.TabularInline):
    model = SeatGrade
    extra = 1
    min_num = 1

class CastingInline(admin.TabularInline):
    model = Casting
    extra = 1
    autocomplete_fields = ['actor']

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
    list_display = ['name', 'created_at', 'get_performances_count']
    search_fields = ['name']
    ordering = ['name']
    
    def get_performances_count(self, obj):
        return obj.castings.count()
    get_performances_count.short_description = '출연 공연 수'

@admin.register(Casting)
class CastingAdmin(admin.ModelAdmin):
    list_display = ['performance', 'actor', 'role_name']
    list_filter = ['performance', 'actor']
    search_fields = ['performance__name', 'actor__name', 'role_name']
    autocomplete_fields = ['performance', 'actor']
