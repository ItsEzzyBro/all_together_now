from django import forms
from .models import Member, Family, Vistor

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['first_name', 'last_name', 'date_of_birth', 'gender', 'marital_status', 'address', 'phone_number', 'email', 'family']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'marital_status': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Address'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'family': forms.Select(attrs={'class': 'form-control'}),
        }

class FamilyForm(forms.ModelForm):
    class Meta:
        model = Family
        fields = ['family_name']
        widgets = {
            'family_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Family Name'}),
        }

class VistorForm(forms.ModelForm):
    HOW_FOUND_CHOICES = [
        ("Social Media", "Social Media"),
        ("Friend", "Friend"),
        ("Website", "Website"),
        ("Drive-by", "Drive-by"),
        ("Event", "Event"),
    ]

    how_found_multi = forms.MultipleChoiceField(
        choices=HOW_FOUND_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    interested_ministries = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Vistor
        fields = [
            'first_name', 'last_name', 'phone_number', 'email', 'address',
            'age_group', 'marital_status', 'gender', 'how_found',
            'dedicated_to_christ', 'rededicated_to_christ', 'request_contact_by_leader',
            'notes', 'interested_ministries'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control form-control-lg border-2 border-primary', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-lg border-2 border-primary', 'placeholder': 'Last Name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control form-control-lg border-2 border-primary', 'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-lg border-2 border-primary', 'placeholder': 'Email'}),
            'address': forms.Textarea(attrs={'class': 'form-control form-control-lg border-2 border-primary', 'rows': 2, 'placeholder': 'Address'}),
            'age_group': forms.Select(attrs={'class': 'form-select'}),
            'marital_status': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'how_found': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Find Method (optional)'}),
            'dedicated_to_christ': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'rededicated_to_christ': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'request_contact_by_leader': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-lg border-2 border-primary', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        from ministry.models import Ministry
        super().__init__(*args, **kwargs)
        self.fields['interested_ministries'].queryset = Ministry.objects.all().order_by('ministry_name')
        # Make first/last required
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def clean(self):
        cleaned = super().clean()
        # Store how_found_multi into comma-separated 'how_found'
        selected = cleaned.get('how_found_multi') or []
        cleaned['how_found'] = ", ".join(selected) if selected else cleaned.get('how_found')
        return cleaned