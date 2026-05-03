from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Product, ProductImage, Color


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_preview')
    search_fields = ('name',)
    list_per_page = 20
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 50%;"/>',
                obj.image.url
            )
        return "-"
    image_preview.short_description = "Превью"


class ProductImageInline(admin.TabularInline):  # StackedInline -> TabularInline для экономии места
    model = ProductImage
    extra = 1
    fields = ('image', 'is_main', 'order')
    ordering = ['order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    prepopulated_fields = {'slug': ('name',)}
    
    list_display = ('name', 'price_display', 'display_colors', 'show', 'created_at')
    list_editable = ('show',)
    list_filter = ('show', 'available_colors', 'created_at')
    search_fields = ('name', 'description', 'slug')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'slug', 'description', 'make_time')
        }),
        (_('Изображения и цены'), {
            'fields': ('image', ('price', 'price_str', 'discount'))
        }),
        (_('Настройки'), {
            'fields': ('show', 'available_colors')
        }),
        (_('Даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def price_display(self, obj):
        if obj.discount:
            discounted = obj.get_discounted_price()
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">{} ₽</span> '
                '<span style="color: #28a745; font-weight: bold;">{} ₽</span>',
                obj.price, int(discounted)
            )
        return format_html('<span style="font-weight: bold;">{} ₽</span>', obj.price)
    price_display.short_description = 'Цена'
    
    def display_colors(self, obj):
        colors = obj.available_colors.all()
        if not colors:
            return "-"
        return ", ".join([color.name for color in colors])
    display_colors.short_description = 'Цвета'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('available_colors')