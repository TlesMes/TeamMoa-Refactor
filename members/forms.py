from dataclasses import field
import datetime
from django import forms

from .models import Todo

class CreateTodoForm(forms.ModelForm):
    class Meta:
        model = Todo
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'placeholder': '새로운 할 일을 입력하세요...',
                'class': 'form-control'
            })
        }