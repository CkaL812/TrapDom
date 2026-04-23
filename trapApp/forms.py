from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model  = CustomUser
        fields = ['first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('Цей email вже використовується')
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Паролі не збігаються')
        if p1:
            validate_password(p1)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email    = user.email.lower().strip()
        user.username = user.email
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email    = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        return self.cleaned_data.get('email', '').lower().strip()


class ProfileForm(forms.ModelForm):
    class Meta:
        model  = CustomUser
        fields = ['first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Цей email вже використовується')
        return email


class SetPasswordForm(forms.Form):
    """Для Google-користувачів, що хочуть встановити пароль для email-входу."""
    new_password1 = forms.CharField(widget=forms.PasswordInput)
    new_password2 = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Паролі не збігаються')
        if p1:
            validate_password(p1)
        return cleaned


class PasswordChangeForm(forms.Form):
    """Для зміни існуючого пароля."""
    old_password  = forms.CharField(widget=forms.PasswordInput)
    new_password1 = forms.CharField(widget=forms.PasswordInput)
    new_password2 = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old = self.cleaned_data.get('old_password')
        if not self.user.check_password(old):
            raise forms.ValidationError('Невірний поточний пароль')
        return old

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Паролі не збігаються')
        if p1:
            validate_password(p1)
        return cleaned
