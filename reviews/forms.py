from django import forms
from reviews.models import Reviews


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Reviews
        fields = ['comment', 'stars']
        widgets = {
            'stars': forms.HiddenInput(),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Оставьте ваш отзыв...\n\nРасскажите: \n• Что вам понравилось?\n• Как прошла запись?\n• Качество исполнения?\n• Что можно улучшить?',
                'maxlength': 500
            })
        }
        labels = {
            'comment': 'Ваш отзыв',
            'stars': 'Оценка'
        }
    
    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()
        if len(comment) < 10:
            raise forms.ValidationError('Комментарий должен содержать не менее 10 символов')
        if len(comment) > 500:
            raise forms.ValidationError('Комментарий не должен превышать 500 символов')
        return comment
    
    def clean_stars(self):
        stars = self.cleaned_data.get('stars')
        if stars is None or stars < 1 or stars > 5:
            raise forms.ValidationError('Пожалуйста, выберите оценку от 1 до 5')
        return stars