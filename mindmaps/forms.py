from django import forms

from .models import Mindmap

class CreateMindmapForm(forms.ModelForm):
    class Meta:
        model = Mindmap
        fields = ['title']