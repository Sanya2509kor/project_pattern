from django.contrib import admin
from about.models import PortfolioImage, Portfolio


class PortfolioImageInline(admin.TabularInline):
    model = PortfolioImage
    extra = 1


@admin.register(Portfolio)
class ProductsAdmin(admin.ModelAdmin):
    inlines = [PortfolioImageInline]
    list_display = ['name', 'created_at']  # Добавлено created_at
    search_fields = ['name', 'description']
    list_filter = ['created_at']  # Добавлен фильтр по дате
    fields = ["name", "description"]

    ordering = ('-created_at',)  # Исправлено