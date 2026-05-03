from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from about.models import Portfolio


class AboutView(TemplateView):
    template_name = 'about/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Обо мне'
        context['description'] = 'Я - профессиональный мастер по плетению кос с многолетним опытом работы. Моя миссия - создавать красивые и стильные прически, которые подчеркивают индивидуальность каждого клиента. Использую только качественные материалы и современные техники плетения. Я постоянно совершенствую свои навыки и слежу за последними тенденциями в мире причесок.'
        
        gal = [
            'Более 4 лет опыта',
            'Гипоаллергенные материалы',
            'Индивидуальный подход к каждому клиенту'
        ]
        context['gal'] = gal
        return context


class PortfolioView(ListView):
    template_name = 'about/portfolio.html'
    model = Portfolio
    context_object_name = 'objects'
    paginate_by = 6  # Исправлено: было 10, лучше 6 для портфолио
    allow_empty = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Портфолио'
        return context
    
    def get_queryset(self):
        return Portfolio.objects.all().prefetch_related('images')  # Оптимизация запросов


class ContactsView(TemplateView):
    template_name = 'about/contacts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Контакты'
        context['adress'] = 'Сосновоборск, Солнечная 41'
        context['phone'] = '+7 (983) 692-77-53'
        context['mail'] = 'vikrotiaR@yandex.ru'
        return context