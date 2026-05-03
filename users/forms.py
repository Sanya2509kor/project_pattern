import random
import re
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from users.models import User
from django.contrib.auth import get_user_model


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Номер телефона",
        max_length=12,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 999-99-99'}),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'}),
    )

    class Meta:
        model = User
        fields = ['username', 'password']


class UserRegistrationForm(UserCreationForm):
    USERNAME_LIST = ['ТихаяКосичка', 'РыжаяЛента', 'ШелковыйХвост', 'ПушистыйЛучик', 'СоннаяПрядь', 'СмелаяЗизи', 'ЛасковаяВолна', 'БыстраяИгла', 'БелаяКоса', 'МедныйЛокон', 'ДредныйЕнот', 'ХаерНиндзя', 'BraidQuest', 'ХочуКосы', 'ЖдуМастера', 'ЛюблюПлетение', 'НовыйОбраз', 'БоберПлетельщик', 'SilentBraid', 'HappyKnot']
    
    first_name = forms.CharField(
        label='Имя',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваше имя'})
    )
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'}),
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Подтвердите пароль'}),
    )

    class Meta:
        model = User
        fields = ['first_name', 'phone_number', 'password1', 'password2']

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        # Очистка номера
        cleaned = re.sub(r'[^\d+]', '', phone_number)
        if cleaned.startswith('8'):
            cleaned = '+7' + cleaned[1:]
        elif cleaned.startswith('7') and not cleaned.startswith('+7'):
            cleaned = '+' + cleaned
        
        if User.objects.filter(phone_number=cleaned).exists():
            raise forms.ValidationError("Пользователь с таким номером телефона уже существует.")
        return cleaned

    def save(self, commit=True):
        while True:
            username = f"{random.choice(self.USERNAME_LIST)}{random.randint(1, 999)}"
            if not User.objects.filter(username=username).exists():
                self.instance.username = username
                break
        return super().save(commit)


class ProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("image", "first_name", "username", "phone_number", "email")
    
    image = forms.ImageField(required=False)
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.CharField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        self.edit_name = kwargs.pop('edit_name', True)
        self.edit_username = kwargs.pop('edit_username', True)
        super().__init__(*args, **kwargs)
        
        if not self.edit_name:
            self.fields['first_name'].widget.attrs['readonly'] = True
        if not self.edit_username:
            self.fields['username'].widget.attrs['readonly'] = True


class PasswordResetRequestForm(forms.Form):
    phone_number = forms.CharField(
        label='Номер телефона',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (999) 999-99-99'
        })
    )
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        phone_number = re.sub(r'[^\d+]', '', phone_number)
        
        if phone_number.startswith('8'):
            phone_number = '+7' + phone_number[1:]
        elif not phone_number.startswith('+'):
            phone_number = '+' + phone_number
        
        cleaned_phone = ''.join(filter(str.isdigit, phone_number))
        if cleaned_phone.startswith('8'):
            cleaned_phone = '7' + cleaned_phone[1:]
        elif cleaned_phone.startswith('7') and not cleaned_phone.startswith('+7'):
            cleaned_phone = cleaned_phone
        else:
            cleaned_phone = cleaned_phone.lstrip('+')
        
        try:
            user = User.objects.get(phone_number__contains=cleaned_phone[-10:])
            self.cleaned_user = user
        except User.DoesNotExist:
            raise forms.ValidationError('Пользователь с таким номером телефона не найден')
        except User.MultipleObjectsReturned:
            pass
        
        return phone_number


class PasswordResetConfirmForm(forms.Form):
    new_password1 = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=6
    )
    new_password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Пароли не совпадают')
        return cleaned_data