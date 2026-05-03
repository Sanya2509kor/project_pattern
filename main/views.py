from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView
from django.core.cache import cache
from django.db.models import Prefetch
from .models import Product, ProductImage, Color


class IndexView(ListView):
    template_name = 'main/index.html'
    model = Product
    context_object_name = 'goods'
    paginate_by = 12  # Увеличено для лучшего UX
    allow_empty = True

    def get_queryset(self):
        # Оптимизация запросов с prefetch_related
        return Product.objects.filter(show=True).prefetch_related(
            'images'
        ).only(
            'id', 'name', 'slug', 'image', 'description', 
            'price', 'price_str', 'make_time', 'show'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'NameProject'
        context['title_text'] = 'Наши услуги'
        context['text'] = 'Выберите стиль, который подчеркнет вашу индивидуальность'
        return context


class ProductView(DetailView):
    template_name = 'main/product.html'
    slug_url_kwarg = 'product_slug'
    context_object_name = 'product'
    model = Product

    def get_queryset(self):
        # Оптимизация с prefetch_related
        return Product.objects.prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.all()),
            Prefetch('available_colors', queryset=Color.objects.all())
        ).select_related()

    def get_object(self, queryset=None):
        slug = self.kwargs.get(self.slug_url_kwarg)
        
        # Кэширование объекта на 15 минут
        cache_key = f'product_{slug}'
        product = cache.get(cache_key)
        
        if not product:
            queryset = self.get_queryset()
            product = get_object_or_404(queryset, slug=slug, show=True)
            cache.set(cache_key, product, 60 * 15)  # 15 минут
        
        return product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.object.name
        return context
    
    
# Добавьте в конец файла main/views.py

from django.shortcuts import render


def custom_404(request, exception):
    """Кастомная страница 404"""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Кастомная страница 500"""
    return render(request, '500.html', status=500)