from django import forms
from django.contrib.auth.models import User
from .models import Income, CashEntry

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['amount', 'date', 'income_type']

class CashEntryForm(forms.ModelForm):
    class Meta:
        model = CashEntry
        fields = ['description', 'amount', 'date', 'is_income']
