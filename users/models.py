from io import BytesIO
import os
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.forms import ValidationError
from django.core.cache import cache
import requests
from django.core.files import File


class User(AbstractUser):
    username = models.CharField(
        verbose_name='Ник',
        max_length=150,
        unique=True,
        blank=True,
        null=True
    )
    image = models.ImageField(upload_to='users_images', blank=True, null=True, verbose_name='Аватар')
    phone_number = models.CharField(
        verbose_name='Номер телефона', 
        max_length=12, 
        unique=True,
        blank=True,
        null=True,
        db_index=True,
        error_messages={
            'unique': "Пользователь с таким номером уже существует!",
        }
    )
    first_name = models.CharField(verbose_name='Имя', max_length=150, db_index=True)
    email = models.EmailField(blank=True, null=True, default='')
    count_comments = models.PositiveSmallIntegerField(verbose_name='Колличество комментариев может оставить', default=1, blank=True, null=True)
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True, db_index=True)
    telegram_username = models.CharField(max_length=32, blank=True, null=True)
    telegram_photo_url = models.URLField(blank=True, null=True)
    edit_name = models.BooleanField(verbose_name='Изменять имя?', default=True)
    edit_username = models.BooleanField(verbose_name='Изменять имя пользователя?', default=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name', 'username']

    class Meta:
        db_table = 'user'
        verbose_name = 'Пользователя'
        verbose_name_plural = 'Пользователи'
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['telegram_id']),
            models.Index(fields=['first_name']),
        ]

    def __str__(self):
        return self.phone_number or self.username or str(self.id)
    
    def clean(self):
        if not self.phone_number and not self.telegram_id:
            raise ValidationError("Должен быть указан либо номер телефона, либо Telegram ID")

    def save_telegram_image(self):
        if self.telegram_photo_url and not self.image:
            try:
                response = requests.get(self.telegram_photo_url, timeout=10)
                response.raise_for_status()
                image_name = os.path.basename(self.telegram_photo_url)
                image_file = BytesIO(response.content)
                self.image.save(image_name, File(image_file), save=True)
                return True
            except Exception as e:
                print(f"Ошибка при загрузке изображения: {e}")
                return False
        return False
    
    def save(self, *args, **kwargs):
        self.save_telegram_image()
        super().save(*args, **kwargs)
        # Инвалидация кэша пользователя
        cache.delete(f'user_{self.pk}')
        cache.delete(f'user_phone_{self.phone_number}')


class PasswordResetCallSession(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает звонка'),
        ('confirmed', 'Подтвержден'),
        ('expired', 'Просрочен'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    phone = models.CharField(max_length=20, verbose_name='Номер телефона')
    check_id = models.CharField(max_length=50, unique=False, verbose_name='ID проверки', db_index=True)
    call_phone = models.CharField(max_length=20, verbose_name='Номер для звонка')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создана')
    expires_at = models.DateTimeField(verbose_name='Истекает')
    reset_token = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name='Токен сброса', db_index=True)
    
    class Meta:
        db_table = 'password_reset_call_session'
        verbose_name = 'Сессия восстановления пароля по звонку'
        verbose_name_plural = 'Сессии восстановления пароля по звонку'
        unique_together = [['check_id', 'status']]
        indexes = [
            models.Index(fields=['check_id', 'status']),
            models.Index(fields=['reset_token']),
            models.Index(fields=['expires_at']),
        ]
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def save(self, *args, **kwargs):
        from django.utils import timezone
        from datetime import timedelta
        import secrets
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        if not self.reset_token:
            self.reset_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.phone} - {self.status}"