from dataclasses import field
import datetime
from django import forms

from .models import Todo

class CreateTodoForm(forms.ModelForm):
    class Meta:
        model = Todo
        fields = ['content']