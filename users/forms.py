from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomerRegistrationForm(UserCreationForm):
    # Field for reCAPTCHA (requires django-recaptcha package)
    # captcha = ReCaptchaField(widget=ReCaptchaV3) 

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("phone_number", "role", "first_name", "last_name")
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})