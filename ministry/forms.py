from django import forms
from .models import Ministry, MembersAndMinistries
from member_management.models import Member

class MinistryForm(forms.ModelForm):
    class Meta:
        model = Ministry
        fields = ['ministry_name', 'is_active', 'leader']
        widgets = {
            'ministry_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ministry Name'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'leader': forms.Select(attrs={'class': 'form-control'}),
        }

class MembersAndMinistriesForm(forms.ModelForm):
    class Meta:
        model = MembersAndMinistries
        fields = ['member', 'ministry', 'role']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-control'}),
            'ministry': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
