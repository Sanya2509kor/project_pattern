from datetime import timedelta
from django.db import models
from django.conf import settings
from django.core.cache import cache


class Reviews(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='reviews'
    )
    comment = models.TextField(verbose_name='Комментарий', blank=True, null=True)
    stars = models.PositiveIntegerField(verbose_name='Звёзды', default=5)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания', db_index=True)

    class Meta:
        db_table = 'Отзывы'
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['stars']),
        ]

    def __str__(self):
        return f"Отзыв {self.id} от {self.user.username}"
    
    @property
    def expiry_date(self):
        return self.created_at + timedelta(days=1)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Инвалидация кэша
        cache.delete('reviews_list')
        cache.delete(f'review_{self.id}')
    
    def get_average_rating_display(self):
        """Возвращает отображение рейтинга звездами"""
        full_stars = int(self.stars)
        empty_stars = 5 - full_stars
        return '★' * full_stars + '☆' * empty_stars