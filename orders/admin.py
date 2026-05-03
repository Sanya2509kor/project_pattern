from django.contrib import admin
from .models import AvailableDate, AvailableTime, Appointment
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class AvailableTimeInline(admin.TabularInline):
    model = AvailableTime
    extra = 1
    fields = ('time', 'freely')


@admin.register(AvailableDate)
class AvailableDateAdmin(admin.ModelAdmin):
    inlines = [AvailableTimeInline]
    list_display = ('date', 'available_times_count', 'has_free_slots')
    list_filter = ('date',)
    search_fields = ('date',)
    
    def available_times_count(self, obj):
        return obj.available_times.count()
    available_times_count.short_description = 'Всего слотов'
    
    def has_free_slots(self, obj):
        free = obj.available_times.filter(freely=True).count()
        return format_html(
            '<span style="color: {};">✓ {}</span>',
            'green' if free > 0 else 'red',
            free
        )
    has_free_slots.short_description = 'Свободно'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'date_display', 'time_display', 'product', 'display_colors', 'created_at')
    list_filter = ('date__date', 'product', 'created_at')
    search_fields = ('name', 'phone', 'comment')
    readonly_fields = ('created_at', 'display_colors_preview')
    filter_horizontal = ('colors',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Информация о клиенте', {
            'fields': ('name', 'phone', 'user')
        }),
        ('Детали записи', {
            'fields': ('date', 'time', 'product', 'colors', 'comment')
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def date_display(self, obj):
        return obj.date.date.strftime('%d.%m.%Y')
    date_display.short_description = 'Дата'
    date_display.admin_order_field = 'date__date'
    
    def time_display(self, obj):
        return obj.time.time.strftime('%H:%M')
    time_display.short_description = 'Время'
    
    def display_colors(self, obj):
        colors = obj.colors.all()
        if not colors:
            return "-"
        return ", ".join([color.name for color in colors])
    display_colors.short_description = 'Цвета'
    
    def display_colors_preview(self, obj):
        colors = obj.colors.all()
        if not colors:
            return "-"
        
        html = '<div style="display: flex; gap: 8px; flex-wrap: wrap;">'
        for color in colors:
            if color.image:
                html += f'<img src="{color.image.url}" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover; border: 2px solid #ddd;" title="{color.name}">'
            else:
                html += f'<div style="width: 50px; height: 50px; background: linear-gradient(135deg, #8A2BE2, #FF69B4); border-radius: 50%;" title="{color.name}"></div>'
        html += '</div>'
        return mark_safe(html)
    display_colors_preview.short_description = 'Превью цветов'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'date', 'time', 'product', 'user'
        ).prefetch_related('colors')