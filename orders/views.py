from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.core.cache import cache
from main.models import Color
from .forms import AppointmentForm
from .models import AvailableTime, Appointment
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.generic import CreateView, ListView
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.utils.decorators import method_decorator
from .telegram_service import TelegramNotifier, send_telegram_async
from threading import Thread


class AppointmentView(LoginRequiredMixin, CreateView):
    model = Appointment
    form_class = AppointmentForm
    template_name = 'orders/appointment.html'
    success_url = reverse_lazy('main:index')

    def handle_no_permission(self):
        messages.warning(self.request, 'Для записи войдите в аккаунт или зарегистрируйтесь!')
        return redirect('user:login')

    def get_initial(self):
        initial = super().get_initial()
        product_id = self.request.GET.get('product_id')
        if product_id:
            initial['product'] = product_id
        
        if self.request.user.is_authenticated:
            initial['name'] = self.request.user.get_full_name() or self.request.user.username
        
        if hasattr(self.request.user, 'phone_number') and self.request.user.phone_number:
            initial['phone'] = self.request.user.phone_number

        # 🔧 ИСПРАВЛЕНИЕ: Просто передаем список ID, форма сама преобразует в QuerySet
        colors = self.request.GET.getlist('colors', [])
        if colors:
            initial['colors'] = [int(c) for c in colors if c.isdigit()]
        
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Запись'
        context['colors'] = Color.objects.all()
        
        make_appoint = True
        if self.request.user.is_authenticated and not self.request.user.is_superuser:
            today = timezone.now().date()
            appointments_count = Appointment.objects.filter(
                user=self.request.user,
                date__date__gte=today
            ).count()
            
            if appointments_count >= 3:
                messages.warning(self.request, 'У вас уже есть 3 активные записи!')
                make_appoint = False
        
        context['make_appoint'] = make_appoint
        return context

    @transaction.atomic
    def form_valid(self, form):
        try:
            time_slot = form.cleaned_data['time']
            
            # Блокировка записи
            locked_time_slot = AvailableTime.objects.select_for_update().get(pk=time_slot.pk)
            
            if not locked_time_slot.freely:
                form.add_error('time', 'Это время уже занято')
                return self.form_invalid(form)
            
            self.object = form.save(commit=False)
            self.object.time = locked_time_slot
            
            if self.request.user.is_authenticated:
                self.object.user = self.request.user
            
            self.object.save()
            form.save_m2m()
            
            # Обновление статуса времени
            locked_time_slot.freely = False
            locked_time_slot.save()
            
            # Инвалидация кэша
            cache.delete('available_dates')
            cache.delete('appointments_list')
            
            # Отправка уведомления в Telegram
            try:
                notifier = TelegramNotifier()
                send_telegram_async(notifier, self.object)
            except Exception as e:
                print(f"Telegram error: {e}")
            
            messages.success(self.request, 'Запись успешно создана!')
            return super().form_valid(form)
            
        except AvailableTime.DoesNotExist:
            form.add_error('time', 'Выбранное время не найдено')
            return self.form_invalid(form)
        except Exception as e:
            form.add_error(None, f'Произошла ошибка')
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме')
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


@vary_on_headers('X-Requested-With')
@cache_page(60 * 15)  # Кэширование на 15 минут
def load_times(request):
    """AJAX загрузка доступных временных слотов"""
    date_id = request.GET.get('date')
    if not date_id:
        return JsonResponse({'error': 'Date ID required'}, status=400)
    
    times = AvailableTime.objects.filter(
        date_id=date_id, 
        freely=True
    ).order_by('time').values('id', 'time')
    
    return render(
        request, 
        'orders/times_dropdown_list_options.html', 
        {'times': times}
    )


class ListOrdersView(UserPassesTestMixin, ListView):
    model = Appointment
    context_object_name = 'orders'
    template_name = 'orders/list_orders.html'
    paginate_by = 6
    raise_exception = True
    permission_denied_message = "Доступ запрещен"

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    def handle_no_permission(self):
        raise Http404("Страница не найдена")

    def get_queryset(self):
        today = timezone.now().date()
        return Appointment.objects.filter(
            date__date__gt=today
        ).select_related(
            'product', 'date', 'time', 'user'
        ).prefetch_related(
            'colors'
        ).order_by('date__date', 'time__time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        context['title'] = 'Ближайшие записи'
        return context


class ListOrdersTodayView(UserPassesTestMixin, ListView):
    model = Appointment
    context_object_name = 'orders'
    template_name = 'orders/list_orders_today.html'
    paginate_by = 10
    raise_exception = True
    permission_denied_message = "Доступ запрещен"

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    def handle_no_permission(self):
        raise Http404("Страница не найдена")

    def get_queryset(self):
        today = timezone.now().date()
        return Appointment.objects.filter(
            date__date=today
        ).select_related(
            'product', 'date', 'time', 'user'
        ).prefetch_related(
            'colors'
        ).order_by('time__time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        context['title'] = 'Записи на сегодня'
        return context