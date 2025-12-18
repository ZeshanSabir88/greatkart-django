from django import forms
from .models import Account

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Enter Password',
        'class': 'form-control',
    }))

    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirm Password',
        'class': 'form-control', # Added class for consistency
    }))

    class Meta:
        model = Account
        # Note: 'confirm_password' is NOT included here as it's not a model field
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'password']

    def clean(self):
        # EVERYTHING inside clean() must be indented (4 spaces or 1 tab)
        cleaned_data = super(RegistrationForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError(
                "Password does not match!"
            )

        # All clean methods MUST return the cleaned_data dictionary
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)

        # Set individual placeholders
        self.fields['first_name'].widget.attrs['placeholder'] = 'Enter First Name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Enter Last Name'
        self.fields['phone_number'].widget.attrs['placeholder'] = 'Enter Phone Number'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter Email Address'

        # Apply the 'form-control' class to all fields (including the ones defined above)
        for field in self.fields:
            # We already set the class on 'password' and 'confirm_password', but this ensures all others get it.
            self.fields[field].widget.attrs['class'] = 'form-control'
