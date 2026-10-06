from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class GuestSignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=64)
    last_name = forms.CharField(max_length=64)
    phone = forms.CharField(max_length=32, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "phone")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.GUEST
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    remember = forms.BooleanField(required=False)
