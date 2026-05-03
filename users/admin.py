from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, PasswordResetCallSession


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'phone_number', 'first_name', 'username', 'is_staff', 'avatar_preview', 'count_comments')
    list_filter = ('is_staff', 'is_active', 'edit_name', 'edit_username')
    search_fields = ('phone_number', 'first_name', 'username', 'email')
    readonly_fields = ('last_login', 'date_joined', 'telegram_id', 'telegram_username')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('phone_number', 'password', 'first_name', 'username', 'email')
        }),
        ('Аватар и Telegram', {
            'fields': ('image', 'telegram_id', 'telegram_username', 'telegram_photo_url')
        }),
        ('Настройки', {
            'fields': ('count_comments', 'edit_name', 'edit_username')
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Даты', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'first_name', 'username', 'password1', 'password2'),
        }),
    )
    
    ordering = ('-date_joined',)
    
    def avatar_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />', obj.image.url)
        return "-"
    avatar_preview.short_description = 'Аватар'


@admin.register(PasswordResetCallSession)
class PasswordResetCallSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone', 'status', 'created_at', 'expires_at', 'is_expired_display')
    list_filter = ('status', 'created_at')
    search_fields = ('phone', 'check_id', 'reset_token')
    readonly_fields = ('created_at', 'expires_at', 'check_id', 'call_phone', 'reset_token')
    
    def is_expired_display(self, obj):
        return obj.is_expired()
    is_expired_display.boolean = True
    is_expired_display.short_description = 'Просрочена'