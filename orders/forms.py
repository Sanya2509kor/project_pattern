from django import forms
from django.core.cache import cache
from main.models import Color
from .models import AvailableDate, AvailableTime, Appointment
from django.db.models import Exists, OuterRef
from django.utils import timezone
import pytz


class AppointmentForm(forms.ModelForm):
    colors = forms.ModelMultipleChoiceField(
        queryset=Color.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Можете написать свои пожелания',
            'class': 'form-control',
            'rows': 3
        }),
        required=False,
        label='Комментарий'
    )
    
    class Meta:
        model = Appointment
        fields = ['date', 'time', 'name', 'phone', 'product', 'colors', 'comment']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваше имя'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (999) 999-99-99'
            }),
            'product': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 🔧 БЕЗ КЭШИРОВАНИЯ - просто получаем QuerySet
        current_date = timezone.localtime(timezone.now()).date()
        self.fields['date'].queryset = AvailableDate.objects.annotate(
            has_available_times=Exists(
                AvailableTime.objects.filter(
                    date=OuterRef('pk'),
                    freely=True
                )
            )
        ).filter(
            has_available_times=True,
            date__gte=current_date
        ).order_by('date')
        
        # Фильтрация времени
        self.fields['time'].queryset = AvailableTime.objects.none()
        
        if 'date' in self.data:
            try:
                date_id = int(self.data.get('date'))
                date = AvailableDate.objects.get(id=date_id)
                
                current_time = timezone.localtime(timezone.now()).time()
                current_date = timezone.localtime(timezone.now()).date()
                
                if date.date == current_date:
                    self.fields['time'].queryset = AvailableTime.objects.filter(
                        date_id=date_id,
                        time__gte=current_time,
                        freely=True
                    ).order_by('time')
                else:
                    self.fields['time'].queryset = AvailableTime.objects.filter(
                        date_id=date_id,
                        freely=True
                    ).order_by('time')
            except (ValueError, TypeError, AvailableDate.DoesNotExist):
                pass
        elif self.instance.pk and self.instance.date:
            self.fields['time'].queryset = self.instance.date.available_times.filter(
                freely=True
            ).order_by('time')
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        cleaned = phone.replace('+', '').replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
        if len(cleaned) not in [11, 12]:
            raise forms.ValidationError('Введите корректный номер телефона')
        return cleaned
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
            self.save_m2m()
        return instance