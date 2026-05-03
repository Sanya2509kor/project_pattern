from datetime import timedelta
from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Avg
from django.utils import timezone
from reviews.models import Reviews
from reviews.forms import ReviewForm


class ReviewsView(ListView):
    template_name = 'reviews/reviews.html'
    model = Reviews
    context_object_name = 'reviews'
    paginate_by = 9
    allow_empty = True

    def get_queryset(self):
        # Кэширование списка отзывов на 5 минут
        cache_key = 'reviews_list'
        queryset = cache.get(cache_key)
        
        if queryset is None:
            queryset = Reviews.objects.select_related('user').all()
            cache.set(cache_key, queryset, 60 * 5)  # 5 минут
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Отзывы'
        if self.request.user.is_authenticated:
            context['user_has_comment'] = self.request.user.count_comments > 0
        else:
            context['user_has_comment'] = False
        return context


class CreateReviewView(LoginRequiredMixin, CreateView):
    model = Reviews
    form_class = ReviewForm
    success_url = reverse_lazy('reviews:my_reviews')
    template_name = 'reviews/make_review.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Создание отзыва'
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        
        # Проверка, может ли пользователь оставить отзыв
        if self.request.user.count_comments <= 0:
            form.add_error(None, 'Вы не можете оставить отзыв')
            return self.form_invalid(form)
        
        user = self.request.user
        user.count_comments -= 1
        user.save()
        
        # Инвалидация кэша
        cache.delete('reviews_list')
        
        return super().form_valid(form)


class MyReviewsView(LoginRequiredMixin, ListView):
    template_name = 'reviews/my_reviews.html'
    context_object_name = 'my_reviews'
    model = Reviews
    paginate_by = 9
    allow_empty = True

    def get_queryset(self):
        return Reviews.objects.filter(user=self.request.user).select_related('user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Мои отзывы'
        context['current_date'] = timezone.now()
        
        # Расчет среднего рейтинга
        avg_rating = Reviews.objects.filter(user=self.request.user).aggregate(Avg('stars'))['stars__avg']
        context['average_rating'] = avg_rating or 5.0
        
        return context


class EditReviewView(LoginRequiredMixin, UpdateView):
    model = Reviews
    form_class = ReviewForm
    success_url = reverse_lazy('reviews:my_reviews')
    template_name = 'reviews/edit_review.html'

    def dispatch(self, request, *args, **kwargs):
        review = self.get_object()
        
        # Проверка времени редактирования (24 часа)
        time_passed = timezone.now() - review.created_at
        if time_passed > timedelta(hours=24):
            raise Http404("Отзыв можно редактировать только в течение 24 часов после создания")
        
        # Проверка прав
        if review.user != request.user:
            raise Http404("Вы не можете редактировать чужой отзыв")
        
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование отзыва'
        return context

    def form_valid(self, form):
        # Инвалидация кэша
        cache.delete('reviews_list')
        cache.delete(f'review_{self.object.id}')
        return super().form_valid(form)