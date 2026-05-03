"""
URL configuration for NameProject project.
Optimized URL patterns with cache buster for static files.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.views.static import serve
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

# Кастомная админка с кэшированием
admin.site.site_header = 'NameProject Администрирование'
admin.site.site_title = 'NameProject'
admin.site.index_title = 'Панель управления'

urlpatterns = [
    # Админка (защищена CSRF)
    path('admin/', admin.site.urls),
    
    # Основные URL
    path('', include('main.urls', namespace='main')),
    path('captcha/', include('captcha.urls')),
    path('reviews/', include('reviews.urls', namespace='reviews')),
    path('user/', include('users.urls', namespace='user')),
    path('order/', include('orders.urls', namespace='order')),
    path('about/', include('about.urls', namespace='about')),
]

# Обслуживание медиа-файлов в режиме разработки с кэшированием
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # В продакшене используем serve с кэшированием
    urlpatterns += [
        path('media/<path:path>', cache_page(60 * 60 * 24)(serve), {
            'document_root': settings.MEDIA_ROOT
        }),
        path('static/<path:path>', cache_page(60 * 60 * 24)(serve), {
            'document_root': settings.STATIC_ROOT
        }),
    ]

# Обработка ошибок (опционально)
handler404 = 'main.views.custom_404'
handler500 = 'main.views.custom_500'