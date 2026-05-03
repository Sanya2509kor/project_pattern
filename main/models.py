from django.db import models
from django.urls import reverse
from django.core.cache import cache


class Color(models.Model):
    name = models.CharField(max_length=30, verbose_name='Название цвета')
    image = models.ImageField(upload_to='color_images/', verbose_name='Изображение цвета')

    class Meta:
        db_table = 'main_color'
        verbose_name = 'Цвет'
        verbose_name_plural = 'Цвета'
        ordering = ('name',)
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=150, verbose_name='Название', db_index=True)
    slug = models.SlugField(max_length=200, unique=True, db_index=True, verbose_name='URL')
    image = models.ImageField(upload_to='product_images', verbose_name='Изображение')
    description = models.TextField(verbose_name='Текст', blank=True, null=True)
    price = models.DecimalField(max_digits=7, decimal_places=0, verbose_name='Цена', db_index=True)
    price_str = models.TextField(verbose_name='Текст для цены, если надо (за штуку)', blank=True, null=True)
    discount = models.DecimalField(default=0.00, max_digits=4, decimal_places=2, verbose_name='Скидка в %')
    available_colors = models.ManyToManyField(Color, verbose_name='Доступные цвета', related_name='products', blank=True)
    show = models.BooleanField(verbose_name='Показать на сайте?', default=True, db_index=True)
    make_time = models.CharField(max_length=100, verbose_name='Время занятости', blank=True, null=True, default='30 мин')
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Дата обновления', auto_now=True)

    class Meta:
        db_table = 'Services'
        verbose_name = 'Услугу'
        verbose_name_plural = 'Услуги'
        ordering = ("-created_at",)  # Изменено на сортировку по дате
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
            models.Index(fields=['price']),
            models.Index(fields=['show']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.name}'
    
    def get_absolute_url(self):
        return reverse('main:product', kwargs={'product_slug': self.slug})
    
    def get_discounted_price(self):
        """Возвращает цену со скидкой"""
        if self.discount:
            return self.price * (1 - self.discount / 100)
        return self.price
    
    def invalidate_cache(self):
        """Инвалидация кэша при сохранении"""
        cache.delete(f'product_{self.slug}')
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invalidate_cache()
        
        
    def get_discounted_price(self):
        """Возвращает цену со скидкой"""
        if self.discount and self.discount > 0:
            return self.price * (1 - self.discount / 100)
        return self.price
    
    def get_discount_percent(self):
        """Возвращает процент скидки (целое число)"""
        if self.discount and self.discount > 0:
            return int(self.discount)
        return 0
    
    def has_discount(self):
        """Проверяет, есть ли скидка"""
        return self.discount and self.discount > 0


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name='Товар')
    image = models.ImageField(upload_to='product_images/', verbose_name='Изображение')
    is_main = models.BooleanField(default=False, verbose_name='Основное изображение')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    
    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товара'
        ordering = ['order', '-is_main']
        indexes = [
            models.Index(fields=['product', 'is_main']),
        ]
    
    def __str__(self):
        return f"Изображение {self.id} для {self.product.name}"