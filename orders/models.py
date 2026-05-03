from django.conf import settings
from django.db import models
from django.core.cache import cache
from main.models import Color, Product


class AvailableDate(models.Model):
    date = models.DateField(unique=True, verbose_name='Дата')
    
    class Meta:
        verbose_name = 'Даты для записи'
        verbose_name_plural = 'Даты для записи'
        indexes = [
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return str(self.date)
    
    def invalidate_cache(self):
        """Инвалидация кэша при сохранении"""
        cache.delete('available_dates')


class AvailableTime(models.Model):
    date = models.ForeignKey(AvailableDate, on_delete=models.CASCADE, related_name='available_times', verbose_name='Дата')
    time = models.TimeField(verbose_name='Время')
    freely = models.BooleanField(verbose_name='Свободно?', default=True)
    
    class Meta:
        verbose_name = 'Время'
        verbose_name_plural = 'Время'
        unique_together = ('date', 'time')
        indexes = [
            models.Index(fields=['date', 'freely']),
            models.Index(fields=['time']),
        ]
    
    def __str__(self):
        return str(self.time)


class Appointment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,  # Изменено с CASCADE на SET_NULL
        verbose_name='Пользователь',
        null=True, 
        blank=True, 
        related_name='appointment'
    )
    name = models.CharField('Имя', max_length=100, db_index=True)
    phone = models.CharField('Телефон', max_length=12, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Услуга')
    colors = models.ManyToManyField(Color, verbose_name='Выбранные цвета', blank=True)
    date = models.ForeignKey(AvailableDate, on_delete=models.CASCADE, verbose_name='Дата')
    time = models.ForeignKey(AvailableTime, on_delete=models.CASCADE, verbose_name='Время')
    comment = models.TextField(verbose_name='Комментарий', blank=True)
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        unique_together = ('date', 'time')
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['date', 'time']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['phone']),
        ]
    
    def __str__(self):
        return f'Заказ #{self.id} от {self.name}'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Инвалидация кэша при сохранении
        cache.delete(f'appointment_{self.id}')
        cache.delete('appointments_list')