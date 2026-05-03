from django.contrib import admin
from django.utils.html import format_html
from reviews.models import Reviews


@admin.register(Reviews)
class ReviewsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'stars_display', 'comment_preview', 'created_at', 'can_edit')
    list_filter = ('stars', 'created_at', 'user')
    search_fields = ('user__username', 'user__phone_number', 'comment')
    readonly_fields = ('created_at', 'stars_display_full')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Информация об отзыве', {
            'fields': ('user', 'stars', 'comment')
        }),
        ('Дополнительно', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def stars_display(self, obj):
        """Отображение звезд в списке"""
        full = '★' * obj.stars
        empty = '☆' * (5 - obj.stars)
        return format_html(
            '<span style="color: #FFD700; font-size: 1.1rem;">{}</span><span style="color: #E5E7EB;">{}</span>',
            full, empty
        )
    stars_display.short_description = 'Оценка'
    
    def stars_display_full(self, obj):
        """Отображение звезд в деталях"""
        return self.stars_display(obj)
    stars_display_full.short_description = 'Оценка'
    
    def comment_preview(self, obj):
        """Превью комментария"""
        if obj.comment:
            preview = obj.comment[:100]
            if len(obj.comment) > 100:
                preview += '...'
            return preview
        return '-'
    comment_preview.short_description = 'Комментарий (превью)'
    
    def can_edit(self, obj):
        """Проверка, можно ли редактировать отзыв"""
        from django.utils import timezone
        from datetime import timedelta
        
        time_passed = timezone.now() - obj.created_at
        if time_passed <= timedelta(hours=24):
            return format_html('<span style="color: #28a745;">✓ Да</span>')
        return format_html('<span style="color: #dc3545;">✗ Нет</span>')
    can_edit.short_description = 'Можно редактировать'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')