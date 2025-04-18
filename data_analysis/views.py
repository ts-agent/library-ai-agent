from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import F
from .models import Performance, Actor, SeatGrade, Casting, Review
from .forms import PerformanceForm

def index(request):
    context = {
        'performances': Performance.objects.all(),
        'actors': Actor.objects.all(),
        'seatgrades': SeatGrade.objects.all(),
        'castings': Casting.objects.all(),
    }
    return render(request, 'data_analysis/index.html', context)

# Performance Views
class PerformanceListView(ListView):
    model = Performance
    template_name = 'data_analysis/performance/list.html'
    context_object_name = 'performances'
    ordering = ['-start_date']

class PerformanceDetailView(DetailView):
    model = Performance
    template_name = 'data_analysis/performance/detail.html'
    context_object_name = 'performance'

class PerformanceCreateView(CreateView):
    model = Performance
    form_class = PerformanceForm
    template_name = 'data_analysis/performance/form.html'
    success_url = reverse_lazy('data_analysis:performance_list')

class PerformanceUpdateView(UpdateView):
    model = Performance
    form_class = PerformanceForm
    template_name = 'data_analysis/performance/form.html'
    success_url = reverse_lazy('data_analysis:performance_list')

class PerformanceDeleteView(DeleteView):
    model = Performance
    template_name = 'data_analysis/performance/confirm_delete.html'
    success_url = reverse_lazy('data_analysis:performance_list')

# Actor Views
class ActorListView(ListView):
    model = Actor
    template_name = 'data_analysis/actor/list.html'
    context_object_name = 'actors'
    ordering = ['name']

class ActorDetailView(DetailView):
    model = Actor
    template_name = 'data_analysis/actor/detail.html'
    context_object_name = 'actor'

class ActorCreateView(CreateView):
    model = Actor
    template_name = 'data_analysis/actor/form.html'
    fields = ['name']
    success_url = reverse_lazy('data_analysis:actor_list')

class ActorUpdateView(UpdateView):
    model = Actor
    template_name = 'data_analysis/actor/form.html'
    fields = ['name']
    success_url = reverse_lazy('data_analysis:actor_list')

class ActorDeleteView(DeleteView):
    model = Actor
    template_name = 'data_analysis/actor/confirm_delete.html'
    success_url = reverse_lazy('data_analysis:actor_list')

# SeatGrade Views
class SeatGradeListView(ListView):
    model = SeatGrade
    template_name = 'data_analysis/seatgrade/list.html'
    context_object_name = 'seatgrades'
    ordering = ['performance', 'price']

class SeatGradeCreateView(CreateView):
    model = SeatGrade
    template_name = 'data_analysis/seatgrade/form.html'
    fields = ['performance', 'name', 'price']
    success_url = reverse_lazy('data_analysis:seatgrade_list')

class SeatGradeUpdateView(UpdateView):
    model = SeatGrade
    template_name = 'data_analysis/seatgrade/form.html'
    fields = ['performance', 'name', 'price']
    success_url = reverse_lazy('data_analysis:seatgrade_list')

class SeatGradeDeleteView(DeleteView):
    model = SeatGrade
    template_name = 'data_analysis/seatgrade/confirm_delete.html'
    success_url = reverse_lazy('data_analysis:seatgrade_list')

# Casting Views
class CastingListView(ListView):
    model = Casting
    template_name = 'data_analysis/casting/list.html'
    context_object_name = 'castings'
    ordering = ['performance', 'actor']

class CastingCreateView(CreateView):
    model = Casting
    template_name = 'data_analysis/casting/form.html'
    fields = ['performance', 'actor', 'role_name']
    success_url = reverse_lazy('data_analysis:casting_list')

class CastingUpdateView(UpdateView):
    model = Casting
    template_name = 'data_analysis/casting/form.html'
    fields = ['performance', 'actor', 'role_name']
    success_url = reverse_lazy('data_analysis:casting_list')

class CastingDeleteView(DeleteView):
    model = Casting
    template_name = 'data_analysis/casting/confirm_delete.html'
    success_url = reverse_lazy('data_analysis:casting_list')

# Review Views
class ReviewListView(ListView):
    model = Review
    template_name = 'data_analysis/review/list.html'
    context_object_name = 'reviews'
    ordering = ['-created_at']
    paginate_by = 10

class ReviewDetailView(DetailView):
    model = Review
    template_name = 'data_analysis/review/detail.html'
    context_object_name = 'review'

    def get_object(self, queryset=None):
        # 조회수 증가
        obj = super().get_object(queryset)
        obj.views = F('views') + 1
        obj.save()
        return obj

class ReviewCreateView(CreateView):
    model = Review
    template_name = 'data_analysis/review/form.html'
    fields = ['performance', 'title', 'content', 'rating', 'nickname']
    success_url = reverse_lazy('data_analysis:review_list')

class ReviewUpdateView(UpdateView):
    model = Review
    template_name = 'data_analysis/review/form.html'
    fields = ['title', 'content', 'rating']
    success_url = reverse_lazy('data_analysis:review_list')

class ReviewDeleteView(DeleteView):
    model = Review
    template_name = 'data_analysis/review/confirm_delete.html'
    success_url = reverse_lazy('data_analysis:review_list')

class PerformanceReviewListView(ListView):
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