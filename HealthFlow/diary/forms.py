# diary/forms.py

from django import forms
from .models import Entry


class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ['title', 'content', 'file']
        labels = {
            'title': 'Заголовок',
            'content': 'Содержание',
            'file': 'Файл (необязательно)',
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Например: Утреннее давление'}),
            'content': forms.Textarea(attrs={'rows': 7, 'placeholder': 'Как вы себя чувствуете?'}),
        }
