from django.db import models


class Portfolio(models.Model):
    name = models.CharField(verbose_name='Название', blank=False, null=False, max_length=255)
    description = models.TextField(verbose_name='Описание', blank=True, null=True)
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)

    class Meta:
        db_table = 'Portfolio'
        verbose_name = 'Пример'
        verbose_name_plural = 'Примеры'
        ordering = ("-created_at",)  # Исправлено: сортировка по дате

    def __str__(self):
        return f'{self.name}'


class PortfolioImage(models.Model):
    product = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='images', verbose_name='Доп. изображения')
    image = models.ImageField(upload_to='portfolio_images/', verbose_name='Изображение')
    order = models.PositiveIntegerField(default=0)  # Исправлено: default=0

    class Meta:
        verbose_name = 'Изображение примера'
        verbose_name_plural = 'Изображения примера'
        ordering = ['order']

    def __str__(self):
        return f"Изображение {self.id} для {self.product.name}"