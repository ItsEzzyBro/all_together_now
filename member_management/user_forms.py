from django import forms
from django.contrib.auth.models import User
from django.db.models import Case, When, Value, IntegerField
from .models import UserProfile, Role, UsersAndRoles, RolesAndMinistries

class UserCreateForm(forms.ModelForm):
    """Form for creating a new user with password and member association"""
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        help_text="Enter a secure password for this user"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        label="Confirm Password"
    )
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all().annotate(
            custom_order=Case(
                When(role_name='Church Administrator', then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('custom_order', 'role_name'),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        help_text="Select one or more roles for this user"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data


class UserEditForm(forms.ModelForm):
    """Form for editing an existing user (no password field)"""
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all().annotate(
            custom_order=Case(
                When(role_name='Church Administrator', then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('custom_order', 'role_name'),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        help_text="Select one or more roles for this user"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RoleForm(forms.ModelForm):
    """Form for creating/editing roles"""
    ministries = forms.ModelMultipleChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        help_text="Select ministries this role has access to"
    )

    class Meta:
        model = Role
        fields = ['role_name']
        widgets = {
            'role_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Role Name'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Import here to avoid circular import
        from ministry.models import Ministry
        self.fields['ministries'].queryset = Ministry.objects.all().order_by('ministry_name')

        # If editing an existing role, pre-select its ministries
        if self.instance and self.instance.pk:
            self.fields['ministries'].initial = RolesAndMinistries.objects.filter(
                role=self.instance
            ).values_list('ministry_id', flat=True)
